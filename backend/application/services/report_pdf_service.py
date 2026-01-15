from __future__ import annotations

import os
import html
from io import BytesIO
from typing import Any, Dict, Optional


def _h(v: Any) -> str:
    if v is None:
        return ''
    return html.escape(str(v))


def _fmt_num(v: Any, digits: int = 4) -> str:
    try:
        f = float(v)
        return f"{f:.{digits}f}"
    except Exception:
        return '-'


def _fmt_pct(v: Any, digits: int = 2) -> str:
    try:
        f = float(v)
        return f"{f * 100:.{digits}f}%"
    except Exception:
        return '-'


def _pick_font_path() -> Optional[str]:
    """尽量找到可用的中文字体，避免 PDF 乱码。

    xhtml2pdf/reportlab 在没有中文字体时会乱码/方框。
    这里优先使用 macOS 常见字体；若不存在则返回 None。
    """
    candidates = [
        # macOS
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
        '/Library/Fonts/Arial Unicode MS.ttf',
        # 常见 Linux
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for p in candidates:
        try:
            if p and os.path.exists(p):
                return p
        except Exception:
            continue
    return None


def build_report_html(report: Dict[str, Any]) -> str:
    meta = report.get('meta') or {}
    file_meta = (meta.get('file') or {}) if isinstance(meta, dict) else {}
    time_meta = (meta.get('time') or {}) if isinstance(meta, dict) else {}
    summary = report.get('summary') or {}

    sections = report.get('sections')
    if not isinstance(sections, list):
        sections = []

    # 抽取关键 section
    sec_network = next((s for s in sections if (s or {}).get('id') == 'network_overview'), None)
    sec_key = next((s for s in sections if (s or {}).get('id') == 'key_nodes_and_propagation'), None)
    sec_gov = next((s for s in sections if (s or {}).get('id') == 'governance_actions'), None)

    # 网络指标
    net_metrics = ((sec_network or {}).get('data') or {}).get('metrics') or {}
    lccm = (net_metrics.get('largest_component_metrics') or {}) if isinstance(net_metrics, dict) else {}

    # Top nodes
    top_nodes = ((sec_key or {}).get('data') or {}).get('top_nodes')
    if not isinstance(top_nodes, list):
        top_nodes = []

    # 治理 actions
    gov_data = ((sec_gov or {}).get('data') or {})
    actions = gov_data.get('actions')
    if not isinstance(actions, list):
        actions = []

    font_path = _pick_font_path()
    font_face = ''
    if font_path:
        font_face = f"""
        @font-face {{
          font-family: ReportFont;
          src: url('file://{font_path}');
        }}
        """

    title = f"智能报告 - 任务 {meta.get('task_id') or ''}"

    # Top 节点表格
    top_rows = []
    for r in top_nodes:
        if not isinstance(r, dict):
            continue
        top_rows.append(
            f"<tr>"
            f"<td>{_h(r.get('rank'))}</td>"
            f"<td class='mono'>{_h(r.get('node_id'))}</td>"
            f"<td>{_h(_fmt_num(r.get('score'), 4))}</td>"
            f"<td>{_h(r.get('degree') if r.get('degree') is not None else '-')}</td>"
            f"<td class='mono'>{_h(', '.join((r.get('neighbors_sample') or [])[:10]))}</td>"
            f"</tr>"
        )
    top_table = """
    <table>
      <thead>
        <tr><th style='width:56px'>序号</th><th>节点</th><th style='width:90px'>分数</th><th style='width:70px'>度</th><th>邻居采样</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    """.format(rows='\n'.join(top_rows) if top_rows else "<tr><td colspan='5'>暂无数据</td></tr>")

    # 治理建议
    def _p_rank(p: Any) -> int:
        pp = str(p or '').upper().strip()
        if pp == 'P0':
            return 0
        if pp == 'P1':
            return 1
        if pp == 'P2':
            return 2
        return 9

    actions_sorted = sorted([a for a in actions if isinstance(a, dict)], key=lambda x: (_p_rank(x.get('priority')),))

    action_blocks = []
    for a in actions_sorted:
        pri = _h(a.get('priority') or '')
        title2 = _h(a.get('title') or '处置建议')
        reason = _h(a.get('reason') or '')

        targets = a.get('targets') or {}
        nodes = targets.get('nodes') if isinstance(targets, dict) else None
        scope = targets.get('scope') if isinstance(targets, dict) else None
        component = targets.get('component') if isinstance(targets, dict) else None

        ops = a.get('operations') if isinstance(a.get('operations'), list) else []
        op_items = []
        for op in ops:
            if not isinstance(op, dict):
                continue
            op_items.append(f"<li><span class='op-type'>{_h(op.get('type') or 'action')}</span><span class='op-desc'>{_h(op.get('desc') or '')}</span></li>")

        action_blocks.append(
            """
            <div class='action'>
              <div class='action-title-row'>
                <span class='badge badge-{pri_lc}'>{pri}</span>
                <span class='action-title'>{title}</span>
              </div>
              {reason_block}
              <div class='action-meta'>
                {nodes_block}
                {scope_block}
                {comp_block}
              </div>
              {ops_block}
            </div>
            """.format(
                pri_lc=str(a.get('priority') or '').lower(),
                pri=pri,
                title=title2,
                reason_block=(f"<div class='action-reason'>原因：{reason}</div>" if reason else ""),
                nodes_block=(f"<div><b>目标节点：</b><span class='mono'>{_h(', '.join([str(x) for x in nodes]))}</span></div>" if isinstance(nodes, list) and nodes else ""),
                scope_block=(f"<div><b>作用范围：</b>{_h(scope)}</div>" if scope else ""),
                comp_block=(f"<div><b>目标组件：</b>{_h(component)}</div>" if component else ""),
                ops_block=(
                    "<div class='ops'><b>建议动作：</b><ul>" + "".join(op_items) + "</ul></div>" if op_items else ""
                ),
            )
        )

    gov_html = """
    <div class='section'>
      <div class='section-title'>治理建议与处置方案</div>
      {blocks}
    </div>
    """.format(blocks='\n'.join(action_blocks) if action_blocks else "<div class='muted'>暂无治理建议</div>")

    html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8' />
  <title>{_h(title)}</title>
  <style>
    {font_face}
    body {{
      font-family: {'ReportFont' if font_path else '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif'};
      color: #111827;
      font-size: 12px;
      line-height: 1.55;
    }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace; }}
    .header {{ margin-bottom: 12px; }}
    .h1 {{ font-size: 18px; font-weight: 800; margin: 0 0 6px 0; }}
    .sub {{ color: #6b7280; font-size: 11px; }}

    .kv {{ margin: 10px 0 14px 0; }}
    .kv table td {{ border: none; padding: 2px 0; }}
    .kv b {{ color: #374151; }}

    .section {{ margin-top: 14px; }}
    .section-title {{ font-size: 14px; font-weight: 800; margin: 0 0 8px 0; }}

    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f3f4f6; font-weight: 700; }}

    .action {{ border: 1px solid #e5e7eb; padding: 10px; margin: 8px 0; }}
    .action-title-row {{ margin-bottom: 6px; }}
    .action-title {{ font-weight: 800; }}
    .action-reason {{ margin: 6px 0; color: #4b5563; }}

    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-weight: 800; font-size: 11px; margin-right: 8px; }}
    .badge-p0 {{ background: #fee2e2; color: #b91c1c; }}
    .badge-p1 {{ background: #fffbeb; color: #b45309; }}
    .badge-p2 {{ background: #e5e7eb; color: #374151; }}

    .ops ul {{ margin: 6px 0 0 18px; padding: 0; }}
    .ops li {{ margin: 4px 0; }}
    .op-type {{ display: inline-block; min-width: 88px; font-weight: 800; }}
    .op-desc {{ color: #374151; }}

    .muted {{ color: #6b7280; }}

    @page {{ size: A4; margin: 14mm 12mm; }}
  </style>
</head>
<body>
  <div class='header'>
    <div class='h1'>智能报告</div>
    <div class='sub'>任务：{_h(meta.get('task_id') or '')}　文件：{_h(file_meta.get('original_name') or '')}</div>
    <div class='sub'>算法：{_h((meta.get('algo') or {{}}).get('name') or meta.get('algorithm_key') or '')}　生成时间：{_h(time_meta.get('ended_at') or '')}</div>
  </div>

  <div class='section'>
    <div class='section-title'>网络概览</div>
    <div class='kv'>
      <table>
        <tr><td><b>节点数：</b>{_h(net_metrics.get('nodes'))}</td><td><b>边数：</b>{_h(net_metrics.get('edges'))}</td></tr>
        <tr><td><b>平均度：</b>{_h(_fmt_num(net_metrics.get('avg_degree'), 4))}</td><td><b>密度：</b>{_h(_fmt_num(net_metrics.get('density'), 6))}</td></tr>
        <tr><td><b>连通分量：</b>{_h(net_metrics.get('components'))}</td><td><b>最大分量占比：</b>{_h(_fmt_pct(net_metrics.get('largest_component_ratio')))}</td></tr>
        <tr><td><b>平均路径长度(最大分量)：</b>{_h(_fmt_num(lccm.get('avg_path_length'), 4))}</td><td><b>平均聚类系数(最大分量)：</b>{_h(_fmt_num(lccm.get('avg_clustering'), 4))}</td></tr>
      </table>
    </div>
  </div>

  <div class='section'>
    <div class='section-title'>关键节点（Top-10）</div>
    {top_table}
  </div>

  {gov_html}

  <div class='section muted'>
    <div>备注：PDF为后端生成的结构化报告，图可视化不包含在内。</div>
  </div>
</body>
</html>"""

    return html_doc


def render_pdf_from_html(html_string: str) -> bytes:
    """使用 xhtml2pdf 将 HTML 转为 PDF 字节流。

    说明：xhtml2pdf 底层基于 reportlab。
    - 直接用 TTF/TTC 的 @font-face 在 xhtml2pdf 中不稳定
    - 默认字体不支持中文会乱码/方块

    这里采用更稳的方案：注册 reportlab 的 CIDFont（如 STSong-Light），并在 HTML 中强制使用该字体。
    """
    from xhtml2pdf import pisa

    # 1) 尝试注册 CIDFont（最稳的中文方案）
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        # 内置 CID 字体名（常见：STSong-Light 支持简体中文）
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

        # 强制 HTML 使用该字体（xhtml2pdf 更容易识别 font-family）
        html_string = html_string.replace(
            "font-family:",
            "font-family: STSong-Light,",
            1,
        )
    except Exception:
        # 2) 兜底：尝试注册本机字体（可能仍乱码，但不阻断）
        font_path = _pick_font_path()
        if font_path:
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont('ReportFont', font_path))
            except Exception:
                pass

    bio = BytesIO()
    result = pisa.CreatePDF(
        src=html_string,
        dest=bio,
        encoding='utf-8',
    )
    if result.err:
        raise RuntimeError('PDF渲染失败')
    return bio.getvalue()

