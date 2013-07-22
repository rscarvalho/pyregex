module.exports = function(grunt) {
	// Configuration
	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'),

		// Coffee to JS compilation
		coffee: {
			app: {
				src: [
					'src/coffee/main.coffee',
					'src/coffee/**.coffee',
				],
				dest: 'build/',
				expand: true,
				flatten: true,
				ext: '.js'
			}
		},

		// Move other files to dist folder
		copy: {
			target: {
				files: [
					{expand: true, cwd: 'lib/js', src: ['**.js'], dest: 'build/'},
					{expand: true, cwd: 'lib/css', src: ['**.css'], dest: 'build/'},
					{expand: true, cwd: 'lib/images', src: ['**.png'], dest: 'dist/'},
					{expand: true, cwd: 'lib/images', src: ['**.png'], dest: 'dist/'},
					{expand: true, cwd: 'lib/images', src: ['**.jpg'], dest: 'dist/'},
					{expand: true, cwd: 'lib/images', src: ['**.webp'], dest: 'dist/'},
					{expand: true, cwd: 'src/', src: ['*.html'], dest: 'dist/'},
					{expand: true, cwd: 'src/css/', src: ['**'], dest: 'build/'},
					{expand: true, cwd: 'src/js/', src:['**'], dest: 'build/'},
					{expand: true, cwd: 'components/normalize-css/', src: ['normalize.css'], dest: 'build/'}
				]
			}
		},

		concat: {
			options: {
				separator: "\n",
			},
			screen_css: {
				src: [
					'build/normalize.min.css', 
					'build/bootstrap.min.css'
				],
				dest: 'dist/screen.css'
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
				sourceMap: 'dist/source-map.js',
				beautify: true,
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
			scripts: {
				files: ["lib/js/**.js", "src/**.coffee"],
				tasks: ['build'],
				options: {
					spawn: false,
					// atBegin: true,
				}
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

	grunt.event.on('watch', function(action, filepath, target) {
	  grunt.log.writeln(target + ': ' + filepath + ' has ' + action);
	});

	// Custom tasks
	grunt.registerTask('build', ['coffee', 'copy', 'concat', 'uglify:app']);
	grunt.registerTask('default', ['build']);
};