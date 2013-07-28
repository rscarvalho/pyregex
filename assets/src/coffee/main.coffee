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
    return 0 if _.isUndefined(value) or _.isNull(value)

    if _.isArray(value)
      length = value.length
      if _.isObject(value[value.length - 1]) and !_.isUndefined(value[value.length - 1].$$hashKey)
        length -= 1
      return length

    # subtract 1 because of angular's $$hashKey
    if _.isObject(value)
      length = _.values(value).length; 
      if !_.isUndefined(value.$$hashKey)
        length -= 1
      return length

    value.length

@PyRegex = -> angular.module('pyregex')
