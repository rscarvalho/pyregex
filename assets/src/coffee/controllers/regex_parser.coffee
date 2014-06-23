ctrl = (_, $log, RegexResource, RegexBuilder, ShortenerService,
        templateUrl, $scope, $routeParams, $rootScope) ->

  $scope.allFlags =
    I: 'Ignore Case'
    L: 'Make \\w, \\W, \\b, \\B, \\s and \\S dependent on the current locale.'
    M: 'Multi-line Regular Expression'
    S: 'Make the "." special character match any character at all, ' +
       'including a newline'
    U: 'Make \\w, \\W, \\b, \\B, \\d, \\D, \\s and \\S dependent on the ' +
       'Unicode character properties database.'
    X: 'Verbose'

  pickTemplate = (name) ->
    $scope.resultTemplateUrl = templateUrl("regex/#{name}.html")

  pickTemplate('start')
  $scope.currentResult = {result_type: null}
  $scope.processing = false
  $scope.permalinkUrl = null
  $scope.permalinkShortUrl = null

  $scope.re = RegexBuilder.clean()

  regexIsInValid = (regex) ->
    regex.source is null ||
    regex.testString is null ||
    regex.source is '' ||
    regex.testString is ''

  $scope.getResults = ->
    return if $scope.processing

    if regexIsInValid(@re)
      $scope.currentResult.result = null
      return

    $scope.processing = true
    pickTemplate('start')

    data = $scope.re.data()

    RegexResource.test(data).then (result) ->
      $scope.processing = false
      $scope.currentResult = result.data
      if $scope.isError()
        $scope.permalinkUrl = null
        $scope.permalinkShortUrl = null
      else
        $scope.permalinkUrl = "/?id=#{$scope.re.encodedData()}"

        longUrl = window.location.origin + $scope.permalinkUrl
        ShortenerService.short(longUrl).then (result) ->
          $scope.permalinkShortUrl = result

      pickTemplate('result')

    , (result) ->
      $scope.processing = false
      $scope.currentResult = result.data
      $scope.permalinkUrl = null
      pickTemplate('error')

  $scope.hasResult = ->
    $scope.isResult() and
    $scope.currentResult.result != undefined and
    $scope.currentResult.result != null

  checkResultType = (type) ->
    $scope.isResult() and $scope.currentResult.match_type == type

  $scope.isError = ->
    $scope.currentResult != null and
    $scope.currentResult.result_type == 'error'

  $scope.isResult = -> not $scope.isError()
  $scope.isFindall = -> checkResultType('findall')
  $scope.isSearch = -> checkResultType('search')
  $scope.isMatch = -> checkResultType('match')

  if $routeParams.id
    $scope.re.fromData $routeParams.id
    $scope.getResults()

@PyRegex().controller('RegexParserController', ctrl)
