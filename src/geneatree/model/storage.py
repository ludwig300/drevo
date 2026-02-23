from __future__ import annotations

import json
import shutil
from pathlib import Path

from .entities import TreeProject
from .validation import assert_valid_project


class StorageError(Exception):
    pass


def _resolve_input_photo_path(photo_path: str, project_dir: Path) -> Path:
    path = Path(photo_path)
    if path.is_absolute():
        return path
    return project_dir / path


def save_project(project: TreeProject, path: str | Path) -> None:
    assert_valid_project(project)

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    project_dir = target_path.parent
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    payload = project.to_dict()
    assets_manifest: dict[str, str] = {}

    for index, person in enumerate(project.people):
        if not person.photo_path:
            continue

        source_path = _resolve_input_photo_path(person.photo_path, project_dir)
        if not source_path.exists() or not source_path.is_file():
            continue

        suffix = source_path.suffix or ".jpg"
        asset_rel_path = Path("assets") / f"{person.id}{suffix.lower()}"
        asset_abs_path = project_dir / asset_rel_path

        if source_path.resolve() != asset_abs_path.resolve():
            shutil.copy2(source_path, asset_abs_path)

        normalized = asset_rel_path.as_posix()
        payload["people"][index]["photo_path"] = normalized
        person.photo_path = normalized
        assets_manifest[person.id] = normalized

    payload["assets_manifest"] = assets_manifest

    try:
        target_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise StorageError(f"Не удалось сохранить проект: {target_path}") from exc


def load_project(path: str | Path) -> TreeProject:
    source_path = Path(path)
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StorageError(f"Не удалось прочитать файл проекта: {source_path}") from exc
    except json.JSONDecodeError as exc:
        raise StorageError(f"Файл проекта не является корректным JSON: {source_path}") from exc

    try:
        project = TreeProject.from_dict(raw)
        assert_valid_project(project)
    except Exception as exc:  # noqa: BLE001
        raise StorageError("Данные проекта некорректны") from exc

    return project
