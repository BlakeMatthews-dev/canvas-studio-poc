"""Canvas Studio POC — trimmed engine.

Self-contained subset of the maistro-canvas engine, stripped of
maistro-core dependency and adapted for the book-maker POC spec.

Import surface:
    from server.engine.types import BookLayer, CanvasTier, ...
    from server.engine.layers import LayerKind, Anchor, Slot, WorldStyle, ...
    from server.engine.image_provider import generate_image, azure_image_edit, ...
    from server.engine.compositor import composite_scene

ADR cross-references: ADR-039 (layer model), ADR-040 (compositor),
ADR-041 (image provider), ADR-042 (personalisation), ADR-043 (world style).
"""

from .types import (
    EngineError,
    CanvasError,
    LayerNotFoundError,
    LayerLockedError,
    PromptBlockedError,
    RefineNoSourceError,
    UnknownLayerKindError,
    WorldStyleConflictError,
    PoseGeometryMismatchError,
    OcclusionCycleError,
    CanvasTier,
    LayerType,
    BlendMode,
    JobAction,
    JobStatus,
    TextConfig,
    BookLayer,
    validate_canvas_dimensions,
)
from .layers import (
    LayerKind,
    Anchor,
    Slot,
    Socket,
    OcclusionHint,
    Transform,
    GroundPlane,
    BackgroundComposition,
    FoundationFootprint,
    WheelAnchors,
    CharacterPose,
    PoseGeometry,
    POSE_GEOMETRY_FOR_KIND,
    PersonalizationSlot,
    ChildProfile,
    AssetSheet,
    AssetDefinition,
    AssetInstance,
    WorldStylePartial,
    WorldStyle,
    RenderStyle,
    StyleVolume,
    merge_world_style,
    layer_type_to_kind,
)

__all__ = [
    # types
    "EngineError",
    "CanvasError",
    "LayerNotFoundError",
    "LayerLockedError",
    "PromptBlockedError",
    "RefineNoSourceError",
    "UnknownLayerKindError",
    "WorldStyleConflictError",
    "PoseGeometryMismatchError",
    "OcclusionCycleError",
    "CanvasTier",
    "LayerType",
    "BlendMode",
    "JobAction",
    "JobStatus",
    "TextConfig",
    "BookLayer",
    "validate_canvas_dimensions",
    # layers
    "LayerKind",
    "Anchor",
    "Slot",
    "Socket",
    "OcclusionHint",
    "Transform",
    "GroundPlane",
    "BackgroundComposition",
    "FoundationFootprint",
    "WheelAnchors",
    "CharacterPose",
    "PoseGeometry",
    "POSE_GEOMETRY_FOR_KIND",
    "PersonalizationSlot",
    "ChildProfile",
    "AssetSheet",
    "AssetDefinition",
    "AssetInstance",
    "WorldStylePartial",
    "WorldStyle",
    "RenderStyle",
    "StyleVolume",
    "merge_world_style",
    "layer_type_to_kind",
]
