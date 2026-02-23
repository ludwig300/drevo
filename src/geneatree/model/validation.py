from __future__ import annotations

from collections import Counter

from .entities import TreeProject


def validate_project(project: TreeProject) -> list[str]:
    errors: list[str] = []

    person_ids = [person.id for person in project.people]
    duplicate_person_ids = {pid for pid, count in Counter(person_ids).items() if count > 1}
    if duplicate_person_ids:
        errors.append(f"Duplicate person ids: {sorted(duplicate_person_ids)}")

    relationship_ids = [rel.id for rel in project.relationships]
    duplicate_relationship_ids = {
        rid for rid, count in Counter(relationship_ids).items() if count > 1
    }
    if duplicate_relationship_ids:
        errors.append(f"Duplicate relationship ids: {sorted(duplicate_relationship_ids)}")

    known_people = set(person_ids)
    for rel in project.relationships:
        if rel.type not in {"parent", "spouse"}:
            errors.append(f"Unknown relationship type: {rel.id}:{rel.type}")
        if rel.from_id not in known_people:
            errors.append(f"Relationship {rel.id} references missing from_id={rel.from_id}")
        if rel.to_id not in known_people:
            errors.append(f"Relationship {rel.id} references missing to_id={rel.to_id}")
        if rel.from_id == rel.to_id:
            errors.append(f"Relationship {rel.id} links person to itself")

    return errors


def assert_valid_project(project: TreeProject) -> None:
    errors = validate_project(project)
    if errors:
        raise ValueError("Invalid project data:\n- " + "\n- ".join(errors))
