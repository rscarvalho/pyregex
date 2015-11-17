@PyRegex().factory('ShortenerService', ($q, $rootScope, gapi) ->

  short: (url) ->
    short_deferred = $q.defer()
    request = gapi.client.urlshortener.url.insert(
      resource:
        longUrl: url
    )
    request.execute (response) ->
      $rootScope.$apply ->
        short_deferred.resolve(response.id)


    short_deferred.promise
)
