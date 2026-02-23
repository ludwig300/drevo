from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QMarginsF, QRectF, Qt
from PySide6.QtGui import QPageLayout, QPageSize, QPainter, QPdfWriter
from PySide6.QtWidgets import QGraphicsScene


@dataclass
class PdfExportOptions:
    page_size: str = "A4"
    orientation: str = "portrait"
    margin_mm: float = 10.0
    fit_to_page: bool = True
    dpi: int = 300


def _page_size_id(value: str) -> QPageSize.PageSizeId:
    normalized = value.upper().strip()
    mapping: dict[str, QPageSize.PageSizeId] = {
        "A4": QPageSize.PageSizeId.A4,
        "A3": QPageSize.PageSizeId.A3,
        "LETTER": QPageSize.PageSizeId.Letter,
    }
    return mapping.get(normalized, QPageSize.PageSizeId.A4)


def export_scene_to_pdf(
    scene: QGraphicsScene,
    output_path: str | Path,
    options: PdfExportOptions | None = None,
) -> None:
    opts = options or PdfExportOptions()

    writer = QPdfWriter(str(output_path))
    writer.setResolution(opts.dpi)

    orientation = (
        QPageLayout.Orientation.Landscape
        if opts.orientation.lower() == "landscape"
        else QPageLayout.Orientation.Portrait
    )

    page_layout = QPageLayout(
        QPageSize(_page_size_id(opts.page_size)),
        orientation,
        QMarginsF(opts.margin_mm, opts.margin_mm, opts.margin_mm, opts.margin_mm),
        QPageLayout.Unit.Millimeter,
    )
    writer.setPageLayout(page_layout)

    source = scene.itemsBoundingRect().adjusted(-20.0, -20.0, 20.0, 20.0)
    if source.isNull():
        source = QRectF(0, 0, 100, 100)

    target_rect = QRectF(page_layout.paintRectPixels(writer.resolution()))

    painter = QPainter(writer)
    try:
        mode = (
            Qt.AspectRatioMode.KeepAspectRatio
            if opts.fit_to_page
            else Qt.AspectRatioMode.IgnoreAspectRatio
        )
        scene.render(painter, target_rect, source, mode)
    finally:
        painter.end()
