"""Model predictions do not depend on Observation or storage."""
import math
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Prediction:
    label: str
    class_id: int
    score: float

    def __post_init__(self):
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("prediction label is required")
        if type(self.class_id) is not int or self.class_id < 0:
            raise ValueError("prediction class_id must be non-negative integer")
        if isinstance(self.score, bool) or not math.isfinite(self.score) or not 0 <= self.score <= 1:
            raise ValueError("prediction score must be finite and between 0 and 1")


class VisionModel(Protocol):
    producer_ref: str
    taxonomy: str

    def predict(self, image_bytes: bytes) -> Prediction: ...
