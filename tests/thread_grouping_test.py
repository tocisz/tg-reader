import unittest
from thread_grouping import group_threads

class TestThreadGrouping(unittest.TestCase):
    def test_grouping(self):
        messages = [
            {'id': 1, 'reply_to': None, 'timestamp': '2024-01-01 10:00:00', 'text': 'Root A'},
            {'id': 2, 'reply_to': 1, 'timestamp': '2024-01-01 10:01:00', 'text': 'Reply to A'},
            {'id': 3, 'reply_to': 1, 'timestamp': '2024-01-01 10:02:00', 'text': 'Another reply to A'},
            {'id': 4, 'reply_to': 2, 'timestamp': '2024-01-01 10:03:00', 'text': 'Reply to reply'},
            {'id': 5, 'reply_to': None, 'timestamp': '2024-01-01 11:00:00', 'text': 'Root B'},
            {'id': 6, 'reply_to': 5, 'timestamp': '2024-01-01 11:01:00', 'text': 'Reply to B'},
        ]
        threads = group_threads(messages)
        # Thread for root A should include 1,2,3,4
        a_ids = [msg['id'] for msg in threads[1]]
        self.assertCountEqual(a_ids, [1,2,3,4])
        # Thread for root B should include 5,6
        b_ids = [msg['id'] for msg in threads[5]]
        self.assertCountEqual(b_ids, [5,6])
        # Each thread should be sorted by timestamp
        self.assertEqual([msg['id'] for msg in threads[1]], [1,2,3,4])
        self.assertEqual([msg['id'] for msg in threads[5]], [5,6])

if __name__ == '__main__':
    unittest.main()
