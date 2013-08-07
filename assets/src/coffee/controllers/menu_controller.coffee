@PyRegex().controller 'MenuController', ($log, $scope) ->
  $scope.menuItems = [
    {
      title: "Home",
      href: "#/"
    },
    {
      title: "Documentation",
      href: "http://docs.python.org/library/re.html"
    },
    {
      title: "Develop",
      href: "https://www.github.com/rscarvalho/pyregex"
    }
  ]