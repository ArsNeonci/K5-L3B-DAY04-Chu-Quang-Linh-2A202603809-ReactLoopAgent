"""Retry hạ tầng không được chọn điểm cao hay chạy lại agent."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evals'))
import run_evals


def judge_reply(factuality=40):
    return {'finish': 'stop', 'calls': [], 'usage': {}, 'message': {'content': json.dumps({
        'factuality': factuality, 'completeness': 25, 'evidence': 20,
        'boundaries': 15, 'reason': 'test', 'improvement': ''})}}


class JudgeRetryTests(unittest.TestCase):
    def run_case(self, responses, status='completed', retries=2):
        judge = Mock()
        judge.complete.side_effect = responses
        args = SimpleNamespace(provider='gemini', model='agent', judge_provider='gemini',
                               judge_model='judge', max_steps=8, judge_retries=retries)
        case = {'id': 'test', 'question': 'question', 'expected': 'judge only'}
        result = {'status': status, 'answer': 'answer', 'trace': [], 'usage': []}
        with patch.object(run_evals, 'Provider', return_value=judge), \
                patch.object(run_evals, 'run_agent', return_value=result) as agent:
            item = run_evals.run_case(case, args)
            agent.assert_called_once()
        return item['grade'], judge

    def test_invalid_format_retries_and_keeps_error_history(self):
        bad = judge_reply()
        bad['message']['content'] = '{}'
        grade, judge = self.run_case([bad, judge_reply()])
        self.assertEqual(grade['score'], 100)
        self.assertEqual(grade['judge_attempts'], 2)
        self.assertEqual(len(grade['judge_errors']), 1)
        self.assertEqual(judge.complete.call_count, 2)

    def test_valid_low_score_is_accepted_immediately(self):
        grade, judge = self.run_case([judge_reply(0), judge_reply()])
        self.assertEqual(grade['score'], 60)
        self.assertEqual(judge.complete.call_count, 1)

    def test_retries_exhausted_stays_unscored(self):
        bad = judge_reply()
        bad['message']['content'] = '{}'
        grade, judge = self.run_case([bad, bad, bad])
        self.assertIsNone(grade['score'])
        self.assertEqual(judge.complete.call_count, 3)

    def test_failed_agent_does_not_call_judge(self):
        grade, judge = self.run_case([], status='error')
        self.assertEqual(grade['status'], 'unscored')
        judge.complete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
