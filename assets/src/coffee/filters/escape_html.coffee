@PyRegex().filter 'escapeHtml', ->
  times = (string, number) ->
    return '' if number <= 0
    if number == 1 then string else times(string, number - 1)

  (text) ->
    replacements = [
      [/&/g, '&amp;'],
      [/</g, '&lt;'],
      [/>/g, '&gt;'],
      [/\n$/, '<br/>&nbsp;'],
      [/\n/g, '<br/>'],
      [/\s{2,}/g, (space) -> times('&nbsp', space.length - 1) + ' ']
    ]

    r = {}
    for pair in replacements
      r[pair[0]] = pair[1]

    window.REPLACEMENTS = r

    t = text
    for pair in replacements
      regex = pair[0]
      replacement = pair[1]
      t = t.replace(regex, replacement)

    return t