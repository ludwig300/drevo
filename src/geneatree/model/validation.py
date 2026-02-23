from __future__ import annotations

from collections import Counter

from .entities import TreeProject


def _has_parent_cycle(children_by_parent: dict[str, set[str]]) -> bool:
    # 0 = unvisited, 1 = visiting, 2 = visited
    state: dict[str, int] = {person_id: 0 for person_id in children_by_parent}

    def visit(person_id: str) -> bool:
        current = state.get(person_id, 0)
        if current == 1:
            return True
        if current == 2:
            return False

        state[person_id] = 1
        for child_id in children_by_parent.get(person_id, set()):
            if visit(child_id):
                return True
        state[person_id] = 2
        return False

    return any(visit(person_id) for person_id in children_by_parent if state[person_id] == 0)


def validate_project(project: TreeProject) -> list[str]:
    errors: list[str] = []

    person_ids = [person.id for person in project.people]
    duplicate_person_ids = {pid for pid, count in Counter(person_ids).items() if count > 1}
    if duplicate_person_ids:
        errors.append(f"Duplicate person ids: {sorted(duplicate_person_ids)}")

    for person in project.people:
        display_name = str(person.display_name or "").strip()
        full_name = str(person.full_name or "").strip() if person.full_name else ""
        if not display_name and not full_name:
            errors.append(f"Person {person.id} has no display_name or full_name")

    relationship_ids = [rel.id for rel in project.relationships]
    duplicate_relationship_ids = {
        rid for rid, count in Counter(relationship_ids).items() if count > 1
    }
    if duplicate_relationship_ids:
        errors.append(f"Duplicate relationship ids: {sorted(duplicate_relationship_ids)}")

    known_people = set(person_ids)
    parent_pairs: set[tuple[str, str]] = set()
    spouse_pairs: set[tuple[str, str]] = set()
    children_by_parent: dict[str, set[str]] = {person_id: set() for person_id in known_people}

    for rel in project.relationships:
        if rel.type not in {"parent", "spouse"}:
            errors.append(f"Unknown relationship type: {rel.id}:{rel.type}")
        if rel.from_id not in known_people:
            errors.append(f"Relationship {rel.id} references missing from_id={rel.from_id}")
        if rel.to_id not in known_people:
            errors.append(f"Relationship {rel.id} references missing to_id={rel.to_id}")
        if rel.from_id == rel.to_id:
            errors.append(f"Relationship {rel.id} links person to itself")

        if rel.type == "parent":
            key = (rel.from_id, rel.to_id)
            if key in parent_pairs:
                errors.append(f"Duplicate parent relationship: {rel.from_id}->{rel.to_id}")
            parent_pairs.add(key)

            if rel.from_id in known_people and rel.to_id in known_people:
                children_by_parent[rel.from_id].add(rel.to_id)
        elif rel.type == "spouse":
            key = tuple(sorted((rel.from_id, rel.to_id)))
            if key in spouse_pairs:
                errors.append(f"Duplicate spouse relationship: {key[0]}<->{key[1]}")
            spouse_pairs.add(key)

    if _has_parent_cycle(children_by_parent):
        errors.append("Parent relationships contain a cycle")

    return errors


def assert_valid_project(project: TreeProject) -> None:
    errors = validate_project(project)
    if errors:
        raise ValueError("Invalid project data:\n- " + "\n- ".join(errors))
