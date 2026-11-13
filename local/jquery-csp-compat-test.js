const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const patch = require('./jquery-csp-compat');
const source = fs.readFileSync('assets/bower_components/jquery/dist/jquery.js', 'utf8');
const patched = patch(source);
assert.throws(() => patch(patched), /Unexpected jQuery/);
assert.throws(() => patch(source + source), /Unexpected jQuery/);
assert.throws(() => patch(source.replace('div.setAttribute( eventName, "t" );', 'changed();')), /Unexpected jQuery/);
const start = source.indexOf('(function() {\n\tvar i, eventName,');
const end = source.indexOf('})();', start) + 5;
assert(start >= 0 && end > start);
function run(js, modern, supported, expando) {
  const writes = [];
  const attributes = {};
  const context = {
    support: {}, window: supported,
    document: {
      addEventListener: modern ? function () {} : undefined,
      createElement() { return {attributes, setAttribute(name) {
        writes.push(name); attributes[name] = {expando};
      }}; }
    }
  };
  vm.runInNewContext(js, context);
  return {flags: {...context.support}, writes};
}
const before = source.slice(start, end);
const after = patched.slice(start, patched.indexOf('})();', start) + 5);
for (const expando of [true, false]) {
  for (const supported of [{}, {onsubmit: null, onchange: null, onfocusin: null}, {onsubmit: null, onchange: null}]) {
    assert.deepStrictEqual(run(after, false, supported, expando), run(before, false, supported, expando));
    const modern = run(after, true, supported, expando);
    assert.deepStrictEqual(modern.writes, []);
    for (const event of ['submit', 'change', 'focusin']) {
      assert.strictEqual(modern.flags[event + 'Bubbles'], ('on' + event) in supported);
    }
  }
}
console.log('jQuery CSP compatibility guards and modern/legacy probe semantics passed');
