# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.simplejson import dumps
from os.path import getmtime
import os, codecs, shutil, logging, re

class MediaGeneratorError(Exception):
    pass

path_re = re.compile(r'/[^/]+/\.\./')

MEDIA_VERSION = unicode(settings.MEDIA_VERSION)
COMPRESSOR = os.path.join(os.path.dirname(__file__), '.yuicompressor.jar')
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(__file__)))))
GENERATED_MEDIA = os.path.join(PROJECT_ROOT, '_generated_media')
MEDIA_ROOT = os.path.join(GENERATED_MEDIA, MEDIA_VERSION)
DYNAMIC_MEDIA = os.path.join(PROJECT_ROOT, '.dynamic_media')

# A list of file types that have to be combined
MUST_COMBINE = ['.js', '.css']

# Detect language codes
if not settings.USE_I18N:
    LANGUAGES = (settings.LANGUAGE_CODE,)
else:
    LANGUAGES = [code for code, _ in settings.LANGUAGES]

# Dynamic source handlers
def site_data(**kwargs):
    """Provide site_data variable with settings (currently only MEDIA_URL)."""
    content = 'window.site_data = {};'
    content += 'window.site_data.settings = %s;' % dumps({
        'MEDIA_URL': settings.MEDIA_URL
    })
    return content

def lang_data(LANGUAGE_CODE, **kwargs):
    # These are needed for i18n
    from django.http import HttpRequest
    from django.views.i18n import javascript_catalog

    LANGUAGE_BIDI = LANGUAGE_CODE.split('-')[0] in \
        settings.LANGUAGES_BIDI

    request = HttpRequest()
    request.GET['language'] = LANGUAGE_CODE

    # Add some JavaScript data
    content = 'var LANGUAGE_CODE = "%s";\n' % LANGUAGE_CODE
    content += 'var LANGUAGE_BIDI = ' + \
        (LANGUAGE_BIDI and 'true' or 'false') + ';\n'
    content += javascript_catalog(request,
        packages=settings.INSTALLED_APPS).content

    # The hgettext() function just calls gettext() internally, but
    # it won't get indexed by makemessages.
    content += '\nwindow.hgettext = function(text) { return gettext(text); };\n'
    # Add a similar hngettext() function
    content += 'window.hngettext = function(singular, plural, count) { return ngettext(singular, plural, count); };\n'

    return content
lang_data.name = 'lang-%(LANGUAGE_CODE)s.js'

def generatemedia(compressed):
    if os.path.exists(MEDIA_ROOT):
        shutil.rmtree(MEDIA_ROOT)

    updatemedia(compressed)

def copy_file(path, generated):
    dirpath = os.path.dirname(generated)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    shutil.copyfile(path, generated)

def compress_file(path):
    if not path.endswith(('.css', '.js')):
        return
    from subprocess import Popen
    print '  Running yuicompressor...',
    try:
        cmd = Popen(['java', '-jar', COMPRESSOR, '--charset', 'UTF-8',
                     path, '-o', path])
        if cmd.wait() == 0:
            print '%d bytes' % os.path.getsize(path)
        else:
            print 'Failed!'
    except:
        raise MediaGeneratorError("Failed to execute Java VM. "
            "Please make sure that you have installed Java "
            "and that it's in your PATH.")

def get_file_path(handler, target, media_dirs, **kwargs):
    if isinstance(handler, basestring):
        path = handler % dict(kwargs, target=target)
        app, filepath = path.replace('/', os.sep).split(os.sep, 1)
        return os.path.abspath(os.path.join(media_dirs[app], filepath))

    ext = os.path.splitext(target)[1]
    owner = ''
    for app in settings.INSTALLED_APPS:
        if handler.__module__.startswith(app + '.') and len(app) > len(owner):
            owner = app
    owner = owner or handler.__module__
    name = getattr(handler, 'name', handler.__name__ + ext) % dict(kwargs,
                                                                target=target)
    return os.path.join(DYNAMIC_MEDIA, '%s/%s' % (owner, name))

def get_css_content(handler, content, **kwargs):
    # Add $MEDIA_URL variable to CSS files
    content = content.replace('$MEDIA_URL/', settings.MEDIA_URL)

    # Remove @charset rules
    content = re.sub(r'@charset(.*?);', '', content)

    if not isinstance(handler, basestring):
        return content

    def fixurls(path):
        # Resolve ../ paths
        path = '%s%s/%s' % (settings.MEDIA_URL,
                            os.path.dirname(handler % dict(kwargs)),
                            path.group(1))
        while path_re.search(path):
            path = path_re.sub('/', path, 1)
        return 'url("%s")' % path

    # Make relative paths work with MEDIA_URL
    content = re.sub(r'url\s*\(["\']?([\w\.][^:]*?)["\']?\)',
                     fixurls, content)

    return content

def get_file_content(handler, cache, **kwargs):
    path = get_file_path(handler, **kwargs)
    if path not in cache:
        if isinstance(handler, basestring):
            try:
                file = codecs.open(path, 'r', 'utf-8')
                cache[path] = file.read().lstrip(codecs.BOM_UTF8.decode('utf-8')
                    ).replace('\r\n', '\n').replace('\r', '\n')
            except:
                import traceback
                raise MediaGeneratorError('Error in %s:\n%s\n' %
                                          (path, traceback.format_exc()))
            file.close()
        elif callable(handler):
            cache[path] = handler(**kwargs)
        else:
            raise ValueError('Media generator source "%r" not valid!' % handler)
    # Rewrite url() paths in CSS files
    ext = os.path.splitext(path)[1]
    if ext == '.css':
        cache[path] = get_css_content(handler, cache[path], **kwargs)
    return cache[path]

def update_dynamic_file(handler, cache, **kwargs):
    assert callable(handler)
    path = get_file_path(handler, **kwargs)
    content = get_file_content(handler, cache, **kwargs)
    needs_update = not os.path.exists(path)
    if not needs_update:
        file = codecs.open(path, 'r', 'utf-8')
        if content != file.read():
            needs_update = True
        file.close()
    if needs_update:
        dir = os.path.dirname(path)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        file = codecs.open(path, 'w', 'utf-8')
        file.write(content)
        file.close()
    return needs_update

def get_target_content(group, cache, **kwargs):
    content = ''
    for handler in group:
        content += get_file_content(handler, cache, **kwargs)
        content += '\n'
    return content

def get_targets(combine_media=settings.COMBINE_MEDIA, **kwargs):
    """Returns all files that must be combined."""
    targets = []
    for target in sorted(combine_media.keys()):
        group = combine_media[target]
        if '.site_data.js' in group:
            # site_data must always come first because other modules might
            # depend on it
            group.remove('.site_data.js')
            group.insert(0, site_data)
        if '%(LANGUAGE_CODE)s' in target:
            # This file uses i18n, so generate a separate file per language.
            # The language data is always added before all other files.
            for LANGUAGE_CODE in LANGUAGES:
                data = kwargs.copy()
                data['LANGUAGE_CODE'] = LANGUAGE_CODE
                filename = target % data
                data['target'] = filename
                if lang_data not in group:
                    group.insert(0, lang_data)
                targets.append((filename, data, group))
        elif '%(LANGUAGE_DIR)s' in target:
            # Generate CSS files for both text directions
            for LANGUAGE_DIR in ('ltr', 'rtl'):
                data = kwargs.copy()
                data['LANGUAGE_DIR'] = LANGUAGE_DIR
                filename = target % data
                data['target'] = filename
                targets.append((filename, data, group))
        else:
            data = kwargs.copy()
            filename = target % data
            data['target'] = filename
            targets.append((filename, data, group))
    return targets

def get_copy_targets(media_dirs, **kwargs):
    """Returns paths of files that must be copied directly."""
    # Some files types (MUST_COMBINE) never get copied.
    # They must always be combined.
    targets = {}
    for app, media_dir in media_dirs.items():
        for root, dirs, files in os.walk(media_dir):
            for name in dirs[:]:
                if name.startswith('.'):
                    dirs.remove(name)
            for file in files:
                if file.startswith('.') or file.endswith(tuple(MUST_COMBINE)):
                    continue
                path = os.path.abspath(os.path.join(root, file))
                base = app + path[len(media_dir):]
                targets[base.replace(os.sep, '/')] = path
    return targets

def cleanup_dir(dir, paths):
    # Remove old generated files
    keep = []
    dir = os.path.abspath(dir)
    for path in paths:
        if not os.path.isabs(path):
            path = os.path.join(dir, path)
        path = os.path.abspath(path)
        while path not in keep and path != dir:
            keep.append(path)
            path = os.path.dirname(path)
    for root, dirs, files in os.walk(dir):
        for name in dirs[:]:
            path = os.path.abspath(os.path.join(root, name))
            if path not in keep:
                shutil.rmtree(path)
                dirs.remove(name)
        for file in files:
            path = os.path.abspath(os.path.join(root, file))
            if path not in keep:
                os.remove(path)

def get_media_dirs():
    from ragendja.apputils import get_app_dirs

    media_dirs = get_app_dirs('media')
    media_dirs['global'] = os.path.join(PROJECT_ROOT, 'media')
    return media_dirs

def updatemedia(compressed=None):
    if 'mediautils' not in settings.INSTALLED_APPS:
        return

    # Remove unused media versions
    if os.path.exists(GENERATED_MEDIA):
        entries = os.listdir(GENERATED_MEDIA)
        if len(entries) != 1 or MEDIA_VERSION not in entries:
            shutil.rmtree(GENERATED_MEDIA)

    from ragendja.apputils import get_app_dirs

    # Remove old media if settings got modified (too much work to check
    # if COMBINE_MEDIA was changed)
    mtime = getmtime(os.path.join(PROJECT_ROOT, 'settings.py'))
    for app_path in get_app_dirs().values():
        path = os.path.join(app_path, 'settings.py')
        if os.path.exists(path) and os.path.getmtime(path) > mtime:
            mtime = os.path.getmtime(path)
    if os.path.exists(MEDIA_ROOT) and getmtime(MEDIA_ROOT) <= mtime:
        shutil.rmtree(MEDIA_ROOT)
    
    if not os.path.exists(MEDIA_ROOT):
        os.makedirs(MEDIA_ROOT)
    if not os.path.exists(DYNAMIC_MEDIA):
        os.makedirs(DYNAMIC_MEDIA)

    if compressed is None:
        compressed = not getattr(settings, 'FORCE_UNCOMPRESSED_MEDIA', False)

    media_dirs = get_media_dirs()
    data = {'media_dirs': media_dirs}
    targets = get_targets(**data)
    copy_targets = get_copy_targets(**data)
    target_names = [target[0] for target in targets]

    # Remove unneeded files
    cleanup_dir(MEDIA_ROOT, target_names + copy_targets.keys())
    dynamic_files = []
    for target, kwargs, group in targets:
        for handler in group:
            if callable(handler):
                dynamic_files.append(get_file_path(handler, **kwargs))
    cleanup_dir(DYNAMIC_MEDIA, dynamic_files)

    # Copy files
    for target in sorted(copy_targets.keys()):
        # Only overwrite files if they've been modified. Also, only
        # copy files that won't get combined.
        path = copy_targets[target]
        generated = os.path.join(MEDIA_ROOT, target.replace('/', os.sep))
        if os.path.exists(generated) and \
                getmtime(generated) >= getmtime(path):
            continue
        print 'Copying %s...' % target
        copy_file(path, generated)
    
    # Update dynamic files
    cache = {}
    for target, kwargs, group in targets:
        for handler in group:
            if callable(handler):
                update_dynamic_file(handler, cache, **kwargs)

    # Combine media files
    for target, kwargs, group in targets:
        files = [get_file_path(handler, **kwargs) for handler in group]
        path = os.path.join(MEDIA_ROOT, target.replace('/', os.sep))
        # Only overwrite files if they've been modified
        if os.path.exists(path):
            target_mtime = getmtime(path)
            if not [1 for name in files if os.path.exists(name) and
                                           getmtime(name) >= target_mtime]:
                continue
        print 'Combining %s...' % target
        dirpath = os.path.dirname(path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        file = codecs.open(path, 'w', 'utf-8')
        file.write(get_target_content(group, cache, **kwargs))
        file.close()
        if compressed:
            compress_file(path)
