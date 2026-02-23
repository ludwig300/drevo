from __future__ import annotations

from geneatree.model.entities import Person, Relationship, TreeProject
from geneatree.scene.layout import auto_layout, compute_generations


def test_generation_layout_order() -> None:
    gp = Person(display_name="Grandparent")
    p1 = Person(display_name="Parent A")
    p2 = Person(display_name="Parent B")
    child = Person(display_name="Child")

    project = TreeProject(
        people=[gp, p1, p2, child],
        relationships=[
            Relationship(type="parent", from_id=gp.id, to_id=p1.id),
            Relationship(type="parent", from_id=gp.id, to_id=p2.id),
            Relationship(type="spouse", from_id=p1.id, to_id=p2.id),
            Relationship(type="parent", from_id=p1.id, to_id=child.id),
        ],
    )

    levels = compute_generations(project)
    assert levels[gp.id] == 0
    assert levels[p1.id] == 1
    assert levels[p2.id] == 1
    assert levels[child.id] == 2

    auto_layout(project)

    assert gp.pos.y < p1.pos.y
    assert p1.pos.y == p2.pos.y
    assert child.pos.y > p1.pos.y
