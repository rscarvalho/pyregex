(function($) {
  /* Fix fadeIn and fadeOut cleartype bug in IE. */
  $.fn.originalFadeIn = $.fn.fadeIn
  $.fn.fadeIn = function(speed, callback) {
    $(this).originalFadeIn(speed, function() {
      if(jQuery.browser.msie)
        $(this).get(0).style.removeAttribute('filter');
      if(callback != undefined)
        callback();
    });
  };
  $.fn.originalFadeOut = $.fn.fadeOut
  $.fn.fadeOut = function(speed, callback) {
    $(this).originalFadeOut(speed, function() {
      if(jQuery.browser.msie)
        $(this).get(0).style.removeAttribute('filter');
      if(callback != undefined)
        callback();
    });
  };

  /* Set better default values that work the same with every browser. */
  $.ajaxSetup({cache: false, timeout: 10000});

  /* If a POST request doesn't contain any data we have to add at least an
   * empty string, so content-length gets set. Some servers refuse to accept
   * the request, otherwise. */
  $(document).ajaxSend(function(evt, request, options) {
    if (options['type'] == 'POST' && options['data'] == null)
      options['data'] = '';
  });
})(jQuery);
