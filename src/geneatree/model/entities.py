from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

RelationshipType = Literal["parent", "spouse"]


def new_id() -> str:
    return uuid4().hex


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"x": float(self.x), "y": float(self.y)}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Position:
        if not data:
            return cls()
        return cls(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))


@dataclass
class Person:
    id: str = field(default_factory=new_id)
    display_name: str = "Новый человек"
    full_name: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    death_date: str | None = None
    note: str | None = None
    photo_path: str | None = None
    pos: Position = field(default_factory=Position)
    style: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "death_date": self.death_date,
            "note": self.note,
            "photo_path": self.photo_path,
            "pos": self.pos.to_dict(),
            "style": dict(self.style),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Person:
        return cls(
            id=str(data.get("id") or new_id()),
            display_name=str(data.get("display_name") or "Новый человек"),
            full_name=data.get("full_name"),
            gender=data.get("gender"),
            birth_date=data.get("birth_date"),
            death_date=data.get("death_date"),
            note=data.get("note"),
            photo_path=data.get("photo_path"),
            pos=Position.from_dict(data.get("pos")),
            style=dict(data.get("style") or {}),
        )


@dataclass
class Relationship:
    id: str = field(default_factory=new_id)
    type: RelationshipType = "parent"
    from_id: str = ""
    to_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Relationship:
        rel_type = data.get("type", "parent")
        if rel_type not in {"parent", "spouse"}:
            raise ValueError(f"Unsupported relationship type: {rel_type}")
        return cls(
            id=str(data.get("id") or new_id()),
            type=rel_type,
            from_id=str(data.get("from_id") or ""),
            to_id=str(data.get("to_id") or ""),
            meta=dict(data.get("meta") or {}),
        )


@dataclass
class TreeSettings:
    page_size: str = "A4"
    orientation: str = "portrait"
    margin_mm: float = 10.0
    card_width: float = 190.0
    card_height: float = 110.0
    generation_spacing: float = 190.0
    sibling_spacing: float = 230.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_size": self.page_size,
            "orientation": self.orientation,
            "margin_mm": self.margin_mm,
            "card_width": self.card_width,
            "card_height": self.card_height,
            "generation_spacing": self.generation_spacing,
            "sibling_spacing": self.sibling_spacing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> TreeSettings:
        if not data:
            return cls()
        return cls(
            page_size=str(data.get("page_size", "A4")),
            orientation=str(data.get("orientation", "portrait")),
            margin_mm=float(data.get("margin_mm", 10.0)),
            card_width=float(data.get("card_width", 190.0)),
            card_height=float(data.get("card_height", 110.0)),
            generation_spacing=float(data.get("generation_spacing", 190.0)),
            sibling_spacing=float(data.get("sibling_spacing", 230.0)),
        )


@dataclass
class TreeProject:
    project_version: int = 1
    people: list[Person] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    settings: TreeSettings = field(default_factory=TreeSettings)
    assets_manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_version": int(self.project_version),
            "people": [person.to_dict() for person in self.people],
            "relationships": [rel.to_dict() for rel in self.relationships],
            "settings": self.settings.to_dict(),
            "assets_manifest": dict(self.assets_manifest),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TreeProject:
        return cls(
            project_version=int(data.get("project_version", 1)),
            people=[Person.from_dict(item) for item in data.get("people", [])],
            relationships=[Relationship.from_dict(item) for item in data.get("relationships", [])],
            settings=TreeSettings.from_dict(data.get("settings")),
            assets_manifest=dict(data.get("assets_manifest") or {}),
        )

    def people_by_id(self) -> dict[str, Person]:
        return {person.id: person for person in self.people}

    def get_person(self, person_id: str) -> Person | None:
        return self.people_by_id().get(person_id)

    def remove_person(self, person_id: str) -> None:
        self.people = [person for person in self.people if person.id != person_id]
        self.relationships = [
            rel for rel in self.relationships if rel.from_id != person_id and rel.to_id != person_id
        ]
