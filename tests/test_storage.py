from __future__ import annotations

from pathlib import Path

from geneatree.model.entities import Person, Position, Relationship, TreeProject
from geneatree.model.storage import load_project, save_project


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    source_photo = tmp_path / "source.jpg"
    source_photo.write_bytes(b"fakejpg")

    parent = Person(display_name="Parent", photo_path=str(source_photo), pos=Position(10, 20))
    child = Person(display_name="Child", pos=Position(30, 40))

    project = TreeProject(
        people=[parent, child],
        relationships=[Relationship(type="parent", from_id=parent.id, to_id=child.id)],
    )

    project_path = tmp_path / "tree.json"
    save_project(project, project_path)

    assert project_path.exists()
    assert parent.photo_path is not None
    assert parent.photo_path.startswith("assets/")

    copied_asset = tmp_path / parent.photo_path
    assert copied_asset.exists()

    loaded = load_project(project_path)
    assert len(loaded.people) == 2
    assert len(loaded.relationships) == 1

    loaded_parent = next(person for person in loaded.people if person.id == parent.id)
    assert loaded_parent.display_name == "Parent"
    assert loaded_parent.photo_path == parent.photo_path


def test_save_ignores_missing_photo_file(tmp_path: Path) -> None:
    person = Person(display_name="No Photo", photo_path="missing.jpg")
    project = TreeProject(people=[person])

    project_path = tmp_path / "tree.json"
    save_project(project, project_path)

    loaded = load_project(project_path)
    assert loaded.people[0].photo_path == "missing.jpg"
