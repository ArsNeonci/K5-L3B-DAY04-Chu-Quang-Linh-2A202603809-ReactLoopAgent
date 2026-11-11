"""Các nhánh lỗi của loop, dùng fake provider, không gọi mạng."""
import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class AgentRobustnessTests(unittest.TestCase):
    @patch('agent.time.sleep')
    def test_disconnect_retries_within_step_budget(self, sleep):
        provider = Mock()
        provider.complete.side_effect = [ConnectionResetError('private body'), final('OK')]
        result = run_agent('status', provider, StatusTools(), max_steps=2)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(provider.complete.call_count, 2)
        self.assertEqual(result['trace'][0]['event'], 'model_retry')
        self.assertEqual(result['trace'][-1]['step'], 2)
        self.assertNotIn('private body', json.dumps(result))
        sleep.assert_called_once_with(1)

    @patch('agent.time.sleep')
    def test_persistent_disconnect_has_bounded_retries(self, sleep):
        provider = Mock()
        provider.complete.side_effect = ConnectionResetError()
        result = run_agent('status', provider, StatusTools(), max_steps=8)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(provider.complete.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        provider.reset_mock()
        result = run_agent('status', provider, StatusTools(), max_steps=1)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(provider.complete.call_count, 1)

    def test_http_authorization_error_is_not_retried(self):
        provider = Mock()
        provider.complete.side_effect = HTTPError('https://example.invalid', 401,
                                                  'Unauthorized', {}, None)
        result = run_agent('status', provider, StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(provider.complete.call_count, 1)

    def test_provider_failure_returns_structured_error_without_exception_body(self):
        provider = Mock()
        provider.complete.side_effect = RuntimeError('secret-request-body')
        result = run_agent('status', provider, StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('secret-request-body', json.dumps(result))
        self.assertEqual(result['trace'][-1]['event'], 'error')

    def test_tool_exception_does_not_drop_remaining_calls(self):
        response = tool_call('a', 'get_status', '{"provider":"github"}')
        second = tool_call('b', 'get_status', '{"provider":"cloudflare"}')
        response['calls'] += second['calls']
        response['message']['tool_calls'] += second['message']['tool_calls']
        tools = Mock()
        tools.system_prompt = 'Test'
        tools.schemas = []
        tools.execute.side_effect = [TimeoutError('untrusted body'), {'provider': 'cloudflare'}]
        provider = FakeProvider([response, final('Chỉ kiểm tra được Cloudflare.')])
        result = run_agent('status', provider, tools)
        self.assertEqual(result['status'], 'completed')
        returned = provider.histories[1][-2:]
        self.assertEqual([m['tool_call_id'] for m in returned], ['a', 'b'])
        self.assertEqual(json.loads(returned[0]['content'])['error'], 'TimeoutError')
        self.assertEqual(json.loads(returned[1]['content'])['provider'], 'cloudflare')

    def test_json_array_is_invalid_arguments(self):
        provider = FakeProvider([tool_call('a', 'get_status', '[]'), final()])
        tools = Mock(spec=StatusTools)
        result = run_agent('status', provider, tools)
        self.assertEqual(result['status'], 'completed')
        tools.execute.assert_not_called()
        self.assertEqual(json.loads(provider.histories[1][-1]['content'])['error'],
                         'INVALID_ARGUMENTS')

    def test_unknown_tool_returns_observation(self):
        provider = FakeProvider([tool_call('a', 'missing', '{}'), final()])
        result = run_agent('status', provider, StatusTools())
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['trace'][1]['result']['error'], 'UNKNOWN_TOOL')

    def test_abnormal_finish_and_empty_answer_are_errors(self):
        for finish, content in [('content_filter', 'partial'), ('stop', None),
                                ('tool_calls', ''), ('stop', '   ')]:
            with self.subTest(finish=finish, content=content):
                response = final(content)
                response['finish'] = finish
                result = run_agent('status', FakeProvider([response]), StatusTools())
                self.assertEqual(result['status'], 'error')

    def test_usage_and_assistant_metadata_are_preserved(self):
        response = tool_call('a', 'get_status', '{"provider":"github"}')
        response['message']['metadata'] = {'provider_tag': 'original'}
        response['usage'] = {'total_tokens': 12}
        provider = FakeProvider([response, final()])
        result = run_agent('status', provider, StatusTools())
        self.assertEqual(result['usage'][0], {'total_tokens': 12})
        self.assertEqual(provider.histories[1][-2], response['message'])

    def test_invalid_budget_never_calls_provider(self):
        for budget in [0, -1, True, 1.5]:
            with self.subTest(budget=budget):
                provider = Mock()
                self.assertEqual(run_agent('status', provider, StatusTools(), budget)['status'],
                                 'error')
                provider.complete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
