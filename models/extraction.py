from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExtractionStep:
    name: str
    status: str
    reason: Optional[str] = None
    page: Optional[int] = None


@dataclass
class ExtractionAudit:
    steps: List[ExtractionStep] = field(default_factory=list)
    final_method: Optional[str] = None

    def add_step(
        self,
        name: str,
        status: str,
        *,
        reason: Optional[str] = None,
        page: Optional[int] = None,
    ) -> None:
        self.steps.append(ExtractionStep(name=name, status=status, reason=reason, page=page))
        if status == "success":
            self.final_method = name
