"""命名模板字段：可勾选、可拖动排序的列表。"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

# 避免 template_field_list → gui → task_runner → ez_client 循环导入
_COLORS = {
    'surface': '#ffffff',
    'text': '#3d3530',
    'select': '#fff0f6',
    'surface_alt': '#faf6f1',
    'text_muted': '#8a7f75',
    'border': '#e8dcc8',
    'accent': '#d4567a',
}
_FONT_UI = ('Segoe UI', 10)
_FONT_SMALL = ('Segoe UI', 9)

# (占位符, 中文名)
TEMPLATE_FIELDS = [
    ('rjcode', 'RJ 号'),
    ('work_name', '作品名'),
    ('maker_id', '社团 RG 号'),
    ('maker_name', '社团名'),
    ('series_name', '系列名'),
    ('release_date', '发售日'),
    ('cv_list_str', '声优列表'),
    ('tags_list_str', '标签列表'),
    ('age_cat', '年龄分级'),
]

_BRACKET_FIELDS = frozenset({'rjcode', 'maker_id', 'maker_name', 'series_name'})
_FIELD_LABELS = {key: label for key, label in TEMPLATE_FIELDS}
_FIELD_KEYS = [key for key, _ in TEMPLATE_FIELDS]
_DEFAULT_TEMPLATE = '[rjcode][maker_name] work_name cv_list_str'
CV_BRACKET_LEFT = '(CV '
CV_BRACKET_RIGHT = ')'


def parse_cv_brackets_enabled(renamer_config: dict | None) -> bool:
    if not renamer_config:
        return True
    left = str(renamer_config.get('renamer_cv_list_left', CV_BRACKET_LEFT) or '')
    right = str(renamer_config.get('renamer_cv_list_right', CV_BRACKET_RIGHT) or '')
    return bool(left.strip() or right.strip())


def cv_bracket_values(enabled: bool) -> tuple[str, str]:
    if enabled:
        return CV_BRACKET_LEFT, CV_BRACKET_RIGHT
    return '', ''

_TEMPLATE_TOKEN_RE = re.compile(
    r'\[(rjcode|maker_id|maker_name|series_name)\]|(?<![a-z_])'
    r'(work_name|series_name|release_date|cv_list_str|tags_list_str|age_cat)(?![a-z_])'
)


def parse_template_items(template: str) -> list[tuple[str, bool]]:
    """解析 renamer_template → [(key, enabled), ...]，顺序与模板一致。"""
    seen: set[str] = set()
    items: list[tuple[str, bool]] = []

    for match in _TEMPLATE_TOKEN_RE.finditer(template or ''):
        key = match.group(1) or match.group(2)
        if key in seen:
            continue
        seen.add(key)
        items.append((key, True))

    if not items:
        return parse_template_items(_DEFAULT_TEMPLATE)

    for key in _FIELD_KEYS:
        if key not in seen:
            items.append((key, False))
    return items


def build_template_string(items: list[tuple[str, bool]]) -> str:
    """按列表顺序与勾选状态生成 renamer_template。"""
    parts: list[str] = []
    for key, enabled in items:
        if not enabled:
            continue
        token = f'[{key}]' if key in _BRACKET_FIELDS else key
        if not parts:
            parts.append(token)
            continue
        if token.startswith('['):
            if parts[-1].endswith(']'):
                parts[-1] += token
            else:
                parts.append(' ' + token)
        else:
            parts.append(' ' + token)
    return ''.join(parts)


def template_includes_rjcode(template: str) -> bool:
    return any(key == 'rjcode' and enabled for key, enabled in parse_template_items(template))


def build_rename_template(template: str) -> str:
    """重命名执行用模板：用户未启用 RJ 号时临时 prepend [rjcode]。"""
    items = parse_template_items(template)
    if template_includes_rjcode(template):
        return build_template_string(items)
    enabled_items = [(key, enabled) for key, enabled in items if enabled]
    return build_template_string([('rjcode', True)] + enabled_items)


def resolve_rename_template(user_template: str) -> tuple[str, bool]:
    """返回 (执行用模板, 重命名后是否移除 RJ 号)。"""
    if template_includes_rjcode(user_template):
        return build_template_string(parse_template_items(user_template)), False
    return build_rename_template(user_template), True


def finalize_folder_name(user_template: str, compiled_name: str) -> str:
    """按用户对 RJ 号的启用状态，得到最终展示的文件夹名。"""
    if template_includes_rjcode(user_template):
        return compiled_name
    from file_ops import strip_rj_from_basename
    return strip_rj_from_basename(compiled_name)

def _settings_checkbutton(parent, text: str, variable: tk.Variable) -> tk.Checkbutton:
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        bg=_COLORS['surface'],
        fg=_COLORS['text'],
        activebackground=_COLORS['select'],
        activeforeground=_COLORS['text'],
        selectcolor=_COLORS['surface'],
        highlightthickness=0,
        bd=0,
        anchor='w',
        font=_FONT_UI,
        cursor='hand2',
    )


class TemplateFieldList(tk.Frame):
    """命名模板字段列表：拖动 ☰ 把手排序，勾选启用。"""

    def __init__(self, parent, *, on_change=None, **kwargs):
        kwargs.setdefault('bg', _COLORS['surface'])
        super().__init__(parent, **kwargs)
        self._on_change = on_change
        self._rows: list[dict] = []
        self._drag_key: str | None = None
        self._drop_index: int | None = None
        self._cv_brackets = tk.BooleanVar(value=True)
        self._cv_brackets.trace_add('write', lambda *_: self._notify_change())

        self.columnconfigure(0, weight=1)

    def set_cv_brackets(self, enabled: bool):
        self._cv_brackets.set(enabled)

    def get_cv_brackets(self) -> bool:
        return bool(self._cv_brackets.get())

    def get_cv_bracket_values(self) -> tuple[str, str]:
        return cv_bracket_values(self.get_cv_brackets())

    def set_items(self, items: list[tuple[str, bool]]):
        for row in self._rows:
            row['frame'].destroy()
        self._rows.clear()

        for key, enabled in items:
            if key not in _FIELD_LABELS:
                continue
            self._append_row(key, enabled)
        self._relayout()

    def get_items(self) -> list[tuple[str, bool]]:
        return [(row['key'], bool(row['enabled'].get())) for row in self._rows]

    def get_enabled_keys(self) -> set[str]:
        return {key for key, enabled in self.get_items() if enabled}

    def _append_row(self, key: str, enabled: bool):
        frame = tk.Frame(
            self, bg=_COLORS['surface'],
            highlightbackground=_COLORS['border'], highlightthickness=1,
        )

        grip = tk.Label(
            frame, text='☰', bg=_COLORS['surface_alt'], fg=_COLORS['text_muted'],
            font=_FONT_UI, width=2, cursor='fleur',
        )
        grip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        enabled_var = tk.BooleanVar(value=enabled)
        _settings_checkbutton(frame, _FIELD_LABELS[key], enabled_var).pack(
            side=tk.LEFT, padx=(0, 8), pady=4,
        )

        if key == 'cv_list_str':
            _settings_checkbutton(frame, '显示括号', self._cv_brackets).pack(
                side=tk.LEFT, padx=(0, 8), pady=4,
            )

        tk.Label(
            frame, text=key, bg=_COLORS['surface'], fg=_COLORS['text_muted'],
            font=_FONT_SMALL,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        enabled_var.trace_add('write', lambda *_: self._notify_change())

        grip.bind('<Button-1>', lambda e, k=key: self._start_drag(k, e))
        grip.bind('<Double-Button-1>', lambda e: 'break')

        self._rows.append({
            'key': key,
            'enabled': enabled_var,
            'frame': frame,
            'grip': grip,
        })

    def _relayout(self):
        self._clear_drop_marks()
        for index, row in enumerate(self._rows):
            row['frame'].grid(row=index, column=0, sticky='ew', pady=2)
        self.columnconfigure(0, weight=1)

    def _clear_drop_marks(self):
        for row in self._rows:
            row['frame'].configure(
                highlightbackground=_COLORS['border'], highlightthickness=1,
            )

    def _row_index(self, key: str) -> int:
        for index, row in enumerate(self._rows):
            if row['key'] == key:
                return index
        return -1

    def _index_at_y(self, y_root: int) -> int:
        for index, row in enumerate(self._rows):
            frame = row['frame']
            top = frame.winfo_rooty()
            bottom = top + frame.winfo_height()
            if y_root < top + (bottom - top) // 2:
                return index
        return len(self._rows) - 1

    def _start_drag(self, key: str, _event):
        self._drag_key = key
        self._drop_index = self._row_index(key)
        self._highlight(key, True)
        top = self.winfo_toplevel()
        top.bind('<B1-Motion>', self._on_drag, add='+')
        top.bind('<ButtonRelease-1>', self._end_drag, add='+')

    def _on_drag(self, event):
        if self._drag_key is None:
            return
        target = self._index_at_y(event.y_root)
        if target < 0:
            return
        if target != self._drop_index:
            self._clear_drop_marks()
            self._highlight(self._drag_key, True)
            self._rows[target]['frame'].configure(
                highlightbackground=_COLORS['accent'], highlightthickness=2,
            )
            self._drop_index = target

    def _end_drag(self, _event):
        top = self.winfo_toplevel()
        top.unbind('<B1-Motion>')
        top.unbind('<ButtonRelease-1>')

        if self._drag_key is not None and self._drop_index is not None:
            from_index = self._row_index(self._drag_key)
            to_index = self._drop_index
            if from_index >= 0 and to_index >= 0 and from_index != to_index:
                row = self._rows.pop(from_index)
                self._rows.insert(to_index, row)
                self._relayout()

        if self._drag_key is not None:
            self._highlight(self._drag_key, False)
        self._drag_key = None
        self._drop_index = None
        self._clear_drop_marks()
        self._notify_change()

    def _highlight(self, key: str, active: bool):
        for row in self._rows:
            if row['key'] == key:
                bg = _COLORS['select'] if active else _COLORS['surface']
                row['frame'].configure(bg=bg)
                row['grip'].configure(bg=_COLORS['select'] if active else _COLORS['surface_alt'])
                break

    def _notify_change(self):
        if self._on_change:
            self._on_change()
