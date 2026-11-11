"""Verify streaming and validation without making paid API calls."""
import http.client
import json
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer

from agent import run_agent, SYSTEM_PROMPT
from demo_server import DemoHandler, TOKEN
from status_tools import StatusTools


class DemoTests(unittest.TestCase):
    def test_live_mode_is_explicit_in_model_context(self):
        messages_seen = []
        class FakeProvider:
            def complete(self, messages, _schemas):
                messages_seen.extend(messages)
                return {'message': {'role': 'assistant', 'content': 'Done'},
                        'calls': [], 'finish': 'stop', 'usage': {}}
        result = run_agent('Check status', FakeProvider(), StatusTools('live'))
        self.assertEqual(result['status'], 'completed')
        self.assertIn('LIVE', messages_seen[0]['content'])
        self.assertIn('captured_at', messages_seen[0]['content'])

    def test_snapshot_prompt_stays_identical_to_eval_prompt(self):
        messages_seen = []
        class FakeProvider:
            def complete(self, messages, _schemas):
                messages_seen.extend(messages)
                return {'message': {'role': 'assistant', 'content': 'Done'},
                        'calls': [], 'finish': 'stop', 'usage': {}}
        run_agent('Check status', FakeProvider(), StatusTools('snapshot'))
        self.assertEqual(messages_seen[0]['content'], SYSTEM_PROMPT)

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), DemoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, token=TOKEN):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        conn.request(method, path, body=json.dumps(body) if body is not None else None,
                     headers={'X-Demo-Token': token, 'Content-Type': 'application/json'})
        response = conn.getresponse()
        status, data = response.status, response.read()
        conn.close()
        return status, data

    def test_rejects_unauthorized_and_invalid_runs(self):
        self.assertEqual(self.request('POST', '/api/run', {}, token='bad')[0], 403)
        for args in ({}, {'question': 'test', 'max_steps': 0},
                     {'question': 'test', 'source': 'invalid'},
                     {'question': 'test', 'bonus': 'false'}):
            self.assertEqual(self.request('POST', '/api/run', args)[0], 400)

    def test_stream_delivers_events_then_final_result(self):
        def fake_agent(question, provider, tools, max_steps, on_event):
            on_event({'event': 'model_start', 'step': 1})
            return {'status': 'completed', 'answer': 'Đã kiểm tra', 'trace': [], 'usage': []}
        with patch('demo_server.Provider') as provider, patch('demo_server.run_agent', side_effect=fake_agent):
            provider.return_value.name = 'fake'
            provider.return_value.model = 'fake-model'
            status, data = self.request('POST', '/api/run', {'question': 'Kiểm tra GitHub'})
        self.assertEqual(status, 200)
        events = [json.loads(line) for line in data.splitlines()]
        self.assertEqual([e['event'] for e in events], ['started', 'model_start', 'result'])
        self.assertEqual(events[-1]['result']['answer'], 'Đã kiểm tra')

    def test_callback_keeps_original_trace_contract(self):
        class FakeProvider:
            def complete(self, *_args):
                return {'message': {'role': 'assistant', 'content': 'Done'},
                        'calls': [], 'finish': 'stop', 'usage': {}}
        events = []
        result = run_agent('Hello', FakeProvider(), object(), on_event=events.append)
        self.assertEqual([e['event'] for e in result['trace']], ['model', 'completed'])
        self.assertEqual([e['event'] for e in events], ['model_start', 'model', 'completed'])


if __name__ == '__main__':
    unittest.main()
