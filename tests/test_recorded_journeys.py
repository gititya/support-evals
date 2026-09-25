import unittest

from support_evals.recorded_journeys import review_voice, review_copilot


def response(status='guiding', **fields):
    return {'http_status': 200, 'body': {'status': status, 'session_id': 'one', **fields}}


class RecordedJourneyTests(unittest.TestCase):
    def test_later_correct_caption_does_not_erase_old_mismatch(self):
        report = review_voice({'responses': [
            response(message='Open Account', guidance={'caption': 'Open Export'}),
            response(message='Open Export', guidance={'caption': 'Open Export'}),
        ]}, 'source')
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(report['checks'][0]['status'], 'fail')
        self.assertEqual(report['checks'][1]['status'], 'pass')

    def test_observed_navigation_cannot_close_without_confirmation(self):
        report = review_voice({'responses': [response('resolved', history=[
            {'kind': 'observed_result'}])]}, 'source')
        self.assertEqual(report['status'], 'fail')

    def test_later_unsure_overrides_earlier_yes(self):
        report = review_voice({'responses': [response('resolved', confirmation='yes', history=[
            {'kind': 'observed_result'}, {'kind': 'customer_confirmation', 'answer': 'yes'},
            {'kind': 'customer_confirmation', 'answer': 'unsure'}])]}, 'source')
        self.assertEqual(report['status'], 'fail')

    def test_failed_request_stays_error(self):
        report = review_voice({'responses': [{'http_status': 500, 'body': {}}]}, 'source')
        self.assertEqual(report['status'], 'error')

    def test_handoff_without_receipt_abstains(self):
        report = review_voice({'responses': [response('handoff', reference='case')]}, 'source')
        self.assertEqual(report['checks'][0]['status'], 'abstention')

    def test_copilot_read_does_not_prove_good_advice(self):
        report = review_copilot({'history': [{'type': 'read'}, {'type': 'private_advice'}]}, 'source')
        self.assertEqual(report['status'], 'abstention')

    def test_copilot_missing_or_late_sources_do_not_pass_inventory(self):
        for types in (['private_advice'], ['private_advice', 'read'],
                      ['customer_update', 'private_advice', 'read'],
                      ['read', 'private_advice']):
            with self.subTest(types=types):
                report = review_copilot({'history': [{'type': t} for t in types]}, 'source')
                self.assertEqual(report['checks'][0]['status'], 'abstention')

    def test_copilot_inventory_does_not_certify_support_judgment(self):
        report = review_copilot({'history': [{'type': t} for t in
            ['customer_update', 'private_advice', 'rep_answer', 'read', 'private_advice']]}, 'source')
        self.assertEqual(report['checks'][0]['status'], 'pass')
        self.assertEqual(report['checks'][1]['status'], 'abstention')


if __name__ == '__main__':
    unittest.main()
