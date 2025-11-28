import unittest
import os
import shutil
import time
import tempfile
from backup_core import BackupManager

class TestBackupManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.test_dir, 'src')
        self.dst_dir = os.path.join(self.test_dir, 'dst')
        os.makedirs(self.src_dir)
        os.makedirs(self.dst_dir)
        self.manager = BackupManager()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content='content'):
        with open(path, 'w') as f:
            f.write(content)

    def test_full_backup(self):
        # Create files
        self.create_file(os.path.join(self.src_dir, 'file1.txt'), 'data1')
        self.create_file(os.path.join(self.src_dir, 'file2.txt'), 'data2')
        
        # Run backup
        gen = self.manager.backup_generator(self.src_dir, self.dst_dir)
        for _ in gen: pass # Consume generator
        
        # Check files exist
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, 'file2.txt')))

    def test_incremental_backup(self):
        # Initial backup
        src_file = os.path.join(self.src_dir, 'data.txt')
        dst_file = os.path.join(self.dst_dir, 'data.txt')
        
        self.create_file(src_file, 'v1')
        for _ in self.manager.backup_generator(self.src_dir, self.dst_dir): pass
        
        # Check content
        with open(dst_file, 'r') as f: self.assertEqual(f.read(), 'v1')
        
        # Modify source (wait a bit to ensure mtime diff if filesystem is fast)
        time.sleep(1) # Wait for FS resolution
        self.create_file(src_file, 'v2_updated')
        
        # Run backup again
        actions = []
        for msg in self.manager.backup_generator(self.src_dir, self.dst_dir):
            if msg.get('type') == 'progress':
                actions.append(msg['action'])
        
        # Check if copied
        self.assertIn('copied', actions)
        with open(dst_file, 'r') as f: self.assertEqual(f.read(), 'v2_updated')

    def test_skip_unmodified(self):
        src_file = os.path.join(self.src_dir, 'static.txt')
        self.create_file(src_file, 'static')
        
        # First run
        for _ in self.manager.backup_generator(self.src_dir, self.dst_dir): pass
        
        # Second run (no changes)
        actions = []
        for msg in self.manager.backup_generator(self.src_dir, self.dst_dir):
            if msg.get('type') == 'progress':
                actions.append(msg['action'])
                
        self.assertIn('skipped', actions)
        self.assertNotIn('copied', actions)

if __name__ == '__main__':
    unittest.main()

