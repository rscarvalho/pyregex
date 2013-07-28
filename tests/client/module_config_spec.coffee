describe "App Configuration", ->
  beforeEach module('pyregex')

  it "should have a value for API endpoint", inject (apiUrl) ->
    expect(apiUrl).toBe('/api')

  describe "factories", ->
    it "should reflect jQuery global object", inject (jQuery) ->
      expect(jQuery).toBe(window.jQuery)

    it "should reflect underscore (_) global object", inject (_) ->
      expect(_).toBe(window._)

  describe "filters", ->
    it "should return the number of elements of a given array or object",
       inject (lengthFilter) ->
         expect(lengthFilter(a: 1, b: 2, c: 3, d: 4)).toBe(4)
         expect(lengthFilter([1, 2, 3])).toBe(3)
         expect(lengthFilter([1, 2, 3, $$hashKey: {}])).toBe(3)
         expect(lengthFilter(a: 1, b: 2, $$hashKey: {})).toBe(2)


