"use strict"

config = ($locationProvider, $routeProvider, $httpProvider) ->
  $locationProvider.html5Mode(true)

  $routeProvider.when('/',
    templateUrl: '/assets/templates/index.html'
    controller: 'RegexParserController').
  when('/changelog',
    templateUrl: '/assets/templates/changelog.html').
  otherwise(redirectTo: '/')

  $httpProvider.defaults.useXDomain = true
  delete $httpProvider.defaults.headers.common['X-Requested-With']

app = angular.module('pyregex', ['ui.select2']).config(config)

l = location
# app.value('apiUrl', '/api')
app.factory '_', -> window._
app.factory 'jQuery', -> window.jQuery
app.factory 'window', -> window
app.factory 'templateUrl', -> (name) -> "/assets/templates/#{name}"

# Base64 encode/decode functions
app.factory 'base64_decode', -> window.atob
app.factory 'base64_encode', -> window.btoa

@PyRegex = -> angular.module('pyregex')
