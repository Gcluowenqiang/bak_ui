import unittest
import os
import json
import tempfile
from history_manager import HistoryManager

class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        self.test_file = tempfile.mktemp()
        self.manager = HistoryManager(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_and_retrieve(self):
        self.manager.add_record('/src', '/dst')
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['src'], '/src')
        self.assertEqual(history[0]['dst'], '/dst')

    def test_update_order(self):
        self.manager.add_record('/src1', '/dst1')
        self.manager.add_record('/src2', '/dst2')
        
        history = self.manager.get_history()
        self.assertEqual(history[0]['src'], '/src2')
        
        # Re-add first one, should move to top
        self.manager.add_record('/src1', '/dst1')
        history = self.manager.get_history()
        self.assertEqual(history[0]['src'], '/src1')
        self.assertEqual(len(history), 2)

    def test_limit_size(self):
        for i in range(15):
            self.manager.add_record(f'/src{i}', f'/dst{i}')
            
        history = self.manager.get_history()
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]['src'], '/src14')

    def test_clear(self):
        self.manager.add_record('/src', '/dst')
        self.manager.clear_history()
        self.assertEqual(len(self.manager.get_history()), 0)

if __name__ == '__main__':
    unittest.main()

