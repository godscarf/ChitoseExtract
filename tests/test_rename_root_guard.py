"""禁止把下载目录等上层容器整夹重命名。"""

import os
import unittest
from types import SimpleNamespace
from unittest import mock

import task_runner


class TestRenameRootGuard(unittest.TestCase):
    def setUp(self):
        task_runner._work_roots.clear()
        task_runner._work_root_preferred_names.clear()
        self._prev_conf = task_runner.conf
        task_runner.conf = SimpleNamespace(
            output_path=r'D:\奥术魔刃\同人音声',
            resource_path=r'D:\下载\临时',
            recycle_path=r'D:\下载缓冲\recycle',
        )

    def tearDown(self):
        task_runner.conf = self._prev_conf
        task_runner._work_roots.clear()
        task_runner._work_root_preferred_names.clear()

    def test_download_folder_is_container(self):
        self.assertTrue(task_runner._is_container_or_library_root(r'D:\下载'))
        self.assertTrue(task_runner._is_container_or_library_root(r'D:\\'))
        self.assertTrue(task_runner._is_container_or_library_root(r'D:\奥术魔刃\同人音声'))

    def test_work_folder_under_download_is_ok(self):
        self.assertFalse(
            task_runner._is_container_or_library_root(r'D:\下载\RJ01620216')
        )
        self.assertFalse(
            task_runner._is_container_or_library_root(
                r'D:\奥术魔刃\同人音声\[RJ01620216]作品'
            )
        )

    def test_refuse_register_download_as_work_root(self):
        task_runner._register_work_root(r'D:\下载')
        self.assertNotIn(os.path.normpath(r'D:\下载'), task_runner._work_roots)

    def test_narrow_from_download_to_child(self):
        download = r'D:\下载'
        work = r'D:\下载\RJ01620216'
        nested = r'D:\下载\RJ01620216\inner'

        def _is_container(path):
            return os.path.normcase(os.path.normpath(path)) == os.path.normcase(
                os.path.normpath(download)
            )

        with mock.patch('file_ops.is_path_under', return_value=True), mock.patch(
            'file_ops.is_dir_path', return_value=True,
        ), mock.patch.object(
            task_runner, '_is_container_or_library_root', side_effect=_is_container,
        ):
            narrowed = task_runner._narrow_rename_root(download, nested)
        self.assertEqual(os.path.normcase(narrowed), os.path.normcase(work))

    def test_under_work_root_prefers_deeper(self):
        shallow = r'D:\下载'
        deep = r'D:\下载\作品A'
        # 即使误登记了浅层，也应优先返回更深的登记根
        task_runner._work_roots.add(os.path.normpath(shallow))
        task_runner._work_roots.add(os.path.normpath(deep))
        with mock.patch('file_ops.is_path_under', side_effect=lambda root, path: (
            os.path.normcase(os.path.normpath(path)).startswith(
                os.path.normcase(os.path.normpath(root)).rstrip('\\')
            )
        )):
            found = task_runner._under_work_root(r'D:\下载\作品A\file.wav')
        self.assertEqual(os.path.normcase(found), os.path.normcase(deep))


if __name__ == '__main__':
    unittest.main()
