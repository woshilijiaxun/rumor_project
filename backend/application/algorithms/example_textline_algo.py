"""示例算法：按行读取文本，输出 {line_no: line_text}。

这是一个可运行的例子，后续你可以把真实算法实现放在类似文件中。
"""

from typing import Any, Dict

from .registry import ProgressCallback, IsCancelled


def run(abs_path: str, params: Dict[str, Any], progress_cb: ProgressCallback, is_cancelled: IsCancelled) -> Dict[str, Any]:
    max_lines = int((params or {}).get('max_lines', 5000))
    truncate_len = int((params or {}).get('truncate_len', 128))

    out: Dict[str, Any] = {}
    progress_cb(5, 'loading', '读取输入数据')

    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f):
            if is_cancelled():
                return {}
            if idx >= max_lines:
                break

            text = (line or '').strip()
            if not text:
                continue

            out[str(idx + 1)] = text[:truncate_len]

            if (idx + 1) % 200 == 0:
                p = 10 + int(min(80, (idx + 1) / max_lines * 80))
                progress_cb(p, 'computing', f'处理中：已处理 {idx + 1} 行')

    progress_cb(95, 'finalizing', '整理结果')
    return out

