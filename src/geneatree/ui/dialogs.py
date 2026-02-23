from __future__ import annotations

import re

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from geneatree.model.entities import Person, Relationship, new_id
from geneatree.scene.export_pdf import PdfExportOptions

DATE_FORMAT = "dd.MM.yyyy"
YEAR_PATTERN = re.compile(r"^\d{4}$")


def short_name_from_full_name(full_name: str) -> str:
    parts = [part for part in full_name.replace(",", " ").split() if part]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return " ".join(parts[:2])


class PersonDialog(QDialog):
    def __init__(self, person: Person | None = None, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Человек")
        self._source_person = person
        self._last_auto_display_name = ""

        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("Короткое имя на карточке, например: Иван")

        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Фамилия Имя Отчество")

        self.auto_short_name_check = QCheckBox("Автоматически брать короткое имя из ФИО")

        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Не указан", "")
        self.gender_combo.addItem("Мужской", "male")
        self.gender_combo.addItem("Женский", "female")
        self.gender_combo.addItem("Другой", "other")

        self.birth_date_edit, birth_date_field = self._build_date_field("Дата рождения")
        self.death_date_edit, death_date_field = self._build_date_field("Дата смерти")

        self.note_edit = QPlainTextEdit()
        self.note_edit.setPlaceholderText("Короткая заметка (опционально)")

        self.photo_path_edit = QLineEdit()
        self.photo_path_edit.setReadOnly(True)
        self.photo_path_edit.setPlaceholderText("Фото не выбрано")
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(96, 96)
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setStyleSheet("border: 1px solid #cbd5e1; background: #f8fafc;")
        photo_btn = QPushButton("Выбрать...")
        photo_btn.clicked.connect(self._pick_photo)
        clear_photo_btn = QPushButton("Очистить")
        clear_photo_btn.clicked.connect(self._clear_photo)

        photo_row = QHBoxLayout()
        photo_row.addWidget(self.photo_path_edit)
        photo_row.addWidget(photo_btn)
        photo_row.addWidget(clear_photo_btn)

        form = QFormLayout()
        form.addRow("Имя на карточке", self.display_name_edit)
        form.addRow("ФИО", self.full_name_edit)
        form.addRow("", self.auto_short_name_check)
        form.addRow("Пол", self.gender_combo)
        form.addRow("Дата рождения", birth_date_field)
        form.addRow("Дата смерти", death_date_field)
        form.addRow("Заметка", self.note_edit)
        form.addRow("Фото", photo_row)

        preview_grid = QGridLayout()
        preview_grid.addWidget(self.photo_preview, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(preview_grid)
        layout.addWidget(button_box)

        self.full_name_edit.textChanged.connect(self._on_full_name_changed)
        self.auto_short_name_check.toggled.connect(self._on_auto_short_name_toggled)

        auto_short_name_default = person is None or not (person.display_name if person else "")
        self.auto_short_name_check.setChecked(auto_short_name_default)

        if person is not None:
            self.display_name_edit.setText(person.display_name)
            self.full_name_edit.setText(person.full_name or "")
            self._set_combo_by_data(self.gender_combo, person.gender or "")
            self.birth_date_edit.setText(self._normalized_date_text(person.birth_date or ""))
            self.death_date_edit.setText(self._normalized_date_text(person.death_date or ""))
            self.note_edit.setPlainText(person.note or "")
            self.photo_path_edit.setText(person.photo_path or "")
            self._load_preview(person.photo_path)

        if self.auto_short_name_check.isChecked():
            self._apply_auto_short_name()

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    def _build_date_field(self, title: str) -> tuple[QLineEdit, QWidget]:
        edit = QLineEdit()
        edit.setPlaceholderText("дд.мм.гггг, yyyy-mm-dd или yyyy")
        edit.setClearButtonEnabled(True)

        calendar_btn = QPushButton("Календарь")
        calendar_btn.setToolTip("Выбрать дату из календаря")
        calendar_btn.clicked.connect(lambda: self._open_calendar_for(edit, title))

        row_widget = QWidget(self)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(edit)
        row_layout.addWidget(calendar_btn)
        return edit, row_widget

    def _open_calendar_for(self, edit: QLineEdit, title: str) -> None:
        selected = self._parse_date_text(edit.text()) or QDate.currentDate()

        dialog = QDialog(self)
        dialog.setWindowTitle(title)

        calendar = QCalendarWidget(dialog)
        calendar.setGridVisible(True)
        calendar.setSelectedDate(selected)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout = QVBoxLayout(dialog)
        layout.addWidget(calendar)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            edit.setText(calendar.selectedDate().toString(DATE_FORMAT))

    @staticmethod
    def _parse_date_text(value: str) -> QDate | None:
        text = PersonDialog._normalized_raw_date(value)
        if not text:
            return None
        for fmt in (DATE_FORMAT, "yyyy-MM-dd", "yyyy"):
            parsed = QDate.fromString(text, fmt)
            if parsed.isValid():
                return parsed
        return None

    @staticmethod
    def _normalized_raw_date(value: str) -> str:
        text = value.strip().replace("_", "")
        if not any(ch.isdigit() for ch in text):
            return ""
        return text

    @staticmethod
    def _is_year_text(value: str) -> bool:
        return bool(YEAR_PATTERN.fullmatch(value))

    def _normalized_date_text(self, value: str) -> str:
        text = self._normalized_raw_date(value)
        if not text:
            return ""
        if self._is_year_text(text):
            return text

        parsed = self._parse_date_text(text)
        if not parsed:
            return text
        return parsed.toString(DATE_FORMAT)

    def _pick_photo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фото",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not path:
            return
        self.photo_path_edit.setText(path)
        self._load_preview(path)

    def _clear_photo(self) -> None:
        self.photo_path_edit.clear()
        self.photo_preview.setPixmap(QPixmap())
        self.photo_preview.setText("")

    def _on_auto_short_name_toggled(self, checked: bool) -> None:
        if checked:
            self._apply_auto_short_name()

    def _on_full_name_changed(self, _text: str) -> None:
        self._apply_auto_short_name()

    def _apply_auto_short_name(self) -> None:
        if not self.auto_short_name_check.isChecked():
            return

        generated = short_name_from_full_name(self.full_name_edit.text())
        if not generated:
            return

        current = self.display_name_edit.text().strip()
        if current and current != self._last_auto_display_name:
            return

        self.display_name_edit.setText(generated)
        self._last_auto_display_name = generated

    def _load_preview(self, path: str | None) -> None:
        if not path:
            self.photo_preview.setPixmap(QPixmap())
            self.photo_preview.setText("")
            self.photo_preview.clear()
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.photo_preview.setPixmap(QPixmap())
            self.photo_preview.setText("Нет превью")
            return
        scaled = pixmap.scaled(
            self.photo_preview.width(),
            self.photo_preview.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.photo_preview.setText("")
        self.photo_preview.setPixmap(scaled)

    def _accept(self) -> None:
        display_name = self.display_name_edit.text().strip()
        full_name = self.full_name_edit.text().strip()

        if not display_name and full_name:
            generated = short_name_from_full_name(full_name)
            if generated:
                self.display_name_edit.setText(generated)
                display_name = generated

        if not display_name:
            QMessageBox.warning(
                self,
                "Проверка данных",
                "Заполните поле 'Имя на карточке' или 'ФИО'.",
            )
            return

        for field_name, edit in (
            ("Дата рождения", self.birth_date_edit),
            ("Дата смерти", self.death_date_edit),
        ):
            raw = self._normalized_raw_date(edit.text())
            if not raw:
                edit.clear()
                continue

            parsed = self._parse_date_text(raw)
            if parsed is None:
                QMessageBox.warning(
                    self,
                    "Проверка данных",
                    (
                        f"{field_name} должна быть в формате дд.мм.гггг, yyyy-mm-dd "
                        "или yyyy."
                    ),
                )
                return

            if self._is_year_text(raw):
                edit.setText(raw)
            else:
                edit.setText(parsed.toString(DATE_FORMAT))

        self.accept()

    def build_person(self) -> Person:
        person = self._source_person or Person(id=new_id())
        person.display_name = self.display_name_edit.text().strip()
        person.full_name = self.full_name_edit.text().strip() or None
        person.gender = str(self.gender_combo.currentData() or "") or None
        person.birth_date = self.birth_date_edit.text().strip() or None
        person.death_date = self.death_date_edit.text().strip() or None
        person.note = self.note_edit.toPlainText().strip() or None
        raw_photo = self.photo_path_edit.text().strip()
        person.photo_path = raw_photo or None
        return person


class RelationshipDialog(QDialog):
    def __init__(
        self,
        people: list[Person],
        relationship: Relationship | None = None,
        forced_type: str | None = None,
        fixed_from_id: str | None = None,
        fixed_to_id: str | None = None,
        parent=None,  # noqa: ANN001
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Связь")
        self._source_relationship = relationship

        self.rel_type_combo = QComboBox()
        self.rel_type_combo.addItem("Родитель -> ребенок", "parent")
        self.rel_type_combo.addItem("Супруги", "spouse")
        if forced_type:
            self._set_combo_by_data(self.rel_type_combo, forced_type)
            self.rel_type_combo.setEnabled(False)

        self.from_combo = QComboBox()
        self.to_combo = QComboBox()

        for combo in (self.from_combo, self.to_combo):
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            combo.setMaxVisibleItems(25)
            completer = combo.completer()
            if completer is not None:
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        sorted_people = sorted(
            people,
            key=lambda person: (
                (person.display_name or person.full_name or "").lower(),
                person.id,
            ),
        )
        for person in sorted_people:
            label = person.display_name or person.full_name or person.id
            if person.full_name and person.full_name != label:
                label = f"{label} ({person.full_name})"
            self.from_combo.addItem(label, person.id)
            self.to_combo.addItem(label, person.id)

        if relationship:
            self._set_combo_by_data(self.rel_type_combo, relationship.type)
            self._set_combo_by_person_id(self.from_combo, relationship.from_id)
            self._set_combo_by_person_id(self.to_combo, relationship.to_id)

        if fixed_from_id:
            self._set_combo_by_person_id(self.from_combo, fixed_from_id)
            self.from_combo.setEnabled(False)
            self._select_first_different(self.to_combo, fixed_from_id)

        if fixed_to_id:
            self._set_combo_by_person_id(self.to_combo, fixed_to_id)
            self.to_combo.setEnabled(False)
            self._select_first_different(self.from_combo, fixed_to_id)

        if self.from_combo.currentData() == self.to_combo.currentData():
            self._select_first_different(self.to_combo, str(self.from_combo.currentData() or ""))

        self.from_label = QLabel()
        self.to_label = QLabel()

        form = QFormLayout()
        form.addRow("Тип связи", self.rel_type_combo)
        form.addRow(self.from_label, self.from_combo)
        form.addRow(self.to_label, self.to_combo)

        helper = QLabel("Подсказка: начните печатать имя, чтобы быстро найти человека.")
        helper.setWordWrap(True)
        helper.setStyleSheet("color: #475569;")

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(helper)
        layout.addWidget(button_box)

        self.rel_type_combo.currentIndexChanged.connect(self._update_role_labels)
        self._update_role_labels()

    @staticmethod
    def _set_combo_by_person_id(combo: QComboBox, person_id: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == person_id:
                combo.setCurrentIndex(index)
                return

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    @staticmethod
    def _select_first_different(combo: QComboBox, forbidden_person_id: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) != forbidden_person_id:
                combo.setCurrentIndex(index)
                return

    def _update_role_labels(self) -> None:
        relationship_type = str(self.rel_type_combo.currentData() or "parent")
        if relationship_type == "spouse":
            self.from_label.setText("Супруг 1")
            self.to_label.setText("Супруг 2")
            return

        self.from_label.setText("Родитель")
        self.to_label.setText("Ребенок")

    def _accept(self) -> None:
        if self.from_combo.currentData() == self.to_combo.currentData():
            QMessageBox.warning(
                self,
                "Проверка данных",
                "Нельзя связать человека с самим собой.",
            )
            return
        self.accept()

    def build_relationship(self) -> Relationship:
        relationship = self._source_relationship or Relationship(id=new_id())
        relationship.type = str(self.rel_type_combo.currentData() or "parent")  # type: ignore[assignment]
        relationship.from_id = str(self.from_combo.currentData())
        relationship.to_id = str(self.to_combo.currentData())
        return relationship


class PdfExportDialog(QDialog):
    def __init__(self, options: PdfExportOptions | None = None, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Экспорт в PDF")

        opts = options or PdfExportOptions()

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("A4", "A4")
        self.page_size_combo.addItem("A3", "A3")
        self.page_size_combo.addItem("Letter (US)", "Letter")
        self._set_combo_by_data(self.page_size_combo, opts.page_size)

        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("Книжная", "portrait")
        self.orientation_combo.addItem("Альбомная", "landscape")
        self._set_combo_by_data(self.orientation_combo, opts.orientation)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setValue(int(opts.margin_mm))
        self.margin_spin.setSuffix(" мм")

        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["150", "300"])
        self.dpi_combo.setCurrentText(str(opts.dpi))

        self.fit_check = QCheckBox("Уместить схему на страницу")
        self.fit_check.setChecked(opts.fit_to_page)

        form = QFormLayout()
        form.addRow("Формат бумаги", self.page_size_combo)
        form.addRow("Ориентация", self.orientation_combo)
        form.addRow("Поля", self.margin_spin)
        form.addRow("Качество (DPI)", self.dpi_combo)
        form.addRow("", self.fit_check)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(button_box)

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    def build_options(self) -> PdfExportOptions:
        return PdfExportOptions(
            page_size=str(self.page_size_combo.currentData() or "A4"),
            orientation=str(self.orientation_combo.currentData() or "portrait"),
            margin_mm=float(self.margin_spin.value()),
            fit_to_page=self.fit_check.isChecked(),
            dpi=int(self.dpi_combo.currentText()),
        )
