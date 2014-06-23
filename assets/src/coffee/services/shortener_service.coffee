@PyRegex().factory('ShortenerService', ($q, $rootScope, gapi) ->

  short: (url) ->
    short_url_deffered = undefined
    short_url_deffered = $q.defer()
    request = gapi.client.urlshortener.url.insert(
      resource:
        longUrl: url
    )
    request.execute (response) ->
      $rootScope.$apply ->
        short_url_deffered.resolve(response.id)


    short_url_deffered.promise
)
