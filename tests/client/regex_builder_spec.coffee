describe 'RegexBuilder', ->
  $builder = null

  beforeEach module('pyregex')
  beforeEach inject (RegexBuilder) ->
    $builder = RegexBuilder

  describe 'initialization', ->
    it 'should initialize re flags to false', ->
      expect($builder.flags.I).toBe false
      expect($builder.flags.L).toBe false
      expect($builder.flags.M).toBe false
      expect($builder.flags.S).toBe false
      expect($builder.flags.U).toBe false
      expect($builder.flags.X).toBe false

    it 'should initialize matchType to "match"', ->
      expect($builder.matchType).toBe 'match'

  it 'should calculate builder flags according to Python api', ->
    $builder.flags.I = true
    expect($builder.getFlag()).toBe 2

    $builder.flags.L = true
    expect($builder.getFlag()).toBe 6

    $builder.flags.I = false
    expect($builder.getFlag()).toBe 4

    $builder.flags.X = true
    expect($builder.getFlag()).toBe 68

  it 'should generate form data to send to the API', ->
    $builder.setFlags I: true, L: true, X: false

    $builder.source = "(\\w+)"
    $builder.testString = "Hello, World!"
    $builder.matchType = 'search'

    data = $builder.data()

    expect(_.keys(data)).toEqual ['flags', 'regex', 'test_string', 'match_type']
    expect(data.regex).toBe "(\\w+)"
    expect(data.test_string).toBe "Hello, World!"
    expect(data.match_type).toBe "search"
    expect(data.flags).toBe 6