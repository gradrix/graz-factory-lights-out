"""Negative checks for the synthetic probe scorer; no inference required."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

scripts = Path(__file__).resolve().parents[1] / 'scripts'
with patch.object(sys, 'path', [str(scripts), *sys.path]):
    spec = importlib.util.spec_from_file_location('benchmark_serving', scripts / 'benchmark_serving.py')
    benchmark = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark)


def response(content, **usage):
    return {'choices': [{'message': {'content': content}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20, **usage}}


class ScoringTests(unittest.TestCase):
    def test_bad_json_values_cannot_pass(self):
        for content in ('{"ok":1,"value":7}', '{"ok":true,"value":true}',
                        '{"ok":true,"value":7,"extra":1}', 'looks good'):
            self.assertFalse(benchmark.validate('json', response(content), 8192))
        self.assertTrue(benchmark.validate('json', response('{"ok":true,"value":7}'), 8192))

    def test_missing_or_inconsistent_usage_fails(self):
        self.assertFalse(benchmark.validate('plain', response('OK', total_tokens=21), 8192))
        self.assertFalse(benchmark.validate('plain', response('OK', prompt_tokens=True), 8192))
        self.assertFalse(benchmark.validate('plain', {}, 8192))

    def test_short_input_cannot_pass_long_context_case(self):
        self.assertFalse(benchmark.validate('long_json', response('{"ok":true,"value":7}'), 8192))

    def test_truncated_output_fails(self):
        value=response('OK'); value['choices'][0]['finish_reason']='length'
        self.assertFalse(benchmark.validate('plain', value, 8192))

    def test_tool_call_must_have_expected_arguments(self):
        value=response(None)
        value['choices'][0]['finish_reason']='tool_calls'
        value['choices'][0]['message']['tool_calls']=[{'function': {'name': 'read_file', 'arguments': '{"path":"/etc/passwd"}'}}]
        self.assertFalse(benchmark.validate('tool', value, 8192))
        value['choices'][0]['message']['tool_calls'][0]['function']['arguments']='{"path":"src/provider.py"}'
        self.assertTrue(benchmark.validate('tool', value, 8192))

    def test_filtered_or_multiple_choices_cannot_pass(self):
        value=response('OK'); value['choices'][0]['finish_reason']='content_filter'
        self.assertFalse(benchmark.validate('plain', value, 8192))
        value=response('OK'); value['choices'] *= 2
        self.assertFalse(benchmark.validate('plain', value, 8192))
