// Supplemental DOM-emulated unit tests, NOT browser/UI verification.
const fs = require('fs');
require('./jquery-csp-compat-test');
const {JSDOM} = require('jsdom');
const coffee = require('coffee-script');
const window = new JSDOM('<html><body></body></html>', {
  url: 'http://127.0.0.1:8082/', runScripts: 'outside-only'
}).window;
window.eval(fs.readFileSync(require.resolve('jasmine-node/lib/jasmine-node/jasmine-1.3.1.js'), 'utf8'));
const bundle = fs.readFileSync('public/assets/application.js', 'utf8');
if (!bundle.includes('http://127.0.0.1:5000/api') || bundle.includes('http://localhost:5000/api')) {
  throw new Error('Incorrect local API endpoint');
}
window.eval(bundle);
window.eval(fs.readFileSync('assets/bower_components/angular-mocks/angular-mocks.js', 'utf8'));
for (const file of ['regex_builder_spec.coffee', 'module_config_spec.coffee',
  'controllers/regex_parser_controller_spec.coffee']) {
  // Adapt only historical endpoint expectations to the local output override.
  const source = fs.readFileSync('tests/client/' + file, 'utf8')
    .replace(/http:\/\/localhost:5000\/api/g, 'http://127.0.0.1:5000/api');
  window.eval(coffee.compile(source));
}
const env = window.jasmine.getEnv();
env.addReporter({
  reportSpecResults(spec) {
    if (!spec.results().passed()) console.error(spec.getFullName(),
      spec.results().getItems().map(item => item.message));
  },
  reportRunnerResults(runner) {
    const results = runner.results();
    console.log(`${runner.specs().length} specs; ${results.passedCount} assertions passed; ${results.failedCount} failed`);
    window.close();
    process.exitCode = results.failedCount ? 1 : 0;
  }
});
env.execute();
