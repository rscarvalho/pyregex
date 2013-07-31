@PyRegex().directive 'pyTimeout', ($timeout) ->
  require: 'ngModel'
  link: (scope, ele, attrs, controller) ->
    promise = null
    sleep = if attrs.timeout then parseInt(attrs.timeout) else 3000
    controller.$viewChangeListeners.push ->
      if promise
        $timeout.cancel(promise)
        promise = null

      promise = $timeout ->
        scope.$eval(attrs.pyTimeout)
      , sleep
