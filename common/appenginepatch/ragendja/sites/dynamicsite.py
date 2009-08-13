from django.conf import settings
from django.core.cache import cache
from django.contrib.sites.models import Site
from ragendja.dbutils import db_create
from ragendja.pyutils import make_tls_property

_default_site_id = getattr(settings, 'SITE_ID', None)
SITE_ID = settings.__class__.SITE_ID = make_tls_property()

class DynamicSiteIDMiddleware(object):
    """Sets settings.SIDE_ID based on request's domain"""
    def process_request(self, request):
        # Ignore port if it's 80 or 443
        if ':' in request.get_host():
            domain, port = request.get_host().split(':')
            if int(port) not in (80, 443):
                domain = request.get_host()
        else:
            domain = request.get_host().split(':')[0]

        # We cache the SITE_ID
        cache_key = 'Site:domain:%s' % domain
        site = cache.get(cache_key)
        if site:
            SITE_ID.value = site
        else:
            site = Site.all().filter('domain =', domain).get()
            if not site:
                # Fall back to with/without 'www.'
                if domain.startswith('www.'):
                    fallback_domain = domain[4:]
                else:
                    fallback_domain = 'www.' + domain
                site = Site.all().filter('domain =', fallback_domain).get()

            # Add site if it doesn't exist
            if not site and getattr(settings, 'CREATE_SITES_AUTOMATICALLY',
                                    True):
                site = db_create(Site, domain=domain, name=domain)
                site.put()

            # Set SITE_ID for this thread/request
            if site:
                SITE_ID.value = str(site.key())
            else:
                SITE_ID.value = _default_site_id

            cache.set(cache_key, SITE_ID.value, 5*60)
