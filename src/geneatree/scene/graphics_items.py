from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QMenu,
    QStyleOptionGraphicsItem,
    QWidget,
)

if TYPE_CHECKING:
    from geneatree.model.entities import Person


class PersonItem(QGraphicsObject):
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    link_requested = Signal(str, str)

    def __init__(self, person: Person, width: float, height: float) -> None:
        super().__init__()
        self.person = person
        self.width = width
        self.height = height
        self.edges: list[EdgeItem] = []
        self._photo = QPixmap()

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(1)
        self.setPos(self.person.pos.x, self.person.pos.y)
        self.reload_photo()

    def reload_photo(self) -> None:
        self._photo = QPixmap()
        if self.person.photo_path:
            self._photo.load(self.person.photo_path)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0.0, 0.0, self.width, self.height)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = self.pos()
            self.person.pos.x = float(pos.x())
            self.person.pos.y = float(pos.y())
            for edge in self.edges:
                edge.update_path()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: ANN001
        self.edit_requested.emit(self.person.id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: ANN001
        menu = QMenu()
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        menu.addSeparator()
        add_child_action = menu.addAction("Добавить связь с ребенком")
        add_parent_action = menu.addAction("Добавить связь с родителем")
        add_spouse_action = menu.addAction("Добавить связь с супругом")

        selected = menu.exec(event.screenPos())
        if selected == edit_action:
            self.edit_requested.emit(self.person.id)
        elif selected == delete_action:
            self.delete_requested.emit(self.person.id)
        elif selected == add_child_action:
            self.link_requested.emit(self.person.id, "add_child")
        elif selected == add_parent_action:
            self.link_requested.emit(self.person.id, "add_parent")
        elif selected == add_spouse_action:
            self.link_requested.emit(self.person.id, "add_spouse")

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        del option, widget

        rect = self.boundingRect()
        selected = self.isSelected()
        border_color = QColor("#0f172a") if not selected else QColor("#2563eb")

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QColor("#f8fafc"))
        painter.drawRoundedRect(rect, 10, 10)

        photo_rect = QRectF(8, 8, 58, 58)
        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.setBrush(QColor("#e2e8f0"))
        painter.drawRoundedRect(photo_rect, 6, 6)

        if not self._photo.isNull():
            scaled = self._photo.scaled(
                int(photo_rect.width()),
                int(photo_rect.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            pix_x = photo_rect.x() + (photo_rect.width() - scaled.width()) / 2
            pix_y = photo_rect.y() + (photo_rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(pix_x), int(pix_y), scaled)
        else:
            initials = (self.person.display_name[:1] if self.person.display_name else "?").upper()
            painter.setPen(QColor("#334155"))
            painter.setFont(QFont("Helvetica", 16, weight=QFont.Weight.Bold))
            painter.drawText(photo_rect, Qt.AlignmentFlag.AlignCenter, initials)

        text_x = 74
        text_width = self.width - text_x - 8

        name_font = QFont("Helvetica", 10, weight=QFont.Weight.Bold)
        name_metrics = QFontMetrics(name_font)
        painter.setFont(name_font)
        painter.setPen(QColor("#0f172a"))
        elided_name = name_metrics.elidedText(
            self.person.display_name or "Без имени",
            Qt.TextElideMode.ElideRight,
            int(text_width),
        )
        painter.drawText(
            QRectF(text_x, 8, text_width, 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided_name,
        )

        subtitle_font = QFont("Helvetica", 8)
        subtitle_metrics = QFontMetrics(subtitle_font)
        painter.setFont(subtitle_font)
        painter.setPen(QColor("#475569"))
        life_range = ""
        if self.person.birth_date or self.person.death_date:
            life_range = f"{self.person.birth_date or '?'} - {self.person.death_date or ''}".strip()
        full_name = self.person.full_name or ""
        line_1 = full_name if full_name else life_range
        line_2 = life_range if full_name else ""

        if line_1:
            painter.drawText(
                QRectF(text_x, 30, text_width, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                subtitle_metrics.elidedText(line_1, Qt.TextElideMode.ElideRight, int(text_width)),
            )
        if line_2:
            painter.drawText(
                QRectF(text_x, 46, text_width, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                subtitle_metrics.elidedText(line_2, Qt.TextElideMode.ElideRight, int(text_width)),
            )

        note_metrics = QFontMetrics(subtitle_font)
        note_text = (self.person.note or "").replace("\n", " ").strip()
        if note_text:
            painter.setPen(QColor("#64748b"))
            painter.drawText(
                QRectF(8, 72, self.width - 16, self.height - 80),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                note_metrics.elidedText(
                    note_text,
                    Qt.TextElideMode.ElideRight,
                    int(self.width - 16),
                ),
            )


class EdgeItem(QGraphicsPathItem):
    def __init__(self, source: PersonItem, target: PersonItem, relationship_type: str) -> None:
        super().__init__()
        self.source = source
        self.target = target
        self.relationship_type = relationship_type

        self.setPen(QPen(QColor("#334155"), 2))
        self.setZValue(-1)

        self.source.edges.append(self)
        self.target.edges.append(self)
        self.update_path()

    def detach(self) -> None:
        if self in self.source.edges:
            self.source.edges.remove(self)
        if self in self.target.edges:
            self.target.edges.remove(self)

    def update_path(self) -> None:
        source_rect = self.source.sceneBoundingRect()
        target_rect = self.target.sceneBoundingRect()

        path = QPainterPath()
        if self.relationship_type == "spouse":
            if source_rect.center().x() <= target_rect.center().x():
                start = QPointF(source_rect.right(), source_rect.center().y())
                end = QPointF(target_rect.left(), target_rect.center().y())
            else:
                start = QPointF(source_rect.left(), source_rect.center().y())
                end = QPointF(target_rect.right(), target_rect.center().y())
            path.moveTo(start)
            path.lineTo(end)
        else:
            start = QPointF(source_rect.center().x(), source_rect.bottom())
            end = QPointF(target_rect.center().x(), target_rect.top())
            mid_y = (start.y() + end.y()) / 2
            path.moveTo(start)
            path.lineTo(QPointF(start.x(), mid_y))
            path.lineTo(QPointF(end.x(), mid_y))
            path.lineTo(end)

        self.setPath(path)
