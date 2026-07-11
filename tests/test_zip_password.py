import unittest

import tempfile

import os

from unittest import mock



from zip import Zip



class ZipPasswordTests(unittest.TestCase):

    def test_encrypted_container_requires_password(self):

        archive = Zip(r'D:\work\RJ01620216.7z', ['secret'])

        archive.file_list = ['inner.zip']

        archive.compression_ratio_info = {'encrypted': True}

        archive.mark_namelist_scanned('secret')

        self.assertTrue(archive.is_encrypted())

        self.assertTrue(archive.container_requires_password())



    def test_encrypted_7z_empty_password_scan_not_current(self):

        archive = Zip(r'D:\work\RJ01620216.7z', ['secret'])

        archive.file_list = ['inner.zip']

        archive.compression_ratio_info = {'encrypted': True}

        archive.mark_namelist_scanned('')

        self.assertTrue(archive.container_requires_password())

        self.assertFalse(archive.is_namelist_current())



    def test_encrypted_container_with_password_requires_password(self):

        archive = Zip(r'D:\work\secret.7z', ['secret'])

        archive.file_list = ['track.wav']

        archive.compression_ratio_info = {'encrypted': True}

        archive.mark_namelist_scanned('secret')

        self.assertTrue(archive.container_requires_password())



    def test_plain_empty_password_still_current(self):

        archive = Zip(r'D:\work\outer.7z', [''])

        archive.file_list = ['track.wav']

        archive.compression_ratio_info = {'encrypted': False}

        archive.mark_namelist_scanned('')

        self.assertTrue(archive.is_namelist_current())

        self.assertFalse(archive.container_requires_password())





class FileOpsCoveredStrategyTests(unittest.TestCase):

    def test_standard_zip_disallows_covered_strategy(self):

        import file_ops

        with tempfile.TemporaryDirectory() as tmp:

            zip_path = os.path.join(tmp, 'inner.zip')

            with open(zip_path, 'wb') as fh:

                fh.write(b'PK\x03\x04' + b'\x00' * 16)

            probe = file_ops.ArchiveProbe(True, covered=False)

            strategies = file_ops.build_archive_open_strategies(

                probe, '.zip', zip_path,

            )

            self.assertTrue(any(not covered for _, covered in strategies))

            self.assertFalse(any(covered for _, covered in strategies))



    def test_numeric_zst_is_covered_junk(self):

        import file_ops

        self.assertTrue(file_ops.is_covered_extract_junk_basename('2.zst'))

        self.assertTrue(file_ops.is_covered_extract_junk_basename('1'))





class UnzipperOuterPasswordTests(unittest.TestCase):

    def test_corrupt_inner_zip_is_not_genuine(self):

        from unzip_process_pool import ProcessResourceManager

        from unzipper import Unzipper



        with tempfile.TemporaryDirectory() as tmp:

            corrupt = os.path.join(tmp, 'RJ01620216.zip')

            with open(corrupt, 'wb') as fh:

                fh.write(b'PK\x03\x04' + b'\xff' * 64)



            unzipper = Unzipper(mock.MagicMock(), ProcessResourceManager(4))

            unzipper.driver.get_namelist = mock.MagicMock(

                return_value=(['1', '2.zst'], {'encrypted': False}),

            )

            unzipper.driver.test_archive = mock.MagicMock(return_value=(False, 'Headers Error'))



            self.assertFalse(unzipper._extracted_archive_is_genuine(corrupt))



    def test_7z_outer_wrong_password_does_not_partial_succeed(self):

        from unzip_process_pool import ProcessResourceManager

        from unzipper import Unzipper



        with tempfile.TemporaryDirectory() as tmp:

            outer_path = os.path.join(tmp, 'RJ01620216.7z')

            output_path = os.path.join(tmp, 'out')

            os.makedirs(output_path)

            with open(outer_path, 'wb') as fh:

                fh.write(b'7z\xbc\xaf\x27\x1c' + b'\x00' * 16)

            with open(os.path.join(output_path, 'RJ01620216.zip'), 'wb') as fh:

                fh.write(b'PK\x03\x04' + b'\xff' * 64)



            zip_obj = Zip(outer_path, ['wrong'], False)

            zip_obj.file_list = ['RJ01620216.zip']

            zip_obj.compression_ratio_info = {'encrypted': True}

            zip_obj.mark_namelist_scanned('wrong')



            unzipper = Unzipper(mock.MagicMock(), ProcessResourceManager(4))

            unzipper._run_single_unzip = mock.MagicMock(

                return_value=(1, 'ERROR: CRC Failed in encrypted file. Wrong password? : RJ01620216.zip'),

            )

            unzipper._output_has_usable_partial_extract = mock.MagicMock(return_value=False)



            self.assertFalse(unzipper.single_threaded_unzip(zip_obj, output_path, known_password=True))

    def test_disguised_mp3_tries_password_library(self):
        from unzip_process_pool import ProcessResourceManager
        from unzipper import Unzipper

        with tempfile.TemporaryDirectory() as tmp:
            carrier = os.path.join(tmp, 'lala.mp3')
            output_path = os.path.join(tmp, 'out')
            os.makedirs(output_path)
            with open(carrier, 'wb') as fh:
                fh.write(b'ID3' + b'\x00' * 32)

            zip_obj = Zip(carrier, ['pw1', 'pw2'], False)
            zip_obj.file_list = ['track.wav']
            zip_obj.compression_ratio_info = {'encrypted': False}
            zip_obj.covered = True

            unzipper = Unzipper(mock.MagicMock(), ProcessResourceManager(4))
            unzipper._run_single_unzip = mock.MagicMock(
                side_effect=[
                    (1, 'Wrong password'),
                    (1, 'Wrong password'),
                    (0, ''),
                ],
            )

            self.assertTrue(unzipper.single_threaded_unzip(zip_obj, output_path))
            self.assertEqual(unzipper._run_single_unzip.call_count, 3)
            self.assertEqual(
                [call.args[2] for call in unzipper._run_single_unzip.call_args_list],
                ['', 'pw1', 'pw2'],
            )

    def test_load_namelist_rejects_7z_list_only_password(self):
        from unzip_process_pool import ProcessResourceManager
        from unzipper import Unzipper

        with tempfile.TemporaryDirectory() as tmp:
            outer_path = os.path.join(tmp, '01646431.7z')
            with open(outer_path, 'wb') as fh:
                fh.write(b'7z\xbc\xaf\x27\x1c' + b'\x00' * 16)

            zip_obj = Zip(outer_path, ['RJ01646431', 'yisiki'], False)
            unzipper = Unzipper(mock.MagicMock(), ProcessResourceManager(4))
            unzipper.driver.probe_content_encrypted_single_block = mock.MagicMock(
                return_value={'content_encrypted_solid': False},
            )
            unzipper.driver.get_namelist = mock.MagicMock(
                side_effect=[
                    (['RJ01646431.zip'], {'encrypted': True}),
                    (['RJ01646431.zip'], {'encrypted': True}),
                ],
            )
            unzipper.driver.test_archive = mock.MagicMock(
                side_effect=[(False, 'Wrong password'), (True, '')],
            )

            self.assertTrue(unzipper.load_namelist(zip_obj))
            self.assertEqual(zip_obj.verified_password(), 'yisiki')

    def test_load_namelist_skips_library_for_content_encrypted_solid_7z(self):
        from unzip_process_pool import ProcessResourceManager
        from unzipper import Unzipper

        with tempfile.TemporaryDirectory() as tmp:
            outer_path = os.path.join(tmp, '01646431.7z')
            with open(outer_path, 'wb') as fh:
                fh.write(b'7z\xbc\xaf\x27\x1c' + b'\x00' * 16)

            zip_obj = Zip(outer_path, ['library_pw1', 'library_pw2'], False)
            unzipper = Unzipper(mock.MagicMock(), ProcessResourceManager(4))
            unzipper.driver.probe_content_encrypted_single_block = mock.MagicMock(
                return_value={'content_encrypted_solid': True},
            )
            unzipper.driver.get_namelist = mock.MagicMock(
                return_value=([], {'encrypted': True}),
            )
            unzipper.driver.test_archive = mock.MagicMock()

            self.assertFalse(unzipper.load_namelist(zip_obj))
            self.assertTrue(zip_obj.requires_manual_password())
            unzipper.driver.get_namelist.assert_not_called()

            zip_obj.set_note('yisiki')
            unzipper.driver.get_namelist = mock.MagicMock(
                return_value=(['RJ01646431.zip'], {'encrypted': True}),
            )
            unzipper.driver.test_archive = mock.MagicMock(return_value=(True, ''))

            self.assertTrue(unzipper.load_namelist(zip_obj))
            self.assertEqual(zip_obj.verified_password(), 'yisiki')
            unzipper.driver.get_namelist.assert_called_once()
            self.assertEqual(
                unzipper.driver.get_namelist.call_args.kwargs.get('password'), 'yisiki',
            )

    def test_format_manual_7z_status_detail(self):
        probe = {
            'listable_without_password': True,
            'blocks': 1,
            'store_encrypted': True,
            'file_size': 3775660497,
        }
        detail = Zip.format_manual_7z_status_detail(r'D:\下载\RJ01620216.7z', probe)
        self.assertIn('RJ01620216.7z', detail)
        self.assertIn('仅内容加密', detail)
        self.assertIn('单Block', detail)
        self.assertIn('Copy存储', detail)
        self.assertIn('3.5GB', detail)
        self.assertIn('双击任务填密码', detail)

    def test_requeue_skips_manual_7z_until_note_is_set(self):
        import task_runner
        from timeline import Archive, Timeline

        task_runner.timelines.clear()
        task_runner.passwords = []
        zip_obj = Zip(r'D:\work\RJ01620216.7z', [], False)
        zip_obj.manual_password_only = True
        zip_obj.compression_ratio_info['manual_password_only'] = True
        timeline = Timeline(Archive(r'D:\work\RJ01620216.7z'), 'unzip_failed', zip_obj)
        task_runner.timelines.append(timeline)

        self.assertFalse(task_runner.requeue_unzip_failure(timeline))
        self.assertEqual(timeline.get_current_record().ops, 'unzip_failed')

        zip_obj.set_note('0721')
        self.assertTrue(task_runner.requeue_unzip_failure(timeline))
        self.assertEqual(timeline.get_current_record().ops, 'find_zip')
        self.assertEqual(zip_obj.note, '0721')


if __name__ == '__main__':

    unittest.main()

