from pathlib import Path
import sys
import tempfile
import types
import unittest

from gflo.mini_worker import SENTINEL, MiniSweWorker, SandboxEnvironment, model_kwargs


class Submitted(Exception):
    def __init__(self, *messages):
        super().__init__(messages)
        self.messages = messages


class Sandbox:
    def __init__(self, outputs):
        self.outputs, self.commands = list(outputs), []
    def cleanup(self, workspace):
        pass
    def execute(self, workspace, command, **kwargs):
        self.commands.append((command, kwargs))
        return self.outputs.pop(0)


def fake_minisweagent(test, commands, error=None):
    """A minimal DefaultAgent: runs the scripted commands through the environment, as the real loop would."""
    class LitellmModel:
        def __init__(self, **kwargs):
            test.model = kwargs
    class DefaultAgent:
        def __init__(self, model, env, **kwargs):
            self.env, self.config, self.n_calls = env, kwargs, 0
            test.agent = self
        def run(self, task):
            test.task_text = task
            if error:
                raise error
            for command in commands:
                self.n_calls += 1
                try:
                    self.env.execute({'command': command})
                except Submitted as done:
                    return done.messages[0]['extra']
            return {'exit_status': 'LimitsExceeded', 'submission': ''}
    modules = {'minisweagent': types.ModuleType('minisweagent'),
               'minisweagent.agents': types.ModuleType('minisweagent.agents'),
               'minisweagent.agents.default': types.SimpleNamespace(DefaultAgent=DefaultAgent),
               'minisweagent.exceptions': types.SimpleNamespace(Submitted=Submitted),
               'minisweagent.models': types.ModuleType('minisweagent.models'),
               'minisweagent.models.litellm_model': types.SimpleNamespace(LitellmModel=LitellmModel)}
    for name, module in modules.items():
        test.addCleanup(sys.modules.pop, name, None)
        sys.modules[name] = module


class MiniWorkerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.workspace = Path(directory.name) / 'workspace'
        self.workspace.mkdir()
        self.task = {'objective': 'Fix clamp', 'max_turns': 40, 'checks': [['python', '/acceptance/check.py']],
                     'environment': {'profile': 'python-project', 'image': 'i', 'runtime': 'r'}}
        self.config = {'endpoint': 'http://127.0.0.1:18000', 'model': 'coder', 'reasoning': 'medium'}

    def test_commands_run_in_the_sandbox_and_the_sentinel_submits(self):
        sandbox = Sandbox([{'exit_code': 0, 'output': 'app.py\n'}, {'exit_code': 0, 'output': SENTINEL + '\n'}])
        fake_minisweagent(self, ['ls', 'echo ' + SENTINEL])
        result = MiniSweWorker(self.config, sandbox)(self.workspace, self.task, {'passed': False, 'error': 'old'}, 2)
        self.assertEqual(result['exit_status'], 'Submitted')
        self.assertFalse(result['limited'])
        self.assertEqual(result['turns'], 2)
        self.assertEqual(sandbox.commands[0], (['sh', '-lc', 'ls'], {'timeout': 300}))
        self.assertIn('Fix clamp', self.task_text)
        self.assertIn('Previous attempt evidence', self.task_text)
        self.assertIn('/acceptance/check.py', self.task_text)
        self.assertEqual(self.model['model_name'], 'openai/coder')
        self.assertEqual(self.model['model_kwargs']['api_base'], 'http://127.0.0.1:18000/v1')
        self.assertEqual(self.agent.config['step_limit'], 40)
        self.assertEqual(self.agent.config['output_path'], self.workspace.parent / 'attempts/2/mini-trajectory.json')

    def test_failed_sentinel_command_does_not_submit_and_limits_are_reported(self):
        environment = SandboxEnvironment(Sandbox([{'exit_code': 1, 'output': SENTINEL + '\n'}]), self.workspace, 60, Submitted)
        self.assertEqual(environment.execute({'command': 'false'})['returncode'], 1)
        sandbox = Sandbox([{'exit_code': 0, 'output': ''}])
        fake_minisweagent(self, ['ls'])
        result = MiniSweWorker(dict(self.config, navigation={'max_turns': 7}), sandbox)(self.workspace, self.task, None, 1)
        self.assertTrue(result['limited'])
        self.assertEqual(self.agent.config['step_limit'], 7)

    def test_malformed_model_calls_end_the_attempt_and_other_errors_stop_the_run(self):
        fake_minisweagent(self, [], RuntimeError('Failed to parse tool call arguments as JSON'))
        result = MiniSweWorker(self.config, Sandbox([]))(self.workspace, self.task, None, 1)
        self.assertEqual(result['exit_status'], 'MalformedToolCall')
        self.assertTrue(result['limited'])
        fake_minisweagent(self, [], RuntimeError('connection refused'))
        with self.assertRaisesRegex(RuntimeError, 'connection refused'):
            MiniSweWorker(self.config, Sandbox([]))(self.workspace, self.task, None, 1)

    def test_reasoning_settings_match_the_gflo_worker(self):
        kwargs = model_kwargs(self.config)
        self.assertEqual(kwargs['reasoning_effort'], 'medium')
        self.assertEqual(kwargs['extra_body'], {'chat_template_kwargs': {'enable_thinking': True}, 'thinking_budget_tokens': 1024})
        self.assertEqual(model_kwargs({'endpoint': 'http://127.0.0.1:1/'})['extra_body'], {'chat_template_kwargs': {'enable_thinking': False}})


if __name__ == '__main__':
    unittest.main()
