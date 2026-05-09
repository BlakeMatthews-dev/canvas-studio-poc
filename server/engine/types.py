"""Canvas Studio POC engine types.

Self-contained — no maistro-core dependency.
Trimmed from maistro_canvas.types with POC-specific additions.

Key additions vs maistro_canvas/types.py:
  - EngineError replaces AgentError as the base exception
  - BookLayer: per-page layer carrying version history[], retry() + upgrade()
    methods that enforce the SPEC invariant:
    version_history_never_loses_images
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


# ─────────────────────────────────────────────────────────────────────
# Base error
# ─────────────────────────────────────────────────────────────────────


class EngineError(Exception):
    """Base exception for the book engine. Replaces maistro-core AgentError."""

    code: str = "ENGINE_ERROR"


# ─────────────────────────────────────────────────────────────────────
# Enums (from maistro_canvas.types, unchanged)
# ─────────────────────────────────────────────────────────────────────


class LayerType(StrEnum):
    BACKGROUND = "background"
    CHARACTER = "character"
    OBJECT = "object"
    TEXT = "text"


class BlendMode(StrEnum):
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    DARKEN = "darken"
    LIGHTEN = "lighten"


class JobAction(StrEnum):
    GENERATE = "generate"
    REFINE = "refine"
    REFERENCE = "reference"
    COMPOSITE = "composite"
    TEXT = "text"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CanvasTier(StrEnum):
    DRAFT = "draft"
    PROOF = "proof"


# ─────────────────────────────────────────────────────────────────────
# POC-specific: per-page layer with version history
# ─────────────────────────────────────────────────────────────────────


@dataclass
class BookLayer:
    """Per-page layer with version history.

    Mirrors the JS layer shape used by BookWorkspace.jsx.
    Enforces the SPEC invariant version_history_never_loses_images:
    the old image_url is always pushed to history[] before replacement.
    """

    name: str
    layer_type: str  # 'background' | 'character' | 'prop' | 'text'
    image_url: str | None = None
    prompt: str | None = None
    z_index: int = 0
    visible: bool = True
    quality: str = "draft"  # 'draft' | 'final'
    history: list[str] = field(default_factory=list)
    slot: dict[str, Any] | str | None = None  # {x,y,w,h} normalised or 'full_page'
    pose: dict[str, Any] | None = None
    face_mask: str | None = None
    head_region: dict[str, Any] | None = None

    def retry(self, new_url: str) -> "BookLayer":
        """Return a new layer with new_url active and old image pushed to history."""
        history = list(self.history)
        if self.image_url:
            history.append(self.image_url)
        return BookLayer(
            name=self.name,
            layer_type=self.layer_type,
            image_url=new_url,
            prompt=self.prompt,
            z_index=self.z_index,
            visible=self.visible,
            quality=self.quality,
            history=history,
            slot=self.slot,
            pose=self.pose,
            face_mask=self.face_mask,
            head_region=self.head_region,
        )

    def upgrade(self, new_url: str) -> "BookLayer":
        """Return a new layer upgraded to final quality; history preserved."""
        upgraded = self.retry(new_url)
        upgraded.quality = "final"
        return upgraded

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "layer_type": self.layer_type,
            "image_url": self.image_url,
            "prompt": self.prompt,
            "z_index": self.z_index,
            "visible": self.visible,
            "quality": self.quality,
            "history": self.history,
            "slot": self.slot,
            "pose": self.pose,
            "face_mask": self.face_mask,
            "head_region": self.head_region,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BookLayer":
        return cls(
            name=d.get("name", ""),
            layer_type=d.get("layer_type", "background"),
            image_url=d.get("image_url"),
            prompt=d.get("prompt"),
            z_index=d.get("z_index", 0),
            visible=d.get("visible", True),
            quality=d.get("quality", "draft"),
            history=list(d.get("history") or []),
            slot=d.get("slot"),
            pose=d.get("pose"),
            face_mask=d.get("face_mask"),
            head_region=d.get("head_region"),
        )


# ─────────────────────────────────────────────────────────────────────
# Value objects (from maistro_canvas.types)
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TextConfig:
    content: str
    font: str = "sans-serif"
    size: int = 48
    color: str = "#FFFFFF"
    weight: str = "normal"
    alignment: str = "center"
    shadow_color: str | None = None
    shadow_offset: tuple[int, int] = (2, 2)


@dataclass(frozen=True)
class ModelInfo:
    id: str
    display_name: str
    provider: str
    supports_generate: bool = True
    supports_refine: bool = False
    tier_class: str = "draft"
    cost_per_image_usd: float = 0.0
    is_free: bool = True


# ─────────────────────────────────────────────────────────────────────
# Domain errors (from maistro_canvas.types, base class swapped)
# ─────────────────────────────────────────────────────────────────────


class CanvasError(EngineError):
    code = "CANVAS_ERROR"


class CanvasNotFoundError(CanvasError):
    code = "CANVAS_NOT_FOUND"


class CanvasArchivedError(CanvasError):
    code = "CANVAS_ARCHIVED"


class CanvasHasLayersError(CanvasError):
    code = "CANVAS_HAS_LAYERS"


class LayerNotFoundError(CanvasError):
    code = "LAYER_NOT_FOUND"


class LayerLimitExceededError(CanvasError):
    code = "LAYER_LIMIT_EXCEEDED"


class LayerLockedError(CanvasError):
    code = "LAYER_LOCKED"


class DuplicateZIndexError(CanvasError):
    code = "DUPLICATE_Z_INDEX"


class IncompleteReorderError(CanvasError):
    code = "INCOMPLETE_REORDER"


class JobNotFoundError(CanvasError):
    code = "JOB_NOT_FOUND"


class JobInProgressError(CanvasError):
    code = "JOB_IN_PROGRESS"


class JobNotDoneError(CanvasError):
    code = "JOB_NOT_DONE"


class JobAlreadyTerminalError(CanvasError):
    code = "JOB_ALREADY_TERMINAL"


class TextLayerNoGenError(CanvasError):
    code = "TEXT_LAYER_NO_GEN"


class UnknownModelError(CanvasError):
    code = "UNKNOWN_MODEL"


class PromptBlockedError(CanvasError):
    code = "PROMPT_BLOCKED"


class RefineNoSourceError(CanvasError):
    code = "REFINE_NO_SOURCE"


class VariantIndexOutOfRangeError(CanvasError):
    code = "VARIANT_INDEX_OUT_OF_RANGE"


class UnsupportedFormatError(CanvasError):
    code = "UNSUPPORTED_FORMAT"


# Layer-model domain errors (ADR-039 §9)


class UnknownLayerKindError(CanvasError):
    code = "UNKNOWN_LAYER_KIND"


class MissingAnchorError(CanvasError):
    code = "MISSING_ANCHOR"


class MissingSocketError(CanvasError):
    code = "MISSING_SOCKET"


class OcclusionCycleError(CanvasError):
    code = "OCCLUSION_CYCLE"


class AssetSheetNotFoundError(CanvasError):
    code = "ASSET_SHEET_NOT_FOUND"


class AssetDefinitionNotFoundError(CanvasError):
    code = "ASSET_DEFINITION_NOT_FOUND"


class WorldStyleConflictError(CanvasError):
    code = "WORLD_STYLE_CONFLICT"


class SkinBindingError(CanvasError):
    code = "SKIN_BINDING_ERROR"


class PoseGeometryMismatchError(CanvasError):
    code = "POSE_GEOMETRY_MISMATCH"


# ─────────────────────────────────────────────────────────────────────
# Validation helpers
# ─────────────────────────────────────────────────────────────────────

_MIN_DIM = 64
_MAX_DIM = 8192
_VALID_EXPORT_FORMATS = frozenset({"png", "webp", "jpg", "jpeg"})
_MAX_REFERENCE_PHOTOS = 5


def validate_canvas_dimensions(width: int, height: int) -> None:
    for dim_name, dim_value in (("width", width), ("height", height)):
        if not (_MIN_DIM <= dim_value <= _MAX_DIM):
            msg = f"{dim_name} must be between {_MIN_DIM} and {_MAX_DIM}, got {dim_value}"
            raise ValueError(msg)
        if dim_value % 8 != 0:
            msg = f"{dim_name} must be divisible by 8, got {dim_value}"
            raise ValueError(msg)


def normalise_rotation(degrees: float) -> float:
    return degrees % 360.0
