"""Render the Markdown Testing Plan as a reproducible monochrome PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    LongTable,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "docs" / "testing_plan.md"
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "pdf" / "Iteration2_Testing_Plan.pdf"
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 16 * mm
RIGHT_MARGIN = 16 * mm
TOP_MARGIN = 18 * mm
BOTTOM_MARGIN = 16 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


def normalise_text(value: str) -> str:
    """Replace typographic punctuation with reliable monochrome PDF glyphs."""

    translations = str.maketrans(
        {
            "\u2010": "-",
            "\u2011": "-",
            "\u2012": "-",
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2026": "...",
            "\u00b7": "-",
        }
    )
    return value.translate(translations)


def inline_markup(value: str) -> str:
    """Convert the small Markdown inline subset used by the plan to ReportLab XML."""

    value = normalise_text(value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", value)
    value = re.sub(r"<(https?://[^>]+)>", r"\1", value)
    value = html.escape(value, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(
        r"`([^`]+)`",
        lambda match: f'<font name="Courier">{match.group(1)}</font>',
        value,
    )
    return value


def build_styles() -> dict[str, ParagraphStyle]:
    """Create a black-and-white style system sized for an A4 verification plan."""

    sample = getSampleStyleSheet()
    body = ParagraphStyle(
        "PlanBody",
        parent=sample["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.2,
        textColor=colors.black,
        spaceAfter=5,
        allowWidows=0,
        allowOrphans=0,
    )
    return {
        "title": ParagraphStyle(
            "PlanTitle",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "PlanH2",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            spaceBefore=9,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "PlanH3",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            spaceBefore=7,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "h4": ParagraphStyle(
            "PlanH4",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            spaceBefore=5,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "body": body,
        "quote": ParagraphStyle(
            "PlanQuote",
            parent=body,
            fontName="Helvetica-Oblique",
            leftIndent=10,
            borderWidth=0,
            spaceBefore=4,
            spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "PlanBullet",
            parent=body,
            leftIndent=13,
            firstLineIndent=-9,
            bulletIndent=0,
            spaceAfter=2,
        ),
        "number": ParagraphStyle(
            "PlanNumber",
            parent=body,
            leftIndent=16,
            firstLineIndent=-13,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "PlanCode",
            parent=body,
            fontName="Courier",
            fontSize=7,
            leading=9,
            leftIndent=6,
            rightIndent=6,
            spaceBefore=3,
            spaceAfter=7,
        ),
        "table": ParagraphStyle(
            "PlanTable",
            parent=body,
            fontSize=7.2,
            leading=9.1,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "table_header": ParagraphStyle(
            "PlanTableHeader",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9.1,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
    }


def is_structural(line: str) -> bool:
    """Return whether a Markdown line starts a new block."""

    stripped = line.strip()
    return bool(
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("```")
        or stripped.startswith(">")
        or stripped.startswith("|")
        or stripped == "---"
        or re.match(r"^[-*]\s+", stripped)
        or re.match(r"^\d+\.\s+", stripped)
    )


def column_widths(column_count: int) -> list[float]:
    """Return stable widths for the two- and three-column tables in the plan."""

    if column_count == 2:
        return [CONTENT_WIDTH * 0.31, CONTENT_WIDTH * 0.69]
    if column_count == 3:
        return [CONTENT_WIDTH * 0.22, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.53]
    return [CONTENT_WIDTH / column_count] * column_count


def table_flowable(rows: list[list[str]], styles: dict[str, ParagraphStyle]) -> LongTable:
    """Build a repeating-header table that can split safely across pages."""

    formatted: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = styles["table_header"] if row_index == 0 else styles["table"]
        formatted.append([Paragraph(inline_markup(cell), style) for cell in row])
    table = LongTable(
        formatted,
        colWidths=column_widths(len(rows[0])),
        repeatRows=1,
        splitByRow=True,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, 0), 0.9, colors.black),
            ]
        )
    )
    return table


def markdown_story(source: str, styles: dict[str, ParagraphStyle]) -> list[object]:
    """Parse the plan's constrained Markdown into Platypus flowables."""

    lines = source.splitlines()
    story: list[object] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(normalise_text(lines[index]))
                index += 1
            index += 1
            story.append(Preformatted("\n".join(code), styles["code"], maxLineLength=112))
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            style_name = "title" if level == 1 else f"h{level}"
            story.append(Paragraph(inline_markup(heading.group(2)), styles[style_name]))
            index += 1
            continue
        if stripped == "---":
            story.append(Spacer(1, 3))
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.black))
            story.append(Spacer(1, 5))
            index += 1
            continue
        if stripped.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            rows = [
                [cell.strip() for cell in table_line.strip("|").split("|")]
                for table_line in table_lines
            ]
            if len(rows) > 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
                rows.pop(1)
            story.extend([table_flowable(rows, styles), Spacer(1, 7)])
            continue
        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            story.append(Paragraph(inline_markup(" ".join(quote_lines)), styles["quote"]))
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        numbered = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if bullet or numbered:
            marker = "-" if bullet else f"{numbered.group(1)}."
            content = (bullet or numbered).group(1 if bullet else 2)
            index += 1
            continuations: list[str] = []
            while index < len(lines) and lines[index].strip() and not is_structural(lines[index]):
                continuations.append(lines[index].strip())
                index += 1
            if continuations:
                content = " ".join([content, *continuations])
            style = styles["bullet"] if bullet else styles["number"]
            story.append(Paragraph(f"<b>{marker}</b> {inline_markup(content)}", style))
            continue
        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and not is_structural(lines[index]):
            paragraph_lines.append(lines[index].strip())
            index += 1
        story.append(Paragraph(inline_markup(" ".join(paragraph_lines)), styles["body"]))
    return story


def draw_page_frame(canvas, document) -> None:
    """Draw an unobtrusive monochrome header, rule and page number."""

    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setFillColor(colors.black)
    canvas.setLineWidth(0.45)
    canvas.line(LEFT_MARGIN, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 13 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(LEFT_MARGIN, PAGE_HEIGHT - 10 * mm, "FIT5238 Team SA34 - Iteration 2 Testing Plan")
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def render(source_path: Path, output_path: Path) -> None:
    """Render one Markdown source file into the requested PDF path."""

    source = source_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Iteration 2 Testing Plan",
        author="FIT5238 Team SA34",
        subject="Browser interaction and automated verification plan",
    )
    document.build(
        markdown_story(source, styles),
        onFirstPage=draw_page_frame,
        onLaterPages=draw_page_frame,
    )


def parse_args() -> argparse.Namespace:
    """Parse optional source and output paths for reproducible local use."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    render(arguments.source, arguments.output)
