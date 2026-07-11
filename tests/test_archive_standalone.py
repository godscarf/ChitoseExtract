"""单独执行归档步骤时应能处理音声库外的就地作品目录。"""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import task_runner
from timeline import Archive, Timeline


class TestArchiveStandalone(unittest.TestCase):
    def setUp(self):
        task_runner.clear()
        task_runner.progress_ui = MagicMock()
        self._prev_conf = task_runner.conf
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self._tmpdir.__enter__()
        self.output = os.path.join(self.tmp, 'output')
        self.download = os.path.join(self.tmp, 'download')
        os.makedirs(self.output)
        os.makedirs(self.download)
        task_runner.conf = SimpleNamespace(
            output_path=self.output,
            resource_path=os.path.join(self.tmp, 'resource'),
            recycle_path=os.path.join(self.tmp, 'recycle'),
            logical_deletion=True,
        )
        os.makedirs(task_runner.conf.resource_path)
        os.makedirs(task_runner.conf.recycle_path)
        task_runner.logger = None

    def tearDown(self):
        task_runner.conf = self._prev_conf
        task_runner.clear()
        self._tmpdir.__exit__(None, None, None)

    def test_archive_moves_external_work_root(self):
        work_root = os.path.join(self.download, 'RJ01653819_pk')
        os.makedirs(work_root)
        with open(os.path.join(work_root, 'track.wav'), 'wb') as fh:
            fh.write(b'data')

        archive = Archive(work_root)
        timeline = Timeline(archive, 'create_timeline', archive)
        task_runner.timelines.append(timeline)

        task_runner.archive_loop()

        self.assertFalse(os.path.isdir(work_root))
        moved = os.listdir(self.output)
        self.assertEqual(len(moved), 1)
        self.assertIn('RJ01653819', moved[0])

    def test_prepare_archive_queue_registers_dropped_folder(self):
        work_root = os.path.join(self.download, 'RJ01629264_pk')
        os.makedirs(work_root)

        archive = Archive(work_root)
        timeline = Timeline(archive, 'create_timeline', archive)
        task_runner.timelines.append(timeline)

        task_runner.prepare_archive_queue()

        self.assertIn(os.path.normpath(work_root), task_runner._work_roots)


if __name__ == '__main__':
    unittest.main()
