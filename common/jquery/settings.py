from ragendja.settings_post import settings
settings.add_app_media('combined-%(LANGUAGE_CODE)s.js',
    'jquery/jquery.js',
    'jquery/jquery.fixes.js',
    'jquery/jquery.ajax-queue.js',
    'jquery/jquery.bgiframe.js',
    'jquery/jquery.livequery.js',
    'jquery/jquery.form.js',
)
