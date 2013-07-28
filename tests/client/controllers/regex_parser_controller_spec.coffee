describe "RegexParserController", ->
  $scope = null
  $controller = null

  beforeEach module('pyregex')
  beforeEach inject ($rootScope, _, _$controller_, RegexBuilder, RegexResource) ->
    $scope = $rootScope.$new()
    $controller = _$controller_('RegexParserController', 
      _: _
      RegexResource: RegexResource
      $scope: $scope
      RegexBuilder: RegexBuilder
    )

  describe "$scope", ->
    it "should contain valid scope variables after initialization", ->
      inject ($rootScope, _, $controller, RegexBuilder) ->
        $scope = $rootScope.$new()
        $controller('RegexParserController', 
          _: _
          RegexResource: {}
          $scope: $scope
          RegexBuilder: RegexBuilder
        )

        expect($scope.reFlags).toBe(undefined)
        expect($scope.re).toBe(RegexBuilder)
        expect($scope.re.matchType).toBe('match')
        expect($scope.resultTemplateUrl).toBe('/assets/templates/regex/start.html')
        expect($scope.currentResult).toEqual(result_type: null)
        expect($scope.processing).toBe(false)
        expect($scope.re.getFlag()).toBe(0)

    describe "result processing", ->
      it "should reflect webserver result on $scope", inject (jQuery) ->
        $httpBackend = null
        $scope.re.setFlags(I: true)
        $scope.re.source = "Hello, (.+?)$"
        $scope.re.testString = "Hello, World!"
        $scope.re.matchType = "search"

        data = jQuery.param($scope.re.data())

        inject (_$httpBackend_) ->
          $httpBackend = _$httpBackend_
          $httpBackend.expectGET('/api/regex/test/?' + data).
            respond(result_type: 'success', match_type: 'search')

        expect($scope.processing).toBe false
        $scope.getResults()
        expect($scope.processing).toBe true

        $httpBackend.flush()
        expect($scope.processing).toBe false

        result = $scope.currentResult
        expect(result.result_type).toBe 'success'
        expect(result.match_type).toBe 'search'

        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();

      it "should have correct values for status functions", ->
        result = $scope.currentResult
        result.result_type = 'success'
        result.match_type = 'match'

        expect($scope.isError()).toBe(false)
        expect($scope.isResult()).toBe(true)
        expect($scope.isMatch()).toBe(true)

