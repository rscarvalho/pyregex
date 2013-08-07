@PyRegex().directive 'autoGrow', (escapeHtmlFilter) ->
  (scope, element, attr) ->
    minHeight = element[0].offsetHeight
    paddingLeft = parseInt(element.css('paddingLeft')) || 0
    paddingRight = parseInt(element.css('paddingRight')) || 0

    $shadow = angular.element('<div></div>').css
      position: 'absolute'
      top: -10000
      left: -10000
      width: (element[0].offsetWidth - paddingLeft - paddingRight) + 'px'
      fontSize: element.css('fontSize')
      fontFamily: element.css('fontFamily')
      lineHeight: element.css('lineHeight')
      resize: 'none'
      wordWrap: 'break-word'

    angular.element(document.body).append($shadow)

    update = ->
      val = escapeHtmlFilter(element.val())
      $shadow.html(val)

      height = Math.max($shadow[0].offsetHeight + 10, minHeight) + 'px'

      element.css 'height', height
        

    element.bind('keyup keydown keypress change', update)

    scope.$on '$destroy', -> $shadow.remove()
    update()


