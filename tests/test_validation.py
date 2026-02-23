from __future__ import annotations

from geneatree.model.entities import Person, Relationship, TreeProject
from geneatree.model.validation import validate_project


def test_death_date_is_optional() -> None:
    person = Person(display_name="Иван", death_date=None)
    project = TreeProject(people=[person])

    assert validate_project(project) == []


def test_detects_parent_cycle() -> None:
    parent = Person(display_name="Parent")
    child = Person(display_name="Child")

    project = TreeProject(
        people=[parent, child],
        relationships=[
            Relationship(type="parent", from_id=parent.id, to_id=child.id),
            Relationship(type="parent", from_id=child.id, to_id=parent.id),
        ],
    )

    errors = validate_project(project)
    assert any("cycle" in error.lower() for error in errors)


def test_detects_duplicate_spouse_relationship() -> None:
    first = Person(display_name="A")
    second = Person(display_name="B")

    project = TreeProject(
        people=[first, second],
        relationships=[
            Relationship(type="spouse", from_id=first.id, to_id=second.id),
            Relationship(type="spouse", from_id=second.id, to_id=first.id),
        ],
    )

    errors = validate_project(project)
    assert any("duplicate spouse relationship" in error.lower() for error in errors)


def test_detects_person_without_any_name() -> None:
    project = TreeProject(people=[Person(display_name="", full_name=None)])

    errors = validate_project(project)
    assert any("has no display_name or full_name" in error.lower() for error in errors)
