# PyRegex

[![Build Status](https://travis-ci.org/rscarvalho/pyregex.png)](https://travis-ci.org/rscarvalho/pyregex)

PyRegex is an online Regular Expression tester for python dialect.

## License

The code is licensed under the [GNU General Public License v2](LICENSE)

## Development Environment

### Requirements

* Server-side language
    * [Google AppEngine SDK](https://developers.google.com/appengine/)

* Testing (all of them installable via [pip](http://www.pip-installer.org/))
    * [nose](https://nose.readthedocs.org/en/latest/)
    * [nose-gae](http://code.google.com/p/nose-gae/)
    * I also use [rednose](https://pypi.python.org/pypi/rednose) but this one is optional

* Assets management / generation
    * [Node.js](http://nodejs.org/)
    * [Npm](https://npmjs.org/) - Usually shipped with Node.js
    * [Grunt](http://gruntjs.com/)
    * [Bower](http://bower.io/)

### Dependency Installation

* **Google AppEngine SDK**, **Node.js** and **Npm** - See their websites ([1](https://developers.google.com/appengine/), [2](http://nodejs.org/) and [3](http://npmjs.org)) about how to get them installed in your platform
* **Grunt**: `npm install -g grunt`
* **Bower**: `npm install -g bower`
* **Nose** and its companions: `pip install -r requirements.txt` (May require `sudo` or `su`)
* Assets dependencies:
    * `cd $PYREGEX_ROOT/assets`
    * `npm install`
    * `bower install`
    * `grunt build` (to generate the assets that will be served on the web app)


### Running the application

Just run `dev_appserver.py app.yaml`

If you want to contribute with client-side scripting (writing some CoffeeScript/JS and/or SASS/CSS), I recomend you to keep another terminal open at the `assets` folder and run: `grunt watch`. This will watch the filesystem for changes and regenerate the source files as needed.

## Contributing

Anyone is more than welcome to [Create an issue](https://github.com/rscarvalho/pyregex/issues), [Fork](https://github.com/rscarvalho/pyregex) the repository and submit a [Pull Request](https://github.com/rscarvalho/pyregex/pulls).


## TODO

* Social integration (share regex on facebook, twitter, g+, etc.)
* Save/generate regex permalink
* I18n
* Better result visualization