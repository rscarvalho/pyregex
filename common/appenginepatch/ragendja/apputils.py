from django.conf import settings
import os

def import_module(module_name):
    return __import__(module_name, {}, {}, [''])

def import_package(package_name):
    package = [import_module(package_name)]
    if package[0].__file__.rstrip('.pyc').rstrip('.py').endswith('__init__'):
        package.extend([import_module(package_name + '.' + name)
                        for name in list_modules(package[0])])
    return package

def list_modules(package):
    dir = os.path.normpath(os.path.dirname(package.__file__))
    try:
        return set([name.rsplit('.', 1)[0] for name in os.listdir(dir)
                if not name.startswith('_') and name.endswith(('.py', '.pyc'))])
    except OSError:
        return []

def get_app_modules(module_name=None):
    app_map = {}
    for app in settings.INSTALLED_APPS:
        appname = app.rsplit('.', 1)[-1]
        try:
            if module_name:
                app_map[appname] = import_package(app + '.' + module_name)
            else:
                app_map[appname] = [import_module(app)]
        except ImportError:
            if module_name in list_modules(import_module(app)):
                raise
    return app_map

def get_app_dirs(subdir=None):
    app_map = {}
    for appname, module in get_app_modules().items():
        dir = os.path.abspath(os.path.dirname(module[0].__file__))
        if subdir:
            dir = os.path.join(dir, subdir)
        if os.path.isdir(dir):
            app_map[appname] = dir
    return app_map
