"use strict"

config = ($locationProvider, $routeProvider) ->
  $locationProvider.html5Mode(true)

  $routeProvider.when('/',
    templateUrl: '/assets/templates/index.html'
    controller: 'RegexParser').
  otherwise(redirectTo: '/')

app = angular.module('pyregex', ['ui.select2']).config(config)

l = location
app.value('apiUrl', '/api')
app.factory '_', -> window._
app.factory 'jQuery', -> window.jQuery

app.filter 'length', (_) ->
  (value) ->
    console.log("Length:")
    console.log(value)
    return 0 if _.isUndefined(value) or _.isNull(value)

    # subtract 1 because of angular's $$hashKey
    return (_.values(value).length - 1) if _.isObject(value)
    value.length - 1

@PyRegex = -> angular.module('pyregex')
