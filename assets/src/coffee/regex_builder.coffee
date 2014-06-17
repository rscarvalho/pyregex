@PyRegex().factory 'RegexBuilder', (_, base64_decode, base64_encode, jQuery) ->
  I: 2
  L: 4
  M: 8
  S: 16
  U: 32
  X: 64
  allFlags: ['I', 'L', 'M', 'S', 'U', 'X']
  source: null
  testString: null
  matchType: 'match'
  flags:
    I: false
    L: false
    M: false
    S: false
    U: false
    X: false

  getFlag: ->
    flagValue = (f) => @[f] || 0

    flag = 0
    for key, value of @flags
      flag = flag | flagValue(key) if value
    return flag

  setFlags: (flags) ->
    hasFlag = (f, i) =>
      (f & i) != 0

    if _.isNumber(flags)
      _.forEach @allFlags, (el) =>
        @flags[el] = hasFlag(flags, @[el])
    else
      for key, value of flags
        @flags[key] = value == true unless _.isUndefined(@flags[key])

  data: ->
    regex: @source
    flags: @getFlag()
    match_type: @matchType
    test_string: @testString


  clean: ->
    @flags = {}
    _.map @allFlags, (el) => @flags[el] = false
    @source = null
    @testString = null
    @matchType = 'match'
    return @

  encodedData: ->
    json = JSON.stringify(@data())
    encodeURIComponent(base64_encode(json))

  fromData: (data) ->
    decoded = decodeURIComponent(base64_decode(data))
    data = jQuery.parseJSON(decoded)
    @clean()
    @source = data.regex
    @testString = data.test_string
    @matchType = data.match_type
    @setFlags(data.flags)

