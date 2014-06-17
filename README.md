# PyRegex

[![Build Status](https://travis-ci.org/rscarvalho/pyregex.png)](https://travis-ci.org/rscarvalho/pyregex)

PyRegex is an online Regular Expression tester for python dialect.

## License

The code is licensed under the [GNU General Public License v2](LICENSE)

## Development Environment

### Requirements

* Server-side language
    * [Python](http://www.python.org)
    * [Pip](http://www.pip-installer.org)

* Testing (all of them installable via [pip](http://www.pip-installer.org/))
    * [nose](https://nose.readthedocs.org/en/latest/)
    * I also use [rednose](https://pypi.python.org/pypi/rednose) but this one is optional

* Assets management / generation
    * [Node.js](http://nodejs.org/)
    * [Npm](https://npmjs.org/) - Usually shipped with Node.js
    * [Grunt](http://gruntjs.com/)
    * [Bower](http://bower.io/)

### Dependency Installation

* **Node.js** and **Npm** - See their websites ([2](http://nodejs.org/) and [3](http://npmjs.org)) about how to get them installed in your platform
* **Grunt**: `npm install -g grunt-cli`
* **Bower**: `npm install -g bower`
* **Nose** and its companions: `pip install -r requirements.txt` (May require `sudo` or `su`)
    * For development, please install **also** `pip install -r requirements-dev.txt`
* Assets dependencies: `./install_assets_deps.sh`


### Running the application

Just run `honcho start`

It will start both uWSGI server and grunt. This will watch the filesystem for changes in the source folders and regenerate the client-side target files as needed.

The API will be available on http://localhost:5000 (The port can be overridden by the `$PORT` environment variable). The web app is available at http://localhost:8082

### Testing the application

To test the application, run `nosetests -c nose.cfg` from a terminal window.

## Contributing

Anyone is more than welcome to [Create an issue](https://github.com/rscarvalho/pyregex/issues), [Fork](https://github.com/rscarvalho/pyregex) the repository and submit a [Pull Request](https://github.com/rscarvalho/pyregex/pulls).


## TODO

* Social integration (share regex on facebook, twitter, g+, etc.)
* Save/generate regex permalink
* I18n
* Better result visualization
