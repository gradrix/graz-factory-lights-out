"""mini-swe-agent as the gflo worker (roadmap phase 2 harness comparison).

Only the attempt loop changes: mini-swe-agent's DefaultAgent and tool-calling LitellmModel drive the same local
model, and every command still runs in gflo's offline sandbox. Acceptance, review, budgets and evidence stay with
the gflo controller. mini-swe-agent is not a gflo dependency; it is imported when an attempt starts (on the rig it
lives in ~/gflo-pp/mini-deps, added to PYTHONPATH for this arm only).

Differences from the published SWE-bench configuration, all forced by the task contract: the working directory is
/workspace, regression tests are part of the task, nothing can be installed, and submission is the bare sentinel
because the controller verifies the workspace itself. The observation template is the SWE-bench one.
"""
import json
import os
from pathlib import Path

from .environment import command_seconds, runtime_context
from .worker import MALFORMED_CALL, ModelWorker

SENTINEL = 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'
SYSTEM = 'You are a helpful assistant that can interact with a computer shell to solve programming tasks.'
INSTANCE = '''<pr_description>
Consider the following PR description:
{{task}}
</pr_description>

<instructions>
You're a software engineer interacting continuously with a computer by submitting commands.
Make the changes the PR description asks for in /workspace (the working directory for all commands), in a way that is general and consistent with the codebase, including the regression tests it asks for.

For each response, explain your reasoning, then make at least one bash tool call. You may make several calls when they are independent.
Every command runs in a new, offline, sandboxed shell: directory and environment changes do not persist, only files under /workspace do. Nothing can be installed. Use non-interactive commands.

When you have completed the work, submit with this exact command, on its own:
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT
You cannot continue working after submitting. The controller then runs the acceptance checks.
</instructions>'''
OBSERVATION = '''{% if output.exception_info -%}
<exception>{{output.exception_info}}</exception>
{% endif -%}
<returncode>{{output.returncode}}</returncode>
{% if output.output | length < 10000 -%}
<output>
{{ output.output -}}
</output>
{%- else -%}
<warning>
The output of your last command was too long.
Please try a different command that produces less output.
If you're looking at a file you can try use head, tail or sed to view a smaller number of lines selectively.
If you're using grep or find and it produced too much output, you can use a more selective search pattern.
If you really need to see something from the full command's output, you can redirect output to a file and then search in that file.
</warning>
{%- set elided_chars = output.output | length - 10000 -%}
<output_head>
{{ output.output[:5000] }}
</output_head>
<elided_chars>
{{ elided_chars }} characters elided
</elided_chars>
<output_tail>
{{ output.output[-5000:] }}
</output_tail>
{%- endif -%}'''


class SandboxEnvironment:
    """mini-swe-agent environment protocol over gflo's sandbox: one fresh offline container per command."""

    def __init__(self, sandbox, workspace, timeout, submitted):
        self.sandbox, self.workspace, self.timeout, self.submitted = sandbox, workspace, timeout, submitted

    def execute(self, action, cwd='', *, timeout=None):
        result = self.sandbox.execute(self.workspace, ['sh', '-lc', action.get('command', '')], timeout=self.timeout)
        output = {'output': result.get('output', ''), 'returncode': result.get('exit_code'),
                  'exception_info': f'Command timed out after {self.timeout} seconds' if result.get('timed_out') else ''}
        lines = output['output'].lstrip().splitlines(keepends=True)
        if lines and lines[0].strip() == SENTINEL and output['returncode'] == 0:
            raise self.submitted({'role': 'exit', 'content': ''.join(lines[1:]),
                                  'extra': {'exit_status': 'Submitted', 'submission': ''.join(lines[1:])}})
        return output

    def get_template_vars(self, **kwargs):
        return dict(kwargs, cwd='/workspace')

    def serialize(self):
        return {'info': {'config': {'environment_type': 'gflo.sandbox', 'timeout': self.timeout}}}


def model_kwargs(config):
    reasoning = config.get('reasoning', 'none')
    extra = {'chat_template_kwargs': {'enable_thinking': reasoning != 'none'}}
    if reasoning != 'none':
        extra['thinking_budget_tokens'] = 1024
    return {'api_base': config['endpoint'].rstrip('/') + '/v1', 'api_key': 'local', 'temperature': 0,
            'max_tokens': 4096, 'reasoning_effort': reasoning, 'extra_body': extra}


class MiniSweWorker(ModelWorker):
    """Keeps ModelWorker's endpoint checks and request() (used by review and question assessment)."""

    def __call__(self, workspace, task, previous, attempt):
        os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')  # litellm must not fetch its price list
        os.environ.setdefault('MSWEA_SILENT_STARTUP', '1')
        os.environ.setdefault('MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT', '3')  # a temperature-0 server error repeats
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.exceptions import Submitted
        from minisweagent.models.litellm_model import LitellmModel

        self.sandbox.cleanup(workspace)
        root = Path(workspace).parent
        trace = root / 'attempts' / str(attempt) / 'mini-trajectory.json'
        text = task['objective'] + '\n' + runtime_context(task) + '\nAcceptance commands: ' + json.dumps(task['checks'])
        if previous:
            text += '\n\nPrevious attempt evidence. Repair the retained files:\n' + json.dumps(previous)
        model = LitellmModel(model_name='openai/' + self.config['model'], model_kwargs=model_kwargs(self.config),
                             cost_tracking='ignore_errors', observation_template=OBSERVATION)
        environment = SandboxEnvironment(self.sandbox, workspace, command_seconds(task), Submitted)
        agent = DefaultAgent(model, environment, system_template=SYSTEM, instance_template=INSTANCE,
                             step_limit=self.navigation['max_turns'] or task['max_turns'], cost_limit=0,
                             wall_time_limit_seconds=1800, output_path=trace)
        try:
            result = agent.run(text)
        except Exception as error:  # same policy as the gflo worker: a malformed call ends the attempt
            if MALFORMED_CALL not in str(error):
                raise
            result = {'exit_status': 'MalformedToolCall', 'submission': ''}
        status = result.get('exit_status', '')
        return {'summary': result.get('submission', '') or status, 'harness': 'mini-swe-agent',
                'exit_status': status, 'turns': agent.n_calls, 'limited': status != 'Submitted'}
