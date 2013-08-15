@PyRegex().directive 'a', ($log) ->
  restrict: 'E'
  link: (scope, element, attr) ->
    update = ->
      href = element.attr('href')
      return unless /^.+:\/\//.test href

      element.attr('target', '_blank')

    element.bind 'change ngChange', update
    scope.$on 'ngRepeatFinished', update
    update()


@PyRegex().directive 'ngRepeat', ($rootScope) ->
  (scope, element, attr) ->
    if scope.$last
      $rootScope.$broadcast('ngRepeatFinished')

