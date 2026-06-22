"""
doc/*.md → doc/*.html + doc/index.html 생성

마크다운은 python-markdown 으로 변환하고,
```mermaid 코드블록은 원문 그대로 두어 Mermaid.js(CDN)가 렌더링한다.
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown

HERE = Path(__file__).parent
DOCS = [
    ("PRD.md", "PRD.html", "PRD — 제품 요구사항"),
    ("IA.md", "IA.html", "IA — 정보 구조"),
    ("ERD.md", "ERD.html", "ERD — 데이터 모델"),
]

# ─ Mermaid 코드블록 보존용 토큰화 ─────────────────────────────────────────────
MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def extract_mermaid(md_text: str) -> tuple[str, list[str]]:
    """```mermaid ... ``` 블록을 추출하고 자리표시자로 치환."""
    blocks: list[str] = []

    def _swap(m: re.Match[str]) -> str:
        blocks.append(m.group(1).strip())
        return f"@@MERMAID_{len(blocks) - 1}@@"

    return MERMAID_RE.sub(_swap, md_text), blocks


def restore_mermaid(html: str, blocks: list[str]) -> str:
    for i, code in enumerate(blocks):
        placeholder = f"@@MERMAID_{i}@@"
        # 자리표시자가 <p>로 감싸진 경우도 함께 제거
        html = html.replace(
            f"<p>{placeholder}</p>",
            f'<div class="mermaid">{code}</div>',
        )
        html = html.replace(
            placeholder,
            f'<div class="mermaid">{code}</div>',
        )
    return html


HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --fg: #0f172a; --muted: #64748b; --border: #e2e8f0; --bg: #ffffff;
  --code-bg: #f8fafc; --primary: #2563eb; --accent: #f1f5f9;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 0; background: var(--bg); color: var(--fg);
  font-family: -apple-system, "Segoe UI", "Noto Sans KR", sans-serif;
  line-height: 1.65; font-size: 16px;
}}
.container {{ max-width: 880px; margin: 0 auto; padding: 48px 24px 80px; }}
header.docnav {{
  background: var(--accent); border-bottom: 1px solid var(--border);
  padding: 12px 24px; display: flex; gap: 16px; align-items: center;
  font-size: 0.9rem;
}}
header.docnav a {{ color: var(--primary); text-decoration: none; }}
header.docnav a:hover {{ text-decoration: underline; }}
header.docnav strong {{ color: var(--fg); }}
h1 {{ font-size: 2rem; margin: 0 0 8px; border-bottom: 2px solid var(--border); padding-bottom: 12px; }}
h2 {{ font-size: 1.45rem; margin: 40px 0 12px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
h3 {{ font-size: 1.1rem; margin: 28px 0 8px; }}
h4 {{ font-size: 1rem; margin: 20px 0 6px; }}
p {{ margin: 8px 0; }}
ul, ol {{ padding-left: 24px; }}
li {{ margin: 4px 0; }}
hr {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}
code {{ background: var(--code-bg); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
pre {{
  background: var(--code-bg); padding: 14px 16px; border-radius: 8px;
  overflow-x: auto; border: 1px solid var(--border);
}}
pre code {{ background: transparent; padding: 0; }}
blockquote {{
  border-left: 4px solid var(--primary); padding: 4px 16px;
  background: var(--accent); margin: 12px 0; color: var(--muted);
}}
table {{
  border-collapse: collapse; width: 100%; margin: 12px 0;
  font-size: 0.95em;
}}
th, td {{
  border: 1px solid var(--border); padding: 8px 12px; text-align: left;
  vertical-align: top;
}}
th {{ background: var(--accent); font-weight: 600; }}
a {{ color: var(--primary); }}
.mermaid {{
  background: #fff; border: 1px solid var(--border); border-radius: 8px;
  padding: 16px; margin: 16px 0; text-align: center;
}}
.meta {{ color: var(--muted); font-size: 0.9rem; }}
</style>
</head>
<body>
<header class="docnav">
  <strong>📚 meeting-minutes-automation / doc</strong>
  <a href="index.html">목차</a>
  <a href="PRD.html">PRD</a>
  <a href="IA.html">IA</a>
  <a href="ERD.html">ERD</a>
</header>
<div class="container">
{body}
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose' }});
</script>
</body>
</html>
"""


def render_doc(md_path: Path, title: str) -> str:
    raw = md_path.read_text(encoding="utf-8")
    stripped, blocks = extract_mermaid(raw)
    html_body = markdown.markdown(
        stripped,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )
    html_body = restore_mermaid(html_body, blocks)
    return HTML_TEMPLATE.format(title=title, body=html_body)


def render_index() -> str:
    body = """
<h1>📚 문서 목차 — AI 회의록 자동화</h1>
<p class="meta">meeting-minutes-automation · doc/</p>

<h2>설계 문서</h2>
<ul>
  <li><a href="PRD.html"><strong>PRD</strong></a> — 제품 요구사항 (목적·기능·비기능·로드맵)</li>
  <li><a href="IA.html"><strong>IA</strong></a> — 정보 구조 (사이트맵·플로우·컴포넌트 트리·API)</li>
  <li><a href="ERD.html"><strong>ERD</strong></a> — 데이터 모델 (엔티티·관계·데이터 흐름·보존 정책)</li>
</ul>

<h2>외부 리소스</h2>
<ul>
  <li>저장소: <a href="https://github.com/hongchae1009-crypto/meeting-minutes-automation">GitHub</a></li>
  <li>배포 URL: <a href="https://meeting-minutes-automation-r2yu.vercel.app">meeting-minutes-automation-r2yu.vercel.app</a></li>
  <li>백엔드 API: <a href="https://meeting-minutes-backend-hongchae.onrender.com">Render</a></li>
</ul>

<h2>버전</h2>
<p class="meta">v1.1 (2026-06-19) · Render+Vercel 배포 및 내보내기 기능 추가</p>
"""
    return HTML_TEMPLATE.format(title="문서 목차 — AI 회의록 자동화", body=body)


def main() -> None:
    for md_name, html_name, title in DOCS:
        md_path = HERE / md_name
        if not md_path.exists():
            print(f"[skip] {md_name} (없음)")
            continue
        html = render_doc(md_path, title)
        (HERE / html_name).write_text(html, encoding="utf-8")
        print(f"[ok]   {md_name} → {html_name}")

    (HERE / "index.html").write_text(render_index(), encoding="utf-8")
    print("[ok]   index.html")


if __name__ == "__main__":
    main()
