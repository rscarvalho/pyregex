// Immutable Bower snapshots, verified before extraction.
const fs = require('fs');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const manifest = require('./frontend-components.json');
(async () => {
  for (const [name, component] of Object.entries(manifest)) {
    const response = await fetch(component.url, {signal: AbortSignal.timeout(60000)});
    if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    const hash = crypto.createHash('sha256').update(bytes).digest('hex');
    if (hash !== component.sha256) throw new Error(`${name}: checksum mismatch`);
    const target = `assets/bower_components/${name}`;
    fs.mkdirSync(target, {recursive: true});
    const archive = `/tmp/${name}.tar.gz`;
    fs.writeFileSync(archive, bytes);
    execFileSync('tar', ['xzf', archive, '--strip-components=1', '-C', target]);
    fs.unlinkSync(archive);
  }
})().catch(error => { console.error(error); process.exit(1); });
