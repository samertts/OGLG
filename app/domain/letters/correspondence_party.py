from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CorrespondenceParty:
    id: str
    name: str
    department: str
    title: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""

    @property
    def display_name(self) -> str:
        if self.title:
            return f"{self.title} {self.name}"
        return self.name

    @property
    def full_department_path(self) -> str:
        if self.title:
            return f"{self.department} / {self.title}"
        return self.department
