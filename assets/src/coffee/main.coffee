"use strict"

app = angular.module('pyregex', ['ui.select2', 'ngResource'])

l = location
app.value('apiUrl', '/api')
app.factory '_', -> window._

@PyRegex = -> angular.module('pyregex')
