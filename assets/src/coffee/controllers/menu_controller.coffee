@PyRegex().controller 'MenuController', ($log, $scope) ->
  $scope.menuItems = [
      id: "home"
      title: "Home",
      href: "/"
    ,
      id: "changelog"
      title: "Changelog",
      href: "/changelog"
    ,
      id: "documentation",
      title: "Documentation",
      href: "http://docs.python.org/library/re.html"
    ,
      id: "contribute"
      title: "Contribute"
      href: "#"
      links: [
          id: "contribute:develop"
          title: "Develop",
          href: "https://www.github.com/rscarvalho/pyregex"
        ,
          id: "contribute:donate"
          title: "Donate",
          href: "https://www.paypal.com/cgi-bin/webscr?cmd=" +
                "_donations&business=MU86NLVAYBBQW&lc=GB&" +
                "item_name=Donate+To+Help+Funding+PyRegex+Project" +
                "&item_number=pyregex&" +
                "currency_code=USD&bn=PP%2dDonationsBF%3" +
                "abtn_donate_SM%2egif%3aNonHosted"
      ]
  ]

  $scope.hasLinks = (item) ->
    $log.info item.links
    item.links && item.links.length

  $scope.currentUrl = '/'

  $scope.menuChanged = (item) ->
    $scope.currentUrl = item.href unless \
        hasLinks(item) or /^.+:\/\//.test item.href

@PyRegex().filter 'withLinks', ->
  (list) -> list.filter $scope.hasLinks
