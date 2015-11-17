// Generated by CoffeeScript 1.7.1
(function() {
  describe("RegexParserController", function() {
    var $controller, $scope;
    $scope = null;
    $controller = null;
    beforeEach(module('pyregex'));
    beforeEach(inject(function($rootScope, _, _$controller_, RegexBuilder, RegexResource) {
      $scope = $rootScope.$new();
      return $controller = _$controller_('RegexParserController', {
        _: _,
        RegexResource: RegexResource,
        $scope: $scope,
        RegexBuilder: RegexBuilder
      });
    }), window.gapi = {
      client: {
        urlshortener: {
          url: {
            insert: function(obj) {
              return {
                execute: function() {
                  return console.log('Google API request executed.');
                }
              };
            }
          }
        }
      }
    });
    return describe("$scope", function() {
      it("should contain valid scope variables after initialization", function() {
        return inject(function($rootScope, _, $controller, RegexBuilder) {
          var templateUrl;
          $scope = $rootScope.$new();
          $controller('RegexParserController', {
            _: _,
            RegexResource: {},
            $scope: $scope,
            RegexBuilder: RegexBuilder
          });
          templateUrl = '/assets/templates/regex/start.html';
          expect($scope.reFlags).toBe(void 0);
          expect($scope.re).toBe(RegexBuilder);
          expect($scope.re.matchType).toBe('match');
          expect($scope.resultTemplateUrl).toBe(templateUrl);
          expect($scope.currentResult).toEqual({
            result_type: null
          });
          expect($scope.processing).toBe(false);
          return expect($scope.re.getFlag()).toBe(0);
        });
      });
      return describe("result processing", function() {
        it("should reflect webserver result on $scope", inject(function(jQuery) {
          var $httpBackend, data, result;
          $httpBackend = null;
          $scope.re.setFlags({
            I: true
          });
          $scope.re.source = "Hello, (.+?)$";
          $scope.re.testString = "Hello, World!";
          $scope.re.matchType = "search";
          data = jQuery.param($scope.re.data());
          inject(function(_$httpBackend_) {
            var baseUrl;
            $httpBackend = _$httpBackend_;
            baseUrl = 'http://localhost:5000/api';
            return $httpBackend.expectGET(baseUrl + '/regex/test/?' + data).respond({
              result_type: 'success',
              match_type: 'search'
            });
          });
          expect($scope.processing).toBe(false);
          $scope.getResults();
          expect($scope.processing).toBe(true);
          $httpBackend.flush();
          expect($scope.processing).toBe(false);
          result = $scope.currentResult;
          expect(result.result_type).toBe('success');
          expect(result.match_type).toBe('search');
          $httpBackend.verifyNoOutstandingExpectation();
          return $httpBackend.verifyNoOutstandingRequest();
        }));
        return it("should have correct values for status functions", function() {
          var result;
          result = $scope.currentResult;
          result.result_type = 'success';
          result.match_type = 'match';
          expect($scope.isError()).toBe(false);
          expect($scope.isResult()).toBe(true);
          return expect($scope.isMatch()).toBe(true);
        });
      });
    });
  });

}).call(this);
