install_cache_dirs() {
    npm_cache_dir=$(npm config get cache)
    mkdir -p $CACHE_DIR/node_modules
    mkdir -p $CACHE_DIR/bower_components
    mkdir -p $CACHE_DIR/npm_cache

    rm -rf node_modules
    rm -rf assets/bower_components
    rm -rf $npm_cache_dir

    ln -sf $CACHE_DIR/node_modules node_modules
    ln -sf $CACHE_DIR/bower_components assets/bower_components
    ln -sf $CACHE_DIR/npm_cache $npm_cache_dir
}