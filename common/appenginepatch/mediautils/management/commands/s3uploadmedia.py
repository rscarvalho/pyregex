# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand, CommandError
from optparse import make_option
import os, cStringIO, gzip, mimetypes

class Command(NoArgsCommand):
    help = 'Uploads your _generated_media folder to Amazon S3.'
    option_list = NoArgsCommand.option_list + (
        make_option('--production', action='store_true', dest='production',
            help='Does a real upload instead of a simulation.'),
    )

    requires_model_validation = False

    def handle_noargs(self, **options):
        s3uploadmedia(options.get('production', False))

def submit_cb(bytes_so_far, total_bytes):
    print '  %d bytes transferred / %d bytes total\r' % (bytes_so_far,
            total_bytes),

def s3uploadmedia(production):
    from django.conf import settings
    from ragendja.apputils import get_app_dirs
    try:
        from boto.s3.connection import S3Connection
    except ImportError:
        raise CommandError('This command requires boto.')

    bucket_name = settings.MEDIA_BUCKET
    if production:
        connection = S3Connection()
        bucket = connection.get_bucket(bucket_name)
    print 'Uploading to %s' % bucket_name
    print '\nDeleting old files...'
    if production:
        for key in bucket:
            key.delete()
    print '\nUploading new files...'
    base = os.path.abspath('_generated_media')
    for root, dirs, files in os.walk(base):
        for file in files:
            path = os.path.join(root, file)
            key_name = path[len(base)+1:].replace(os.sep, '/')
            print 'Copying %s (%d bytes)' % (key_name,
                                             os.path.getsize(path))
            if production:
                key = bucket.new_key(key_name)
            fp = open(path, 'rb')
            headers = {}
            # Text files should be compressed to speed up site loading
            if file.split('.')[-1] in ('css', 'ht', 'js'):
                print '  GZipping...',
                gzbuf = cStringIO.StringIO()
                zfile = gzip.GzipFile(mode='wb', fileobj=gzbuf)
                zfile.write(fp.read())
                zfile.close()
                fp.close()
                print '%d bytes' % gzbuf.tell()
                gzbuf.seek(0)
                fp = gzbuf
                headers['Content-Encoding'] = 'gzip'
                headers['Content-Type'] = mimetypes.guess_type(file)[0]
            if production:
                key.set_contents_from_file(fp, headers=headers,
                    cb=submit_cb, num_cb=10, policy='public-read')
            fp.close()

    if not production:
        print '=============================================='
        print 'This was just a simulation.'
        print 'Please use --production to enforce the update.'
        print 'Warning: This will change the production site!'
        print '=============================================='
