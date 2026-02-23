# GeneaTree

Desktop-приложение на Python/PySide6 для создания генеалогического древа с визуальным редактированием и экспортом в PDF.

## Возможности MVP

- интерфейс на русском языке
- карточки людей (ФИО, даты, заметка, фото)
- связи `parent -> child` и `spouse`
- автолэйаут по поколениям + ручное перетаскивание
- сохранение/загрузка проекта в JSON
- экспорт сцены в PDF (A4/A3/Letter, ориентация, поля, fit-to-page)
- быстрый ввод: автозаполнение короткого имени из ФИО, поиск людей в форме связи, горячие клавиши

## Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Запуск

```bash
python -m geneatree
```

## Проверки

```bash
pytest -q
ruff check .
ruff format .
```

## Сборка EXE для Windows

Сборку `exe` нужно делать в Windows (нативно).

### Вариант 1: локально в Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[build]"
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

Результат:
- `dist\Drevo\Drevo.exe` (по умолчанию, стабильнее)
- `dist\Drevo.exe` (если запускать с `-OneFile`)

### Вариант 2: через GitHub Actions

Запусти workflow `.github/workflows/windows-exe.yml` (`workflow_dispatch`), он соберет `Drevo.exe` на `windows-latest` и приложит артефакт `Drevo-windows`.
