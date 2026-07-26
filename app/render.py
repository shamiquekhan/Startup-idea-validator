"""Markdown → PDF rendering via markdown + fpdf2."""

import markdown
from pathlib import Path


_UBUNTU = "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"
_UBUNTU_BOLD = "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"
_UBUNTU_ITALIC = "/usr/share/fonts/truetype/ubuntu/Ubuntu-RI.ttf"
_UBUNTU_MONO = "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf"


def markdown_to_pdf(md_text: str, output_path: str | Path | None = None) -> bytes:
    from fpdf import FPDF

    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    styled = f"""<style>
        h1 {{ font-size: 16pt; margin: 8px 0; }}
        h2 {{ font-size: 13pt; margin: 6px 0; }}
        h3 {{ font-size: 11pt; margin: 5px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 5px 0; }}
        th, td {{ border: 1px solid #666; padding: 3px 5px; }}
        th {{ background: #ddd; }}
        blockquote {{ margin: 5px 0; padding: 3px 8px; }}
        code {{ background: #eee; padding: 1px 3px; }}
    </style>{html}"""

    pdf = FPDF()
    pdf.add_font("Ubuntu", "", _UBUNTU, uni=True)
    pdf.add_font("Ubuntu", "B", _UBUNTU_BOLD, uni=True)
    pdf.add_font("Ubuntu", "I", _UBUNTU_ITALIC, uni=True)
    pdf.add_font("UbuntuMono", "", _UBUNTU_MONO, uni=True)
    pdf.set_font("Ubuntu", size=10)
    pdf.add_page()
    pdf.write_html(styled)
    pdf_bytes = bytes(pdf.output())

    if output_path:
        Path(output_path).write_bytes(pdf_bytes)

    return pdf_bytes