from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPainter
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
)

from geneatree.model.entities import Relationship, TreeProject
from geneatree.model.storage import StorageError, load_project, save_project
from geneatree.scene.export_pdf import PdfExportOptions, export_scene_to_pdf
from geneatree.scene.graphics_items import EdgeItem, PersonItem
from geneatree.scene.layout import auto_layout
from geneatree.ui.dialogs import PdfExportDialog, PersonDialog, RelationshipDialog


class TreeGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent=None) -> None:  # noqa: ANN001
        super().__init__(scene, parent)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event) -> None:  # noqa: ANN001
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Генеалогическое древо")
        self.resize(1400, 900)

        self.project = TreeProject()
        self.project_path: Path | None = None

        self.scene = QGraphicsScene(self)
        self.view = TreeGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.person_items: dict[str, PersonItem] = {}
        self.edge_items: dict[str, EdgeItem] = {}

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self.refresh_scene()
        self.statusBar().showMessage(
            "Подсказка: двойной клик по карточке открывает редактирование.",
            7000,
        )

    def _build_actions(self) -> None:
        self.new_action = QAction("Новый", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_project)

        self.open_action = QAction("Открыть...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_project)

        self.save_action = QAction("Сохранить", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_project)

        self.save_as_action = QAction("Сохранить как...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_project_as)

        self.export_pdf_action = QAction("Экспорт PDF...", self)
        self.export_pdf_action.setShortcut("Ctrl+E")
        self.export_pdf_action.triggered.connect(self.export_pdf)

        self.add_person_action = QAction("Добавить человека", self)
        self.add_person_action.setShortcut("Ctrl+P")
        self.add_person_action.triggered.connect(self.add_person)

        self.add_relationship_action = QAction("Добавить связь", self)
        self.add_relationship_action.setShortcut("Ctrl+R")
        self.add_relationship_action.triggered.connect(self.add_relationship)

        self.layout_action = QAction("Автораскладка", self)
        self.layout_action.setShortcut("Ctrl+L")
        self.layout_action.triggered.connect(self.apply_auto_layout)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_pdf_action)

        edit_menu = self.menuBar().addMenu("Правка")
        edit_menu.addAction(self.add_person_action)
        edit_menu.addAction(self.add_relationship_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.layout_action)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Основное")
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.add_person_action)
        toolbar.addAction(self.add_relationship_action)
        toolbar.addAction(self.layout_action)
        toolbar.addSeparator()
        toolbar.addAction(self.export_pdf_action)

    def _update_window_title(self) -> None:
        filename = self.project_path.name if self.project_path else "Без имени"
        self.setWindowTitle(f"Генеалогическое древо - {filename}")

    def _ensure_absolute_photo_paths(self) -> None:
        if not self.project_path:
            return
        project_dir = self.project_path.parent
        for person in self.project.people:
            if not person.photo_path:
                continue
            photo = Path(person.photo_path)
            if photo.is_absolute():
                continue
            candidate = project_dir / photo
            if candidate.exists():
                person.photo_path = str(candidate)

    def new_project(self) -> None:
        self.project = TreeProject()
        self.project_path = None
        self.refresh_scene()
        self._update_window_title()

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть проект", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self.project_path = Path(path)
            self._ensure_absolute_photo_paths()
            self.refresh_scene()
            self._update_window_title()
            self.statusBar().showMessage(f"Проект открыт: {self.project_path}", 3000)
        except StorageError as exc:
            QMessageBox.critical(self, "Ошибка открытия", str(exc))

    def save_project(self) -> None:
        if self.project_path is None:
            self.save_project_as()
            return

        try:
            save_project(self.project, self.project_path)
            self._ensure_absolute_photo_paths()
            self.statusBar().showMessage(f"Сохранено: {self.project_path}", 3000)
        except (StorageError, ValueError) as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить проект",
            "drevo.json",
            "JSON (*.json)",
        )
        if not path:
            return

        target = Path(path)
        if target.suffix.lower() != ".json":
            target = target.with_suffix(".json")

        self.project_path = target
        self.save_project()
        self._update_window_title()

    def add_person(self) -> None:
        dialog = PersonDialog(parent=self)
        if dialog.exec() != PersonDialog.DialogCode.Accepted:
            return

        person = dialog.build_person()
        scene_center = self.view.mapToScene(self.view.viewport().rect().center())
        person.pos.x = float(scene_center.x())
        person.pos.y = float(scene_center.y())
        self.project.people.append(person)
        self.refresh_scene()
        self.statusBar().showMessage(f"Добавлен: {person.display_name}", 2500)

    def edit_person(self, person_id: str) -> None:
        person = self.project.get_person(person_id)
        if person is None:
            return
        dialog = PersonDialog(person, self)
        if dialog.exec() != PersonDialog.DialogCode.Accepted:
            return

        dialog.build_person()
        self.refresh_scene()

    def delete_person(self, person_id: str) -> None:
        person = self.project.get_person(person_id)
        if person is None:
            return

        answer = QMessageBox.question(
            self,
            "Удаление человека",
            f"Удалить '{person.display_name}' и все связанные связи?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.project.remove_person(person_id)
        self.refresh_scene()

    def add_relationship(
        self,
        forced_type: str | None = None,
        fixed_from_id: str | None = None,
        fixed_to_id: str | None = None,
    ) -> None:
        if len(self.project.people) < 2:
            QMessageBox.warning(
                self,
                "Недостаточно людей",
                "Сначала добавьте минимум двух человек.",
            )
            return

        dialog = RelationshipDialog(
            self.project.people,
            forced_type=forced_type,
            fixed_from_id=fixed_from_id,
            fixed_to_id=fixed_to_id,
            parent=self,
        )
        if dialog.exec() != RelationshipDialog.DialogCode.Accepted:
            return

        relationship = dialog.build_relationship()
        duplicate = self._is_duplicate_relationship(relationship)
        if duplicate:
            QMessageBox.warning(self, "Дубликат", "Такая связь уже существует.")
            return

        self.project.relationships.append(relationship)
        self.refresh_scene()
        self.statusBar().showMessage("Связь добавлена", 2500)

    def _is_duplicate_relationship(self, relationship: Relationship) -> bool:
        if relationship.type == "spouse":
            pair = {relationship.from_id, relationship.to_id}
            return any(
                rel.type == "spouse" and {rel.from_id, rel.to_id} == pair
                for rel in self.project.relationships
            )

        return any(
            rel.type == relationship.type
            and rel.from_id == relationship.from_id
            and rel.to_id == relationship.to_id
            for rel in self.project.relationships
        )

    def on_link_requested(self, person_id: str, mode: str) -> None:
        if mode == "add_child":
            self.add_relationship(forced_type="parent", fixed_from_id=person_id)
        elif mode == "add_parent":
            self.add_relationship(forced_type="parent", fixed_to_id=person_id)
        elif mode == "add_spouse":
            self.add_relationship(forced_type="spouse", fixed_from_id=person_id)

    def apply_auto_layout(self) -> None:
        auto_layout(self.project)
        self.refresh_scene()

    def export_pdf(self) -> None:
        if not self.project.people:
            QMessageBox.warning(self, "Экспорт PDF", "На схеме пока нет данных для экспорта.")
            return

        default_options = PdfExportOptions(
            page_size=self.project.settings.page_size,
            orientation=self.project.settings.orientation,
            margin_mm=self.project.settings.margin_mm,
        )
        dialog = PdfExportDialog(default_options, self)
        if dialog.exec() != PdfExportDialog.DialogCode.Accepted:
            return

        options = dialog.build_options()

        path, _ = QFileDialog.getSaveFileName(self, "Экспорт PDF", "drevo.pdf", "PDF (*.pdf)")
        if not path:
            return

        target = Path(path)
        if target.suffix.lower() != ".pdf":
            target = target.with_suffix(".pdf")

        try:
            export_scene_to_pdf(self.scene, target, options)
            self.project.settings.page_size = options.page_size
            self.project.settings.orientation = options.orientation
            self.project.settings.margin_mm = options.margin_mm
            self.statusBar().showMessage(f"PDF экспортирован: {target}", 3000)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))

    def refresh_scene(self) -> None:
        for edge in self.edge_items.values():
            edge.detach()
        self.edge_items.clear()

        self.scene.clear()
        self.person_items.clear()

        width = self.project.settings.card_width
        height = self.project.settings.card_height

        for person in self.project.people:
            item = PersonItem(person, width=width, height=height)
            item.edit_requested.connect(self.edit_person)
            item.delete_requested.connect(self.delete_person)
            item.link_requested.connect(self.on_link_requested)
            self.scene.addItem(item)
            self.person_items[person.id] = item

        for relationship in self.project.relationships:
            source = self.person_items.get(relationship.from_id)
            target = self.person_items.get(relationship.to_id)
            if source is None or target is None:
                continue
            edge = EdgeItem(source, target, relationship.type)
            self.scene.addItem(edge)
            self.edge_items[relationship.id] = edge

        if self.person_items:
            rect = self.scene.itemsBoundingRect().adjusted(-300, -300, 300, 300)
            self.scene.setSceneRect(rect)
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.scene.setSceneRect(-500, -300, 1000, 600)

        self._update_window_title()
