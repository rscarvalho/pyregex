module.exports = (grunt) ->
  assetPath = (path) -> "assets/" + path
  publicPath = (path) -> "public/" + path

  bowerComponent = (name, src) ->
    expand: true
    cwd: assetPath("bower_components/#{name}")
    src: src
    dest: assetPath("build/")

  Array::flatten = -> [].concat.apply [], this
  Array::clone = -> @slice(0)
  Array::insertAfter = (reference, elements...) ->
    return @ unless elements.length
    idx = @indexOf(reference)
    if idx < 0
      [@unshift(e) for e in elements]
    else
      @splice(idx, 0, elements...)
    @

  coffeePaths = ["tests/client", "src/coffee", "assets/src/coffee"].map((e) ->
    [e + "/*.coffee", e + "/**/*.coffee"]
  ).flatten()

  aws_credentials = undefined
  try
    aws_credentials = grunt.file.readJSON("aws_credentials.json")
  catch e
    aws_credentials = {key: "", secret: "", bucket: ""}

  pkg = grunt.file.readJSON("package.json")
  
  # Configuration
  grunt.initConfig
    pkg: pkg
    aws: aws_credentials
    
    # Coffee to JS compilation
    coffee:
      app:
        src: [
          assetPath("src/coffee/*.coffee"),
          assetPath("src/coffee/**/*.coffee")
        ].flatten()
        dest: assetPath("build/")
        expand: true
        flatten: true
        ext: ".js"

    markdown:
      all:
        files: [
          src: 'CHANGELOG.md'
          dest: 'public/assets/templates/changelog.html'
        ],
      options:
        template: 'grunt/templates/default_md.jst'
    
    # Move other files to dist folder
    copy:
      css:
        files: [
          bowerComponent("normalize-css", "normalize.css"),
          bowerComponent("select2", ["select2.js", "select2.css"])
        ,
          expand: true
          cwd: assetPath("lib/css")
          src: ["**.css"]
          dest: assetPath("build/")
        ,
          expand: true
          cwd: assetPath("src/css/")
          src: ["**.css"]
          dest: assetPath("build/")
        ]

      js:
        files: [
          bowerComponent("jquery", "jquery.js"),
          bowerComponent("angular", "angular.js"),
          bowerComponent("angular-ui-select2", "src/select2.js"),
          bowerComponent("select2", "select2.js"),
          bowerComponent("bootstrap-css/js", "bootstrap.js"),
          bowerComponent("underscore", "underscore.js"),
          bowerComponent("base64", "base64.js"),
          bowerComponent("modernizr", "modernizr.js")
        ,
          expand: true
          cwd: assetPath("lib/js")
          src: ["**.js"]
          dest: assetPath("build/")
        ,
          expand: true
          cwd: assetPath("src/js/")
          src: ["**"]
          dest: assetPath("build/")
        ]

      html:
        files: [
          expand: true
          cwd: assetPath("src/")
          src: ["*.html"]
          dest: publicPath("assets/")
        ,
          expand: true
          cwd: assetPath("src/html/")
          src: ["*.html", "**/*.html"]
          dest: publicPath("assets/")
        ]

      images:
        files: [
          expand: true
          cwd: assetPath("bower_components/bootstrap-css/img")
          src: "*.png"
          dest: publicPath("assets/")
        ,
          expand: true
          cwd: assetPath("bower_components/select2")
          src: ["*.png", "*.gif"]
          dest: publicPath("assets/")
        ,
          expand: true
          cwd: assetPath("lib/images")
          src: ["**.png", "**.jpg", "**.gif", "**.webp"]
          dest: publicPath("assets/")
        ]

    concat:
      options:
        separator: "\n"

      screen_css:
        src: [
          assetPath("build/normalize.css"),
          assetPath("build/bootstrap-responsive.css"),
          assetPath("build/select2.css"), assetPath("build/**.css")
        ]
        dest: publicPath("assets/screen.css")

      application_js:
        src: [
          assetPath("build/jquery.js"),
          assetPath("build/angular.js"),
          assetPath("build/select2.js"),
          assetPath("build/src/select2.js"),
          assetPath("build/base64.js"), assetPath("build/main.js"),
          assetPath("build/modernizr.js"),
          assetPath("build/**.js"),
          assetPath("build/**/*.js")
        ]
        dest: publicPath("assets/application.js")

    watch:
      coffee:
        files: coffeePaths
        tasks: [
          "coffeelint",
          "coffee",
          "copy:js",
          "concat:application_js",
          "karma"
        ]

      less:
        files: [assetPath("src/less/*.less"), assetPath("src/less/**/*.less")]
        tasks: ["less", "copy:css", "concat:screen_css"]

      html:
        files: [assetPath("src/*.html"), assetPath("src/**/*.html")]
        tasks: ["copy:html", "copy:images"]

      markdown:
        files: [assetPath("*.md"), assetPath("**/*.md"), 'grunt/templates/**']
        tasks: ['markdown']

    coffeelint:
      app: [coffeePaths, 'Gruntfile.coffee'].flatten()

    clean:
      build: [assetPath("build/**")]
      dist: [publicPath("assets/**")]

    less:
      dist:
        options:
          dumpLineNumbers: true
          yuicompress: true
          paths: ["assets/src/less"]

        files: [
          expand: true
          cwd: assetPath("src/less")
          src: ["**.less"]
          dest: assetPath("build")
          ext: ".css"
        ]

    karma:
      unit:
        configFile: "tests/client/karma.conf.js"

    connect:
      server:
        options:
          base: "public/"
          port: 8082
          keepalive: true

    gen_api:
      production:
        endpoint: "http://api.pyregex.com/api"

      development:
        endpoint: "http://localhost:5000/api"

    "s3-sync":
      options:
        key: "<%= aws.key %>"
        secret: "<%= aws.secret %>"
        bucket: "<%= aws.bucket %>"
        access: "public-read"
        concurrency: 20
        gzip: false

      dist:
        files: [
          root: "public/"
          src: [
            "public/*.html",
            "public/**/*.html",
            "public/**/*.css",
            "public/**/*.js",
            "public/**.xml"
          ]
          dest: "/"
          gzip: true
        ,
          root: "public/"
          src: ['gif', 'png', 'jpg', 'webp'].map((e) -> "public/**/**.#{e}")
          dest: "/"
          gzip: false
        ]

  
  # Load plugins
  m = (o) -> key for key, value of o
  tasks = [m(pkg.dependencies), m(pkg.devDependencies)].flatten()
  tasks.filter((e) -> /grunt\-/.test e).forEach(grunt.loadNpmTasks)

  grunt.event.on "watch", (action, filepath, target) ->
    grunt.log.writeln "#{target}: #{filepath} has #{action}"


  grunt.registerMultiTask "gen_api", "Generate server name for api", ->
    grunt.log.writeln "#{@target}: #{@data.endpoint}"
    contents = "(function(){\n\tthis.PyRegex().value(" +
        "\"apiUrl\", \"#{@data.endpoint}\");\n}).call(this);\n"
    fs = require("fs")
    fs.writeFileSync "assets/build/api.js", contents
 
  # Custom tasks
  
  common = ["coffeelint", "coffee", "less", "copy", "concat", "markdown"]
  c = (k, args...) -> common.clone().insertAfter(k, args...)
  grunt.registerTask "build", c("copy", "gen_api:development")
  grunt.registerTask "build:production", c("copy", "gen_api:production")
  grunt.registerTask "deploy", ["clean", "build:production", "s3-sync"]
  grunt.registerTask "test", ["karma"]
  grunt.registerTask "default", ["clean", "build", "watch"]
  grunt.registerTask "server", ["build", "connect"]

