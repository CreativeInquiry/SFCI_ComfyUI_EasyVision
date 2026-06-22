# ComfyUI-EasyTrack

Pull **point + box + contour** tracking data out of ComfyUI's native SAM3
video tracking, as one consolidated **JSON / CSV / SVG** file you can import
into other tools.

ComfyUI's native SAM3 nodes (`SAM3_Detect`, `SAM3_VideoTrack`, ...) output a
`SAM3_TRACK_DATA` object built for masks/compositing. They give you no way to
get the tracking *data* out. This pack does.

## Graph

```
LoadVideo ───IMAGE───────────────────────────────┐
Checkpoint(sam3.1) ─MODEL─┐                       │
CLIPTextEncode("bee") ─COND─┐                      │
                            ▼                       │
                     SAM3_VideoTrack                │
                            │ SAM3_TRACK_DATA       │
                            ▼                        │
                   SAM3 Track → Tracks ──TRACKS──┬─> Tracks Export (json/csv/svg)
                                                 └─> Tracks Preview ◄── IMAGE
```

## Nodes

| Node | In → Out | Purpose |
|---|---|---|
| **SAM3 Track → Tracks** | `SAM3_TRACK_DATA` → `TRACKS` | Per object per frame: centroid **point**, **bbox**, **contour** polygon(s), area, score, optional mask. |
| **Tracks Merge** | `TRACKS`+`TRACKS` → `TRACKS` | Collate chunked batches into one (append frames or overlay). Chain for >2. |
| **Tracks Export** | `TRACKS` → file | One consolidated `json`, `csv`, or `svg`. |
| **Tracks Load** | path → `TRACKS` | Reload exported JSON. |
| **Tracks Preview** | `IMAGE`+`TRACKS` → `IMAGE` | Draw point/box/contour/id to verify. |

## What you get out — three forms

**JSON** (full fidelity, one file, nested object→frame):

```jsonc
{ "height":540, "width":960, "num_frames":166, "fps":24.0,
  "objects": {
    "0": { "object_id":0, "label":"bee", "score":1.0,
      "frames": {
        "0": { "bbox":[x1,y1,x2,y2],          // BOX
               "point":[cx,cy],                // POINT (centroid)
               "contour":[[[x,y],[x,y],...]],  // CONTOUR outline polygon(s)
               "area":437, "score":1.0, "visible":true,
               "mask_rle":{...} },             // optional, full mask
        "1": { ... } } } } }
```

**CSV** (one row per object per frame — drop into spreadsheets / After Effects scripts):

```
frame,object_id,label,score,cx,cy,x1,y1,x2,y2,area,n_contour_pts
0,0,bee,1.0,40.0,30.0,29,19,52,42,437,24
```

**SVG** (vector — open in Illustrator / After Effects / Photoshop; one file,
each frame is a `<g>` layer with `<polygon>` contours, `<rect>` boxes, `<circle>`
points, each tagged with `data-id` / `data-label`).

## Import targets

- **Illustrator / Affinity / Figma**: open the SVG; each frame is a layer group.
- **After Effects**: CSV → keyframes via a script, or place the SVG.
- **Photoshop**: place the SVG (contours come in as paths/shape layers).
- **Anything code-driven** (web, d3, Processing, Blender, Houdini): the JSON.

Tune size with the adapter: `contour_simplify` (Douglas-Peucker, fraction of
perimeter) thins polygons; turn off `store_mask_rle` for a much smaller file
when you only need point/box/contour.

## Install

1. Copy into `ComfyUI/custom_nodes/`, then `pip install -r requirements.txt`.
2. ComfyUI must be recent enough to have native SAM3 nodes (PR #13408) and the
   `sam3.1` checkpoint.
3. Restart ComfyUI.

## Notes (confirmed against real track_data)

- `orig_size` = (H, W); `scores` is one confidence **per object**
  (e.g. `[1.0, 0.58, 0.55, 0.52]` for 4 objects); `packed_masks` is
  `[n_frames, n_objects, ...]`, unpacked + resized to full frame internally.
- Multi-object identity is by object index. Multiple *concepts* in one run
  aren't separated by class — one `label` covers all; track one concept per run
  for clean per-class labels.