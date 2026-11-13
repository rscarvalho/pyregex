"""Pure str/re evaluator shared byte-for-byte by native CPython and Pyodide.

Only trusted, bounded fixture cases belong in this first-slice harness.
No Flask, service, multiprocessing, or Pyodide imports.
"""
import json
import platform
import re


def evaluate(case):
    operation = case['operation']
    if operation not in ('match', 'search', 'findall'):
        return {'error': 'invalid_operation'}
    flags = 0
    for name in case['flags']:
        if name not in ('IGNORECASE', 'LOCALE', 'MULTILINE', 'DOTALL',
                        'UNICODE', 'VERBOSE'):
            return {'error': 'invalid_flags'}
        flags |= getattr(re, name)
    try:
        pattern = re.compile(case['pattern'], flags)
    except re.error:
        return {'error': 'invalid_pattern'}
    except ValueError:
        return {'error': 'invalid_flags'}
    result = getattr(pattern, operation)(case['input'])
    if operation != 'findall' and result is not None:
        result = dict(
            group=result.group(), groups=result.groups(),
            group_dict=result.groupdict(), start=result.start(), end=result.end(),
            pos=result.pos, span=result.span(), regs=result.regs,
            last_group=result.lastgroup, last_index=result.lastindex)
    # Normalize tuples, including findall's multiple capture groups, to arrays.
    return json.loads(json.dumps({'result': result}))


def evaluate_json(cases_json):
    return json.dumps(dict(
        python=platform.python_version(),
        implementation=platform.python_implementation(),
        results=[dict(id=case['id'], **evaluate(case))
                 for case in json.loads(cases_json)]), ensure_ascii=True)
