"use strict"

app = angular.module('pyregex', [])

l = location
app.value('apiUrl', "#{l.protocol}//#{l.hostname}:#{location.port}/api")

@PyRegex = app