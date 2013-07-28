"use strict"

config = ($locationProvider, $routeProvider) ->
  $locationProvider.html5Mode(true)

  $routeProvider.when('/',
    templateUrl: '/assets/templates/index.html'
    controller: 'RegexParserController').
  otherwise(redirectTo: '/')

app = angular.module('pyregex', ['ui.select2']).config(config)

l = location
app.value('apiUrl', '/api')
app.factory '_', -> window._
app.factory 'jQuery', -> window.jQuery
app.factory 'window', -> window

@PyRegex = -> angular.module('pyregex')
