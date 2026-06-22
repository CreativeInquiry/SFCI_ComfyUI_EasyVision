"""ComfyUI-EasyTrack — point/box/contour tracking data out of native SAM3, as json/csv/svg."""

from .nodes import (
    SAM3TrackToTracks,
    EasyTracksMerge,
    EasyTracksExport,
    EasyTracksLoad,
    EasyTracksPreview,
)

NODE_CLASS_MAPPINGS = {
    "SAM3TrackToTracks": SAM3TrackToTracks,
    "EasyTracksMerge": EasyTracksMerge,
    "EasyTracksExport": EasyTracksExport,
    "EasyTracksLoad": EasyTracksLoad,
    "EasyTracksPreview": EasyTracksPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SAM3TrackToTracks": "SAM3 Track \u2192 Tracks",
    "EasyTracksMerge": "Tracks Merge (collate batches)",
    "EasyTracksExport": "Tracks Export (json/csv/svg)",
    "EasyTracksLoad": "Tracks Load (JSON)",
    "EasyTracksPreview": "Tracks Preview",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]