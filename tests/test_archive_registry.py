import unittest

import archive_registry


class ArchiveRegistryTests(unittest.TestCase):
    def setUp(self):
        archive_registry.clear()

    def test_discovered_vs_unzipped(self):
        archive_registry.note_discovered(r'D:\work\a.7z')
        self.assertTrue(archive_registry.is_discovered(r'D:\work\a.7z'))
        self.assertFalse(archive_registry.is_unzipped(r'D:\work\a.7z'))

        archive_registry.mark_unzipped(r'D:\work\a.7z')
        self.assertTrue(archive_registry.is_unzipped(r'D:\work\a.7z'))

    def test_case_insensitive(self):
        archive_registry.note_discovered(r'D:\Work\A.7Z')
        self.assertTrue(archive_registry.is_discovered(r'd:\work\a.7z'))


    def test_pending_discovered_under(self):
        archive_registry.note_discovered(r'D:\work\album\inner.zip')
        archive_registry.mark_unzipped(r'D:\work\album.7z')
        pending = archive_registry.pending_discovered_under(r'D:\work\album')
        self.assertEqual(len(pending), 1)


if __name__ == '__main__':
    unittest.main()
