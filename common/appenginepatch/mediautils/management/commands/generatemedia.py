# -*- coding: utf-8 -*-
"""
This app combines media files specified in the COMBINE_MEDIA setting into one
single file. It's a dictionary mapping the combined name to a tuple of files
that should be combined:

COMBINE_MEDIA = {
    'global/js/combined.js': (
        'global/js/main.js',
        'app/js/other.js',
    ),
    'global/css/main.css': (
        'global/css/base.css',
        'app/css/app.css',
    )
}

The files will automatically be combined if you use manage.py runserver.
Files that shouldn't be combined are simply copied. Also, all css and js files
get compressed with yuicompressor. The result is written in a folder named
_generated_media.

If the target is a JavaScript file whose name contains the string
'%(LANGUAGE_CODE)s' it'll automatically be internationalized and multiple
files will be generated (one for each language code).
"""
from django.core.management.base import NoArgsCommand
from optparse import make_option
from mediautils.generatemedia import generatemedia, updatemedia, MEDIA_ROOT
import os, shutil

class Command(NoArgsCommand):
    help = 'Combines and compresses your media files and saves them in _generated_media.'
    option_list = NoArgsCommand.option_list + (
        make_option('--uncompressed', action='store_true', dest='uncompressed',
            help='Do not run yuicompressor on generated media.'),
        make_option('--update', action='store_true', dest='update',
            help='Only update changed files instead of regenerating everything.'),
    )

    requires_model_validation = False

    def handle_noargs(self, **options):
        compressed = None
        if options.get('uncompressed'):
            compressed = False
        if options.get('update'):
            updatemedia(compressed)
        else:
            generatemedia(compressed)
