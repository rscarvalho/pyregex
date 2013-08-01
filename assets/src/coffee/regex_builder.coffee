@PyRegex().factory 'RegexBuilder', (_, $log, atob, btoa, jQuery) ->
  class RegexBuilder
    I: 2
    L: 4
    M: 8
    S: 16
    U: 32
    X: 64
    allFlags: ['I', 'L', 'M', 'S', 'U', 'X']

    constructor: ->
      @clean()

    getFlag: =>
      flagValue = (f) => @[f] || 0

      flag = 0
      for key, value of @flags
        flag = flag | flagValue(key) if value
      return flag

    setFlags: (flags) =>
      hasFlag = (f, i) =>
        $log.info "Has Flag? #{f} & #{i} == #{f & i} (#{f & i != 0})"
        (f & i) != 0

      if _.isNumber(flags)
        _.forEach @allFlags, (el) =>
          @flags[el] = hasFlag(flags, @[el])
      else
        for key, value of flags
          @flags[key] = value == true unless _.isUndefined(@flags[key])

    data: =>
      regex: @source
      flags: @getFlag()
      match_type: @matchType
      test_string: @testString

    clean: =>
      @flags = {}
      _.map @allFlags, (el) => @flags[el] = false

      @source = null
      @testString = null
      @matchType = 'match'

      @

    encodedData: =>
      json = JSON.stringify(@data())
      encodeURIComponent(btoa(json))

    fromData: (data) =>
      decoded = decodeURIComponent(atob(data))
      data = jQuery.parseJSON(decoded)
      @clean()
      @source = data.regex
      @testString = data.test_string
      @matchType = data.match_type
      @setFlags(data.flags)

  new RegexBuilder()
