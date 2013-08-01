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

  it 'should calculate builder flags according to an integer number', ->
    $builder.clean()
    expect($builder.flags.I).toBe false
    $builder.setFlags(2)
    expect($builder.flags.I).toBe true
    $builder.setFlags(4)
    expect($builder.flags.I).toBe false
    expect($builder.flags.L).toBe true



  it 'should generate form data to send to the API', ->
    $builder.setFlags I: true, L: true, X: false

    $builder.source = "(\\w+)"
    $builder.testString = "Hello, World!"
    $builder.matchType = 'search'

    data = $builder.data()

    expect(_.keys(data)).toEqual ['regex', 'flags', 'match_type', 'test_string']
    expect(data.regex).toBe "(\\w+)"
    expect(data.test_string).toBe "Hello, World!"
    expect(data.match_type).toBe "search"
    expect(data.flags).toBe 6

  it 'should generate a Base64-encoded value of the regex data', ->
    expected = 'eyJyZWdleCI6IkhlbGxvLCAoXFx3KykhIiwiZmxhZ3MiOj' +
               'YsIm1hdGNoX3R5cGUiOiJtYXRjaCIsInRlc3Rfc3RyaW5n' +
               'IjoiSGVsbG8sIFdvcmxkISJ9'
    $builder.setFlags 6
    $builder.source = "Hello, (\\w+)!"
    $builder.testString = "Hello, World!"
    $builder.matchType = 'match'

    data = $builder.data()
    expect(data.flags).toBe 6

    expect(expected).toEqual $builder.encodedData()

  it 'should parse a Base64-encoded string and reconstruct regex data', ->
    data = 'eyJyZWdleCI6IkhlbGxvLCAoXFx3KykhIiwiZmxhZ3MiOj' +
           'YsIm1hdGNoX3R5cGUiOiJtYXRjaCIsInRlc3Rfc3RyaW5n' +
           'IjoiSGVsbG8sIFdvcmxkISJ9'

    $builder.fromData data

    data = $builder.data()
    expect(6).toBe data.flags
    expect("Hello, (\\w+)!").toBe data.regex
    expect("match").toBe data.match_type
    expect("Hello, World!").toBe data.test_string

  it 'should recreate the data from a previously encoded string', ->
    $builder.setFlags 6
    $builder.source = "Hello, (\\w+)!"
    $builder.testString = "Hello, World!"
    $builder.matchType = 'match'
    expected = $builder.data()
    encoded_data = $builder.encodedData()

    $builder.clean()

    expect(expected).not.toEqual $builder.data()
    
    $builder.fromData(encoded_data)
    expect(expected).toEqual $builder.data()

