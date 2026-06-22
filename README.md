# ComfyUI-EasyTrack

*By Claire Vlases*

**Inport a video, follow the objects in it, and get their positions out as data
you can actually use.**

This is a small set of ComfyUI nodes for students and artists who want to take
video, have the computer track objects in it, and
export *where each object was, in every frame*, as a point, a box, an outline,
or a combo of all of them, into a file you can open in other tools.


---

## 1. The big idea (read this first)

Imagine a video of a bee flying around a flower. You want the computer to watch
the bee and write down, for every single frame, *where the bee is*.

ComfyUI already includes a very good "detector" called **SAM3**. You give it a
video and a word ("bee"), and it finds the bee in every frame and even
remembers that the bee in frame 50 is the *same* bee as in frame 1. That
"same-bee-over-time" idea is called **tracking**, and SAM3 does it for you.

But there's a catch: when SAM3 finishes, it keeps its findings in a form meant
for *making pictures* (cutting the bee out, masking, compositing). It does
**not** give you the findings as plain *data*, which we as artists need for 
creative processes!

EasyTrack is the bridge that takes SAM3's findings and writes them down as usable data.


---

## 2. Words you'll need (mini glossary)

- **Frame**: one still picture from the video. A 10-second clip at 24 fps has
  240 frames.
- **Object / instance**: one thing being tracked (one specific bee). Each gets
  an **ID** (0, 1, 2, ...) that stays the same across frames.
- **Mask** — which exact pixels belong to the object. The most precise shape
  information there is.
- **Box (bounding box)**: the smallest rectangle that contains the object.
  Four numbers: `[x1, y1, x2, y2]`.
- **Point (centroid)**: the single middle point of the object. Two numbers:
  `[x, y]`.
- **Contour**: the outline traced around the object's real shape (the actual silhouette), stored as a list of edge points.
- **Track**: one object followed across many frames. A "tracks" file is a
  collection of these.
- **RLE**: "run-length encoding," a compact way to store a mask.

---

## 3. How the pieces connect

```
   your video ────────────────────────────────────────────┐
        │                                                  │
        ▼                                                  │
  (the native SAM3 chain)                                  │
   Load Checkpoint(sam3.1) ─model─┐                        │
   CLIP Text Encode("bee") ─text──┐                        │
                                  ▼                          │
                          SAM3 VideoTrack                    │
                                  │  (SAM3_TRACK_DATA)        │
                                  ▼                            │
   ┌──────────────── EasyTrack starts here ──────────────┐    │
   │     SAM3 Track → Tracks   ── TRACKS ──┬── Tracks Export (json/csv/svg)
   │                                       └── Tracks Preview ◄── (same video)
   └─────────────────────────────────────────────────────┘
```



---

## 4. The nodes, one at a time

### SAM3 Track → Tracks  *(the heart of it)*
**What it does:** turns SAM3's output into your data.
**How it works:** SAM3 hands over a bundle with the video size, the number of
frames, a stack of compressed masks (one per object per frame), and a
confidence score per object. This node walks through every frame and every
object, and for each one it works out:
- the **box** (smallest rectangle around the mask),
- the **point** (the mask's center),
- the **contour** (the mask's outline, traced with OpenCV),
- the **area** (how many pixels), and the **score**.
It bundles all of that into one tidy `TRACKS` object.
**Settings:** `label` (name the thing, e.g. "bee"), `store_contour`,
`store_mask_rle`, `contour_simplify` (see §6), `fps`.

### Tracks Preview  *("did it work?")*
**What it does:** draws the point, box, contour, and ID onto the frames so you
can *see* if the tracking is right.
**How it works:** for each object it picks a stable color and draws the chosen
shapes on each frame.
**Settings:** four on/off switches (`draw_boxes`, `draw_contours`,
`draw_points`, `draw_ids`) so you can show any combination. **`images` is
optional** — leave it unconnected and you get a black "debug canvas" at the
right size with just the shapes on it, handy for checking the geometry alone.

### Tracks Export  *(save it)*
**What it does:** writes everything to **one** file you can open elsewhere.
**Formats:** `json` (complete data), `csv` (a spreadsheet, one row per object
per frame), `svg` (a vector drawing — outlines, boxes, points — openable in
Illustrator, After Effects, Photoshop).
**Settings:** `include_point` / `include_box` / `include_contour` let you save
only the parts you want. It also outputs the file `path` so you know where it
landed.

### Tracks Load  *(open a saved file)*
**What it does:** reads a saved `tracks.json` back into a `TRACKS` object, so
you can preview or re-export without re-running slow SAM3.


---

## 5. The data you get out

Everything is keyed by **object → frame**, so "where was object 0 the whole
time?" is a direct lookup. Here's the JSON shape:

```jsonc
{
  "height": 540, "width": 960, "num_frames": 166, "fps": 24.0,
  "objects": {
    "0": {                          // object id 0
      "object_id": 0,
      "label": "bee",
      "score": 1.0,                 // SAM3's confidence in this object
      "frames": {
        "0": {                       // this object, at frame 0
          "bbox":   [x1, y1, x2, y2],          // BOX
          "point":  [cx, cy],                   // POINT (center)
          "contour":[[[x,y],[x,y], ...]],       // CONTOUR (real outline)
          "area":   437,                        // pixels covered
          "score":  1.0,
          "visible": true,
          "mask_rle": { "size":[h,w], "counts":"..." }  // exact mask (optional)
        },
        "1": { ... }
      }
    },
    "1": { ... }
  }
}
```

- **CSV** is the same information flattened: `frame, object_id, label, score,
  cx, cy, x1, y1, x2, y2, area, n_contour_pts`. Great for spreadsheets or
  driving keyframes in After Effects. (A full contour is too big for one
  spreadsheet cell, so CSV lists only the point count — use JSON/SVG if you
  need the actual outline.)
- **SVG** is a vector file where each frame is a layer group containing the
  outlines, boxes, and points, each tagged with its object id and label.

If an object isn't in a frame (it left, or was hidden), it simply has no entry
for that frame — that's how you know it was absent.

---

## 6. Two settings worth understanding

**`store_mask_rle` vs `store_contour` — are they the same?** No.
- **Contour** is a *simplified outline* — just the outer edge, smoothed. Small
  and perfect for vector tools, but it rounds off fine detail and ignores holes.
- **Mask RLE** is the *exact pixel truth* — every pixel, losslessly, including
  holes (a donut shape) and tiny nooks. Use it for precise area, re-creating
  the mask, or compositing.
Keep both, or turn `store_mask_rle` off for much smaller files when you only
need outlines.

**`contour_simplify`** is a quality dial for the outline. It's the allowed
"wiggle" as a fraction of the shape's perimeter. `0` keeps every edge pixel
(most detail, biggest files); `0.002` (default) gently removes redundant points;
higher values give fewer points but round off detail (a fringed wing can become
a smooth blob). Lower = more faithful, higher = smaller.

---

## 7. Installing it

1. Copy the `ComfyUI-EasyTrack` folder into `ComfyUI/custom_nodes/`.
2. Install the helper libraries into ComfyUI's Python:
   `pip install -r requirements.txt`
3. **Get the SAM3 weights — they do not download automatically.** Request
   access to `facebook/sam3` on HuggingFace, download the checkpoint, and place
   it where ComfyUI loads models. Your ComfyUI must be recent enough to include
   the built-in SAM3 nodes.
4. Restart ComfyUI (a full server restart, not just a browser refresh).

> Heads up: SAM3 is large and not fast. Test on short clips first.

---

## 8. Testing it (without waiting on SAM3)

There's a ready-made `examples/sample_tracks.json` with a fake "bee" and
"flower" so you can test the export/preview half with no model and no GPU.

1. **Does it load?** After restarting, search the node menu for "Tracks." If the
   nodes aren't there, check the ComfyUI console for an import error (usually a
   missing library).
2. **Export half:** put `sample_tracks.json` in your `input/` folder →
   **Tracks Load** (path `input/sample_tracks.json`) → **Tracks Export**. Run it
   for json, then csv, then svg. Open each file — you should see two objects.
3. **Draw half (debug canvas):** **Tracks Load** → **Tracks Preview** with
   `images` left unconnected. You'll see the bee and flower outlines on black,
   moving across 5 frames. Turn off every switch except `draw_contours` to see
   the outlines alone.
4. **The real thing:** build the SAM3 chain from §3 on a short clip, send it
   through **SAM3 Track → Tracks → Tracks Preview** (feeding in the same video).
   Watch the console for `[EasyTrack] SAM3TrackToTracks -> Tracks(N frames,
   WxH, K objects)` to confirm the counts match your clip.

Testing in this order means a later failure is easy to locate: if step 2–3 work
but step 4 doesn't, the problem is in the SAM3 wiring, not in these nodes.

---

## 9. The thinking behind the design

This section is the "why," so you can learn from the choices, not just use them.

**Why not reinvent the tracker?** ComfyUI already ships native SAM3 nodes that
detect and track better than anything we'd hand-write. The honest move was to
build only the *missing* piece — getting the data out — and lean on the native
nodes for the hard part. Good engineering is often knowing what *not* to build.

**Why a data type keyed by object → frame?** This is the core design decision.
ComfyUI's popular "SEGS" type (from the Impact Pack) stores detections
*per frame with no identity* — it's built for "find things in one image and
retouch them," and it has no concept of *time* or *which object is which*. A
tracker needs exactly those two things. So instead of bending SEGS to fit, we
made a type whose primary axes are **object identity** and **time**. The lesson:
pick your data structure to match the question you're asking ("where is this
specific object over time?"), not the tool you happen to have.

**Why use SAM3's video mode?** It remembers objects across frames and gives them
stable IDs for free. Doing that ourselves (matching objects frame to frame)
is exactly the wheel SAM3 already invented, so we don't.

**Why store both contour and mask?** They answer different questions — a light
outline for art tools, and an exact pixel mask for measurement. Forcing one to
do both jobs would compromise both, so we offer each and let you switch off what
you don't need.

**Why one consolidated file instead of one-per-frame?** A folder full of
per-frame files is painful to load and reason about. One file, nested by object
then frame, keeps a whole clip together and makes lookups trivial.

**Why is the data type independent of SAM3?** The `TRACKS` structure doesn't
mention SAM3 anywhere — it's just points/boxes/contours over time. That means a
different detector could fill it in later without changing anything downstream.
Keeping the data format separate from the tool that produces it is what lets a
project grow without rewrites.

---

## 10. Troubleshooting

- **Nodes don't appear in the menu** → an import failed; read the ComfyUI
  console (often a missing `pycocotools` or `opencv-python`).
- **A fix "didn't take"** → you didn't fully restart, or stale bytecode. Delete
  the folder's `__pycache__` and restart the server.
- **Preview shapes are offset / wrong size** → your preview image isn't the same
  size as the tracks. Use the same frames SAM3 saw, or leave `images` empty.
- **Nothing tracked / empty output** → the word didn't match the object; try a
  clearer prompt or lower `detection_threshold` on the SAM3 node.
- **Outline too jagged / file huge** → raise `contour_simplify`. Too blocky →
  lower it.

---

## 11. Notes confirmed against real data

`SAM3_TRACK_DATA` carries `orig_size` (height, width), `n_frames`, a
`packed_masks` stack shaped `[frames, objects, ...]`, and `scores` — one
confidence **per object** (e.g. `[1.0, 0.58, 0.55, 0.52]` for four objects).
Multiple objects are told apart by index; multiple *concepts* in one run aren't
split by class, so track one concept per run if you want clean per-class labels.

## 12. What could come next

- More export formats (MOT / COCO-video for analysis).
- A dense point-tracking stage (CoTracker / TAPIR) for sub-object motion.
- An alpha/transparent preview output for compositing.
