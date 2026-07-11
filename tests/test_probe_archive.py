"""probe_archive 识别逻辑单元测试。"""

import os
import shutil
import struct
import tempfile
import unittest
import zipfile

from file_ops import probe_archive


def _write_min_pe(path: str, extra: bytes = b'') -> None:
    pe_offset = 128
    header = bytearray(pe_offset + 64)
    header[0:2] = b'MZ'
    struct.pack_into('<I', header, 0x3C, pe_offset)
    header[pe_offset:pe_offset + 4] = b'PE\x00\x00'
    with open(path, 'wb') as f:
        f.write(header)
        if extra:
            f.write(extra)


class ProbeArchiveApkTest(unittest.TestCase):

    def _tmpdir(self) -> str:
        return tempfile.mkdtemp(prefix='probe_apk_')

    def _write_real_apk(self, path: str):
        with zipfile.ZipFile(path, 'w') as zf:
            zf.writestr('AndroidManifest.xml', b'<manifest/>')
            zf.writestr('classes.dex', b'dex')
            zf.writestr('META-INF/CERT.SF', b'sig')

    def _write_zip_disguised_apk(self, path: str):
        with zipfile.ZipFile(path, 'w') as zf:
            zf.writestr('data/chapter1.txt', b'hello')
            zf.writestr('nested/file.bin', b'\x00' * 64)

    def test_real_apk_not_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'app.apk')
            self._write_real_apk(path)
            probe = probe_archive(path, nested=False)
            self.assertFalse(probe.is_candidate)
            probe_nested = probe_archive(path, nested=True)
            self.assertFalse(probe_nested.is_candidate)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_zip_renamed_to_apk_is_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'game.apk')
            self._write_zip_disguised_apk(path)
            probe = probe_archive(path, nested=False)
            self.assertTrue(probe.is_candidate)
            self.assertEqual(probe.format_type, 'zip')
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_7z_renamed_to_apk_is_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'secret.apk')
            with open(path, 'wb') as f:
                f.write(b'7z\xbc\xaf\x27\x1c' + b'\x00' * 256)
            probe = probe_archive(path, nested=False)
            self.assertTrue(probe.is_candidate)
            self.assertEqual(probe.format_type, '7z')
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_rar_renamed_to_apk_is_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'pack.apk')
            with open(path, 'wb') as f:
                f.write(b'Rar!\x1a\x07\x00' + b'\x00' * 256)
            probe = probe_archive(path, nested=False)
            self.assertTrue(probe.is_candidate)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class ProbeArchiveExeTest(unittest.TestCase):

    def _tmpdir(self) -> str:
        return tempfile.mkdtemp(prefix='probe_exe_')

    def test_real_pe_exe_not_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'laowang.exe')
            _write_min_pe(path)
            self.assertFalse(probe_archive(path, nested=False).is_candidate)
            self.assertFalse(probe_archive(path, nested=True).is_candidate)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_7z_renamed_to_exe_is_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'game.exe')
            with open(path, 'wb') as f:
                f.write(b'7z\xbc\xaf\x27\x1c' + b'\x00' * 256)
            probe = probe_archive(path, nested=False)
            self.assertTrue(probe.is_candidate)
            self.assertEqual(probe.format_type, '7z')
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_pe_with_sfx_tail_is_candidate(self):
        d = self._tmpdir()
        try:
            path = os.path.join(d, 'sfx.exe')
            _write_min_pe(path, b'7z\xbc\xaf\x27\x1c' + b'\x00' * 256)
            probe = probe_archive(path, nested=False)
            self.assertTrue(probe.is_candidate)
            self.assertTrue(probe.covered)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
