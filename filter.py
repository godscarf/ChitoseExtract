import os
import re

import task_runner
from filter_rules import pattern_allows_directory_match

# 无损主音源：有这些时才允许按规则删除 MP3（避免误删 MP3-only 作品）
_LOSSLESS_PATTERN = re.compile(r'\.(?:WAV|FLAC|AIF|AIFF)\b', re.IGNORECASE)
_MP3_PATTERN = re.compile(r'\.MP3$', re.IGNORECASE)


def _compile_filter_patterns(keyword_list: list, logger) -> list[tuple[re.Pattern, str, bool]]:
    compiled: list[tuple[re.Pattern, str, bool]] = []
    for key in keyword_list:
        if not key:
            continue
        try:
            compiled.append((
                re.compile(key, re.IGNORECASE),
                key,
                pattern_allows_directory_match(key),
            ))
        except re.error as err:
            if logger:
                logger.warning(f'过滤规则正则无效，已跳过：[ {key} ] {err}')
    return compiled


class Filter():
    def __init__(self, keyword_list: list, filter_dir: bool, logger):
        self.keyword_patterns = _compile_filter_patterns(keyword_list, logger)
        self.filter_dir = filter_dir
        self.logger = logger

    def _matches_filter(self, path: str, *, for_directory: bool = False) -> str | None:
        for pattern, source, allows_dir in self.keyword_patterns:
            if for_directory and not allows_dir:
                continue
            if pattern.search(path):
                return source
        return None

    @staticmethod
    def _scope_has_lossless(names: list[str]) -> bool:
        return any(_LOSSLESS_PATTERN.search(name) for name in names)

    @staticmethod
    def _looks_like_mp3(path: str) -> bool:
        return bool(_MP3_PATTERN.search(path))

    def _skip_mp3_without_lossless(self, target_path: str, has_lossless: bool) -> bool:
        """作品目录内若无 WAV/FLAC 等无损音源，则跳过对 MP3 的过滤。"""
        return not has_lossless and self._looks_like_mp3(target_path)

    def pre_filter(self, file_list: list):
        has_lossless = self._scope_has_lossless(file_list)
        hit = False
        result_list = []
        for file in file_list:
            if self._skip_mp3_without_lossless(file, has_lossless):
                result_list.append(file)
                continue
            matched = self._matches_filter(file)
            if matched:
                self.logger.info('跳过文件: [ {} ] 命中关键词： [ {} ]'.format(file, matched))
                hit = True
                continue
            result_list.append(file)
        if not hit:
            return None
        return result_list

    def post_filter(self, path):
        if not path or not os.path.exists(path):
            if path:
                self.logger.warning(f'过滤路径不存在，已跳过（不做模糊匹配）：[{path}]')
            return False

        # 先扫一遍判断是否有无损主音源；正式删除用实时 walk，
        # 删掉文件夹后从 dirs 剔除，避免对已移走的子路径再删一次误报失败。
        has_lossless = any(
            _LOSSLESS_PATTERN.search(name)
            for root, dirs, files in os.walk(path)
            for name in list(files) + list(dirs)
        )
        hit = False
        for root, dirs, files in os.walk(path, topdown=True):
            if self.filter_dir:
                for dir_name in dirs[:]:
                    dir_path = os.path.join(root, dir_name)
                    if self._skip_mp3_without_lossless(dir_path, has_lossless):
                        continue
                    matched = self._matches_filter(dir_path, for_directory=True)
                    if matched:
                        task_runner.delete_file(dir_path)
                        self.logger.info('过滤文件夹: [ {} ] 命中关键词： [ {} ]'.format(dir_path, matched))
                        hit = True
                        dirs.remove(dir_name)
            for file in files:
                file_path = os.path.join(root, file)
                if not os.path.exists(file_path):
                    continue
                if self._skip_mp3_without_lossless(file_path, has_lossless):
                    continue
                matched = self._matches_filter(file_path)
                if matched:
                    task_runner.delete_file(file_path)
                    self.logger.info('过滤文件: [ {} ] 命中关键词： [ {} ]'.format(file_path, matched))
                    hit = True
        return hit
