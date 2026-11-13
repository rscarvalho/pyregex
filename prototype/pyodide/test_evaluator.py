import json
from pathlib import Path
import unittest

from evaluator import evaluate, evaluate_json


class EvaluatorTests(unittest.TestCase):
    def test_engine_cases_only(self):
        fixture = Path(__file__).resolve().parents[2] / 'tests/fixtures/regex_baseline.json'
        cases = json.loads(fixture.read_text(encoding='utf-8'))['engine_cases']
        self.assertEqual(27, len(cases))
        for case in cases:
            with self.subTest(case=case['id']):
                expected = ({'error': case['error']} if 'error' in case
                            else {'result': case['expected']})
                self.assertEqual(expected, evaluate(case))
        self.assertEqual(27, len(json.loads(evaluate_json(json.dumps(cases)))['results']))

    def test_data_not_source_and_invalid_operation(self):
        case = dict(id='data', operation='match', flags=[], pattern='.*',
                    input="'); raise RuntimeError('not code') # 😀")
        self.assertEqual(case['input'], evaluate(case)['result']['group'])
        case['operation'] = '__getattribute__'
        self.assertEqual({'error': 'invalid_operation'}, evaluate(case))
        case['operation'] = 'match'
        case['flags'] = ['not_a_flag']
        self.assertEqual({'error': 'invalid_flags'}, evaluate(case))

    def test_bounded_output_overflow_fixture(self):
        case = dict(id='output-overflow', operation='findall', flags=[],
                    pattern='(?=' + '(a?)' * 32 + ')', input='a' * 8192)
        output = evaluate_json(json.dumps([case]))
        self.assertGreater(len(output), 1048576)
        self.assertLess(len(output), 1500000)
        self.assertEqual(8193, len(json.loads(output)['results'][0]['result']))


if __name__ == '__main__':
    unittest.main()
