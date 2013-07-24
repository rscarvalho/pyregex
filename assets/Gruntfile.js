module.exports = function(grunt) {
    var bowerComponent = function(name, src) {
        return {expand: true, cwd: 'components/' + name, src: src, dest: 'build/'}
    }

    // Configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        // Coffee to JS compilation
        coffee: {
            app: {
                src: [
                    'src/coffee/main.coffee',
                    'src/coffee/*.coffee',
                    'src/coffee/**/*.coffee'
                ],
                dest: 'build/',
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
                    {expand: true, cwd: 'lib/css', src: ['**.css'], dest: 'build/'},
                    {expand: true, cwd: 'src/css/', src: ['**.css'], dest: 'build/'},
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
                    bowerComponent('angular-resource', 'angular-resource.js'),
                    {expand: true, cwd: 'lib/js', src: ['**.js'], dest: 'build/'},
                    {expand: true, cwd: 'src/js/', src:['**'], dest: 'build/'},
                ]
            },

            html: {
                files: [
                    {expand: true, cwd: 'src/', src: ['*.html'], dest: 'dist/'},
                    {expand: true, cwd: 'src/html/', src: ['*.html', '**/*.html'], dest: 'dist/'},
                ]
            },

            images: {
                files: [
                    {expand: true, cwd: 'components/bootstrap-css/img', src: '*.png', dest: 'dist/'},
                    {expand: true, cwd: 'components/select2', src: ['*.png', '*.gif'], dest: 'dist/'},
                    {expand: true, cwd: 'lib/images', src: ['**.png', '**.jpg', '**.gif', '**.webp'], dest: 'dist/'},
                ]
            }
        },

        concat: {
            options: {
                separator: "\n",
            },
            screen_css: {
                src: [
                    'build/normalize.css', 
                    'build/bootstrap.css',
                    'build/select2.css',
                    'build/**.css'
                ],
                dest: 'dist/screen.css'
            },
            application_js: {
                src: [
                    'build/jquery.js',
                    'build/angular.js',
                    'build/select2.js',
                    'build/src/select2.js',
                    'build/main.js',
                    'build/**.js',
                    'build/**/*.js',
                ],
                dest: 'dist/application.js'
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
                'build/**.js'
            ]
        },

        uglify: {
            options: {
                mangle: false,
                // sourceMap: 'dist/source-map.js',
                beautify: false,
                banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' +
                        '<%= grunt.template.today("yyyy-mm-dd") %> */'
            },
            app: {
                files: {
                    'dist/application.js': [
                        'build/jquery-1.10.2.js',
                        'build/angular.js',
                        'build/main.js',
                        'build/**.js'
                    ]
                }
            }
        },

        watch: {
            coffee: {
                files: ['src/coffee/*.coffee', 'src/coffee/**/*.coffee'],
                tasks: ['coffeelint', 'coffee', 'copy:js', 'concat:application_js'],
                options: {
                    atBegin: true,
                }
            },
            sass: {
                files: ['src/sass/*.scss', 'src/sass/**/*.scss'],
                tasks: ['sass', 'copy:css', 'concat:screen_css'],
                options: {
                    atBegin: true,
                }
            },
            html: {
                files: ['src/*.html', 'src/**/*.html'],
                tasks: ['copy:html', 'copy:images'],
                options: {
                    atBegin: true,
                }
            }
        },

        coffeelint: {
            app: ['src/coffee/*.coffee', 'src/coffee/**/*.coffee']
        },

        clean: {
            build: ['build/**'],
            dist: ['dist/**']
        },

        sass: {
            dist: {
                options: {
                    lineNumbers: true
                },
                files: [{
                    expand: true,
                    cwd: 'src/sass',
                    src: ['**.scss'],
                    dest: 'build',
                    ext: '.css'
                }]
            }
        }
    });
    
    // Load plugins
    grunt.loadNpmTasks('grunt-contrib');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-coffee');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-notify');
    grunt.loadNpmTasks('grunt-coffeelint');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-sass');

    grunt.event.on('watch', function(action, filepath, target) {
      grunt.log.writeln(target + ': ' + filepath + ' has ' + action);
    });

    // Custom tasks
    grunt.registerTask('build', ['coffee', 'sass', 'copy', 'concat']);
    grunt.registerTask('default', ['watch']);
};