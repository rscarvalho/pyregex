module.exports = function(grunt) {
    var assetPath = function(path) {
        return "assets/" + path;
    };

    var publicPath = function(path) {
        return "public/" + path;
    };

    var bowerComponent = function(name, src) {
        return {expand: true, cwd: assetPath('bower_components/' + name), src: src, dest: assetPath('build/')}
    };

    Array.prototype.flatten = function() {
        return [].concat.apply([], this);
    };

    var coffeePaths = ['tests/client', 'src/coffee', 'assets/src/coffee'].map(function(e) {
        return [e + '/*.coffee', e + '/**/*.coffee'];
    }).flatten();

    // Configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        // Coffee to JS compilation
        coffee: {
            app: {
                src: [
                    assetPath('src/coffee/*.coffee'),
                    assetPath('src/coffee/**/*.coffee')
                ].flatten(),
                dest: assetPath('build/'),
                expand: true,
                flatten: true,
                ext: '.js'
            }
        },

        // Move other files to dist folder
        copy: {
            css: {
                files: [
                    bowerComponent('normalize-css', 'normalize.css'),
                    bowerComponent('select2', ['select2.js', 'select2.css']),
                    {expand: true, cwd: assetPath('lib/css'), src: ['**.css'], dest: assetPath('build/')},
                    {expand: true, cwd: assetPath('src/css/'), src: ['**.css'], dest: assetPath('build/')},
                ]
            },

            js: {
                files: [
                    bowerComponent('jquery', 'jquery.js'),
                    bowerComponent('angular', 'angular.js'),
                    bowerComponent('angular-ui-select2', 'src/select2.js'),
                    bowerComponent('select2', 'select2.js'),
                    bowerComponent('bootstrap-css/js', 'bootstrap.js'),
                    bowerComponent('underscore', 'underscore.js'),
                    bowerComponent('base64', 'base64.js'),
                    bowerComponent('modernizr', 'modernizr.js'),
                    {expand: true, cwd: assetPath('lib/js'), src: ['**.js'], dest: assetPath('build/')},
                    {expand: true, cwd: assetPath('src/js/'), src:['**'], dest: assetPath('build/')},
                ]
            },

            html: {
                files: [
                    {expand: true, cwd: assetPath('src/'), src: ['*.html'], dest: publicPath('assets/')},
                    {expand: true, cwd: assetPath('src/html/'), src: ['*.html', '**/*.html'], dest: publicPath('assets/')},
                ]
            },

            images: {
                files: [
                    {expand: true, cwd: assetPath('bower_components/bootstrap-css/img'), src: '*.png', dest: publicPath('assets/')},
                    {expand: true, cwd: assetPath('bower_components/select2'), src: ['*.png', '*.gif'], dest: publicPath('assets/')},
                    {expand: true, cwd: assetPath('lib/images'), src: ['**.png', '**.jpg', '**.gif', '**.webp'], dest: publicPath('assets/')},
                ]
            }
        },

        concat: {
            options: {
                separator: "\n",
            },
            screen_css: {
                src: [
                    assetPath('build/normalize.css'),
                    assetPath('build/bootstrap-responsive.css'),
                    assetPath('build/select2.css'),
                    assetPath('build/**.css')
                ],
                dest: publicPath('assets/screen.css')
            },
            application_js: {
                src: [
                    assetPath('build/jquery.js'),
                    assetPath('build/angular.js'),
                    assetPath('build/select2.js'),
                    assetPath('build/src/select2.js'),
                    assetPath('build/base64.js'),
                    assetPath('build/main.js'),
                    assetPath('build/modernizr.js'),
                    assetPath('build/**.js'),
                    assetPath('build/**/*.js'),
                ],
                dest: publicPath('assets/application.js')
            }
        },

        // Som typical JSHint options and globals
        jshint: {
            options: {
                curly: true,
                eqeqeq: true,
                immed: true,
                latedef: true,
                newcap: true,
                noarg: true,
                sub: true,
                undef: true,
                boss: true,
                eqnull: true,
                browser: true
            },
            globals: {
                jQuery: true,
                angular: true
            },
            files: [
                'Gruntfile.js',
                assetPath('build/**.js')
            ]
        },

        uglify: {
            options: {
                mangle: false,
                beautify: false,
                banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' +
                        '<%= grunt.template.today("yyyy-mm-dd") %> */'
            },
            app: {
                files: {
                    'public/assets/application.js': [
                        assetPath('build/jquery-1.10.2.js'),
                        assetPath('build/angular.js'),
                        assetPath('build/main.js'),
                        assetPath('build/**.js')
                    ]
                }
            }
        },

        watch: {
            coffee: {
                files: coffeePaths,
                tasks: ['coffeelint', 'coffee', 'copy:js', 'concat:application_js', 'karma'],
                options: {
                    atBegin: true,
                }
            },
            sass: {
                files: [assetPath('src/sass/*.scss'), assetPath('src/sass/**/*.scss')],
                tasks: ['sass', 'copy:css', 'concat:screen_css'],
                options: {
                    atBegin: true,
                }
            },
            html: {
                files: [assetPath('src/*.html'), assetPath('src/**/*.html')],
                tasks: ['copy:html', 'copy:images'],
                options: {
                    atBegin: true,
                }
            }
        },

        coffeelint: {
            app: coffeePaths
        },

        clean: {
            build: [assetPath('build/**')],
            dist: [publicPath('assets/**')]
        },

        sass: {
            dist: {
                options: {
                    lineNumbers: true
                },
                files: [{
                    expand: true,
                    cwd: assetPath('src/sass'),
                    src: ['**.scss'],
                    dest: assetPath('build'),
                    ext: '.css'
                }]
            }
        },

        karma: {
            unit: {
                configFile: 'tests/client/karma.conf.js'
            }
        }
    });

    // Load plugins
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-coffee');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-notify');
    grunt.loadNpmTasks('grunt-coffeelint');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-karma');

    grunt.event.on('watch', function(action, filepath, target) {
      grunt.log.writeln(target + ': ' + filepath + ' has ' + action);
    });

    // Custom tasks
    grunt.registerTask('build', ['coffee', 'sass', 'copy', 'concat']);
    grunt.registerTask('test', ['karma']);

    grunt.registerTask('default', ['clean', 'watch']);
};