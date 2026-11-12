"""Export the existing lock without resolving or upgrading dependencies."""
import json
from pathlib import Path

lock = json.loads(Path('Pipfile.lock').read_text())
packages = dict(lock['default'])
packages.update(lock['develop'])
for name, package in sorted(packages.items()):
    requirement = name + package['version']
    if package.get('markers'):
        requirement += '; ' + package['markers']
    print(requirement + ' ' + ' '.join(
        '--hash=' + value for value in package['hashes']))
