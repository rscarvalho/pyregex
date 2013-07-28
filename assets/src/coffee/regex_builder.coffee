@PyRegex().factory 'RegexBuilder', (_, $log) ->
  class RegexBuilder
    constructor: ->
      @clean()

    getFlag: =>
      flagValue = (f) -> 
        switch f
          when 'I' then 2
          when 'L' then 4
          when 'M' then 8
          when 'S' then 16
          when 'U' then 32
          when 'X' then 64
          else 0

      flag = 0
      for key, value of @flags
        flag = flag | flagValue(key) if value
      return flag

    setFlags: (flags) =>
      for key, value of flags
        @flags[key] = value == true unless _.isUndefined(@flags[key])

    data: =>
      flags: @getFlag()
      regex: @source
      test_string: @testString
      match_type: @matchType

    clean: =>
      @flags = {}
      _.map ['I', 'L', 'M', 'S', 'U', 'X'], (el) => @flags[el] = false

      @source = null
      @testString = null
      @matchType = 'match'

      @


  new RegexBuilder()
