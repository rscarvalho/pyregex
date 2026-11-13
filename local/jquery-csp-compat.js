// Only transform generated local output, never the checksum-verified snapshot.
const original = '\t\tif ( !(support[ i + "Bubbles" ] = eventName in window) ) {';
const replacement = '\t\tif ( !(support[ i + "Bubbles" ] = eventName in window) && !document.addEventListener ) {';
const probe = '\t\t\tdiv.setAttribute( eventName, "t" );\n' +
  '\t\t\tsupport[ i + "Bubbles" ] = div.attributes[ eventName ].expando === false;';

module.exports = function jqueryCspCompat(js) {
  if (js.split(original).length !== 2 || js.split(probe).length !== 2 ||
      !js.includes(original + '\n\t\t\t// Beware of CSP restrictions (https://developer.mozilla.org/en/Security/CSP)\n' + probe)) {
    throw new Error('Unexpected jQuery 1.11.3 bubbling probe; review local CSP compatibility patch');
  }
  return js.replace(original, replacement);
};
