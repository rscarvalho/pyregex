# -*- coding: utf-8 -*-
from os.path import getmtime
import codecs, os

def updatemessages():
    from django.conf import settings
    if not settings.USE_I18N:
        return
    from django.core.management.commands.compilemessages import compile_messages
    if any([needs_update(path) for path in settings.LOCALE_PATHS]):
        compile_messages()
    LOCALE_PATHS = settings.LOCALE_PATHS
    settings.LOCALE_PATHS = ()
    cwd = os.getcwdu()
    for app in settings.INSTALLED_APPS:
        path = os.path.dirname(__import__(app, {}, {}, ['']).__file__)
        locale = os.path.join(path, 'locale')
        if os.path.isdir(locale):
            # Copy Python translations into JavaScript translations
            update_js_translations(locale)
            if needs_update(locale):
                os.chdir(path)
                compile_messages()
    settings.LOCALE_PATHS = LOCALE_PATHS
    os.chdir(cwd)

def needs_update(locale):
    for root, dirs, files in os.walk(locale):
        po_files = [os.path.join(root, file)
                    for file in files if file.endswith('.po')]
        for po_file in po_files:
            mo_file = po_file[:-2] + 'mo'
            if not os.path.exists(mo_file) or \
                    getmtime(po_file) > getmtime(mo_file):
                return True
    return False

def update_js_translations(locale):
    for lang in os.listdir(locale):
        base_path = os.path.join(locale, lang, 'LC_MESSAGES')
        py_file = os.path.join(base_path, 'django.po')
        js_file = os.path.join(base_path, 'djangojs.po')
        modified = False
        if os.path.exists(py_file) and os.path.exists(js_file):
            py_lines, py_mapping = load_translations(py_file)
            js_lines, js_mapping = load_translations(js_file)
            for msgid in js_mapping:
                if msgid in py_mapping:
                    py_index = py_mapping[msgid]
                    js_index = js_mapping[msgid]
                    if py_lines[py_index] != js_lines[js_index]:
                        modified = True
                        # Copy comment to JS, too
                        if js_index >= 2 and py_index >= 2:
                            if js_lines[js_index - 2].startswith('#') and \
                                    py_lines[py_index - 2].startswith('#'):
                                js_lines[js_index - 2] = py_lines[py_index - 2]
                        js_lines[js_index] = py_lines[py_index]

        if modified:
            print 'Updating JS locale for %s' % os.path.join(locale, lang)
            file = codecs.open(js_file, 'w', 'utf-8')
            file.write(''.join(js_lines))
            file.close()

def load_translations(path):
    """Loads translations grouped into logical sections."""
    file = codecs.open(path, 'r', 'utf-8')
    lines = file.readlines()
    file.close()
    mapping = {}
    msgid = None
    start = -1
    resultlines = []
    for index, line in enumerate(lines):
        # Group comments
        if line.startswith('#'):
            if resultlines and resultlines[-1].startswith('#'):
                resultlines[-1] = resultlines[-1] + lines[index]
            else:
                resultlines.append(lines[index])
            continue

        if msgid is not None and (not line.strip() or line.startswith('msgid ')):
            mapping[msgid] = len(resultlines)
            resultlines.append(''.join(lines[start:index]))
            msgid = None
            start = -1

        if line.startswith('msgid '):
            line = line[len('msgid'):].strip()
            start = -1
            msgid = ''
        if start < 0 and line.startswith('"'):
            msgid += line.strip()[1:-1]
            resultlines.append(lines[index])
            continue

        if line.startswith('msgstr') and start < 0:
            start = index

        if start < 0:
            if resultlines and not resultlines[-1].startswith('msgstr'):
                resultlines[-1] = resultlines[-1] + lines[index]
            else:
                resultlines.append(lines[index])

    if msgid and start:
        mapping[msgid] = len(resultlines)
        resultlines.append(''.join(lines[start:]))

    return resultlines, mapping
