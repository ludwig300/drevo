from __future__ import annotations

from collections import defaultdict

from geneatree.model.entities import TreeProject


def compute_generations(project: TreeProject) -> dict[str, int]:
    levels = {person.id: 0 for person in project.people}
    parent_edges = [
        (rel.from_id, rel.to_id)
        for rel in project.relationships
        if rel.type == "parent" and rel.from_id in levels and rel.to_id in levels
    ]

    for _ in range(max(1, len(levels))):
        changed = False
        for parent_id, child_id in parent_edges:
            candidate_level = levels[parent_id] + 1
            if candidate_level > levels[child_id]:
                levels[child_id] = candidate_level
                changed = True
        if not changed:
            break

    return levels


def auto_layout(project: TreeProject, start_x: float = 0.0, start_y: float = 0.0) -> dict[str, int]:
    levels = compute_generations(project)
    people_by_id = project.people_by_id()

    groups: dict[int, list[str]] = defaultdict(list)
    for person_id, level in levels.items():
        groups[level].append(person_id)

    for level, person_ids in groups.items():
        person_ids.sort(key=lambda pid: (people_by_id[pid].display_name.lower(), pid))
        row_width = (len(person_ids) - 1) * project.settings.sibling_spacing
        row_start = start_x - (row_width / 2)

        for index, person_id in enumerate(person_ids):
            person = people_by_id[person_id]
            person.pos.x = row_start + index * project.settings.sibling_spacing
            person.pos.y = start_y + level * project.settings.generation_spacing

    return levels
