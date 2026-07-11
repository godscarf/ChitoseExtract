# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['app_paths', 'audio_convert', 'audio_tagger', 'mutagen', 'mutagen.flac', 'mutagen.id3', 'mutagen.mp3', 'ui_scaling', 'peewee', 'pydantic', 'ruamel.yaml', 'typing_extensions', 'windnd', 'win32api', 'win32con', 'win32pdh', 'pywintypes', 'PIL', 'PIL.Image', 'lxml', 'lxml.etree', 'pyquery', 'scraper.cached_scraper', 'scraper.db', 'scraper.dlsite', 'scraper.locale', 'scraper.scraper', 'scraper.translation', 'scraper.work_metadata', 'scraper.langs.en_us', 'scraper.langs.ja_jp', 'scraper.langs.ko_kr', 'scraper.langs.zh_cn', 'scraper.langs.zh_tw']
hiddenimports += collect_submodules('scraper')


a = Analysis(
    ['main.py'],
    pathex=['E:\\tool\\ChitoseExtract v1.0\\源码'],
    binaries=[],
    datas=[('E:\\tool\\ChitoseExtract v1.0\\源码\\assets', 'assets'), ('E:\\tool\\ChitoseExtract v1.0\\源码\\config.yaml', '.'), ('E:\\tool\\ChitoseExtract v1.0\\源码\\password.txt', '.'), ('E:\\tool\\ChitoseExtract v1.0\\源码\\7zip', '7zip'), ('E:\\tool\\ChitoseExtract v1.0\\源码\\flac', 'flac'), ('E:\\tool\\ChitoseExtract v1.0\\源码\\ffmpeg-minimal', 'ffmpeg-minimal')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ChitoseExtract',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['E:\\tool\\ChitoseExtract v1.0\\源码\\assets\\icon.ico'],
)
