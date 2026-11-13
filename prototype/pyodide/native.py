"""Native entrypoint; require the exact interpreter version before evaluating."""
import hashlib
import json
from pathlib import Path
import platform
import sys

from evaluator import evaluate_json

HERE = Path(__file__).resolve().parent
config = json.loads((HERE / 'runtime.json').read_text())
if platform.python_version() != config['python']:
    sys.exit('Expected CPython ' + config['python'] + ', got ' + platform.python_version())
if platform.python_implementation() != 'CPython':
    sys.exit('Expected CPython')
fixture = HERE.parent.parent / 'tests/fixtures/regex_baseline.json'
corpus = json.loads(fixture.read_text(encoding='utf-8'))
output = json.loads(evaluate_json(json.dumps(corpus['engine_cases'])))
output['fixtureSha256'] = hashlib.sha256(fixture.read_bytes()).hexdigest()
output['evaluatorSha256'] = hashlib.sha256((HERE / 'evaluator.py').read_bytes()).hexdigest()
print(json.dumps(output, ensure_ascii=True))
