---
name: 3d-modeling
description: >
  3D modeling canvas for agents. Use when you need to visualize 3D objects, primitives, or compound
  shapes in a browser canvas. The agent describes scenes with JSON (primitives, positions, materials),
  the viewer renders them via Three.js with orbit controls, and the user can export STL/OBJ/GLB for
  3D printing or CAD workflows. Server auto-starts on first use on port 18794.
metadata:
  keywords: [3d, modeling, cad, stl, obj, gltf, glb, threejs, primitives, render, export, 3dprint]
  port: 18794
  exports: [stl, obj, glb]
---

# 3D Modeling Canvas Skill 🧊

Give any agent a live 3D workspace. Describe primitives and compound shapes in JSON, and they appear
instantly in the browser — ready to rotate, inspect, and export for 3D printing or CAD workflows.

## When to Use

| Trigger | Example |
|---|---|
| User wants to visualize a 3D object or shape | "Show me a gear shape in 3D" |
| Generating models for 3D printing | "Create an STL of a mounting bracket" |
| Visualizing spatial layouts | "Show this rack mount in 3D" |
| Exploring primitive combinations | "Build a house from primitives" |
| Exporting for CAD use | "Generate the OBJ file for this model" |

## Quick Start

```python
import sys
sys.path.insert(0, '/opt/skills/3d-modeling/claude/implementation')
from modeling3d import Canvas3D

c = Canvas3D()          # auto-generates session ID; auto-starts server
c.open()                # opens http://localhost:18794?session=<id> in browser

# Render a simple scene
c.render_scene({
    "title": "My Model",
    "objects": [
        {"type": "box", "width": 10, "height": 10, "depth": 10,
         "color": "#10b981", "position": [0, 5, 0]},
        {"type": "sphere", "radius": 5,
         "color": "#3b82f6", "position": [15, 5, 0]},
    ],
    "grid": True,
})

# Wait for user to click a button (e.g., export trigger)
action = c.wait_for_action(timeout=300)
```

## API Reference

```python
c = Canvas3D(session_id=None)       # auto-generates session ID; starts server

c.open()                            # open browser tab
c.render_scene(scene: dict)         # full scene replace
c.add_object(obj: dict)             # append one object to scene
c.transform(obj_id, position=None, rotation=None, scale=None)  # move/rotate/scale
c.set_camera(position, target=None) # reposition camera
c.clear()                           # remove all objects
c.set_title(title: str)             # update scene title
action = c.wait_for_action(timeout=60)   # block until user clicks button
```

`wait_for_action` returns:
```python
{"type": "action", "action_id": "export_stl", "data": {...}, "session_id": "...", "timestamp": "..."}
# or on timeout:
{"type": "timeout"}
```

---

## Scene JSON Format

```python
scene = {
    "title": "Scene Name",           # optional header
    "background": "#0a0e1a",         # hex color (default: dark)
    "grid": True,                    # show grid helper (default: True)
    "axes": False,                   # show axes helper (default: False)
    "autoRotate": False,             # auto-rotate camera (default: False)
    "camera": {
        "position": [50, 30, 50],    # x, y, z
        "target":   [0, 0, 0],       # look-at point
    },
    "objects": [ ... ],              # see Object Types below
}
```

---

## Object Types

### Box
```python
{"type": "box", "id": "mybox",
 "width": 10, "height": 10, "depth": 10,
 "color": "#10b981", "wireframe": False,
 "position": [0, 5, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1]}
```

### Sphere
```python
{"type": "sphere", "id": "ball",
 "radius": 5, "widthSegments": 32, "heightSegments": 16,
 "color": "#3b82f6",
 "position": [15, 5, 0]}
```

### Cylinder
```python
{"type": "cylinder", "id": "tube",
 "radiusTop": 3, "radiusBottom": 5, "height": 20,
 "radialSegments": 32,
 "color": "#f59e0b",
 "position": [0, 10, 0]}
```

### Cone
```python
{"type": "cone", "id": "peak",
 "radius": 5, "height": 15, "radialSegments": 32,
 "color": "#ef4444",
 "position": [0, 7.5, 0]}
```

### Torus (ring / donut)
```python
{"type": "torus", "id": "ring",
 "radius": 8, "tube": 2, "radialSegments": 16, "tubularSegments": 100,
 "color": "#8b5cf6",
 "position": [0, 8, 0]}
```

### Torus Knot
```python
{"type": "torus_knot", "id": "knot",
 "radius": 6, "tube": 1.5, "p": 2, "q": 3,
 "color": "#f97316",
 "position": [0, 6, 0]}
```

### Plane (flat surface)
```python
{"type": "plane", "id": "floor",
 "width": 100, "height": 100,
 "color": "#374151",
 "rotation": [-90, 0, 0],          # degrees; -90 to lay flat
 "position": [0, 0, 0]}
```

### Capsule
```python
{"type": "capsule", "id": "cap",
 "radius": 3, "length": 12, "capSegments": 4, "radialSegments": 8,
 "color": "#06b6d4",
 "position": [0, 9, 0]}
```

### Icosahedron (gem / crystal facets)
```python
{"type": "icosahedron", "id": "gem",
 "radius": 5, "detail": 0,
 "color": "#e879f9",
 "position": [0, 5, 0]}
```

### Octahedron
```python
{"type": "octahedron", "id": "oct",
 "radius": 5, "detail": 0,
 "color": "#fbbf24",
 "position": [0, 5, 0]}
```

### Dodecahedron
```python
{"type": "dodecahedron", "id": "dodec",
 "radius": 5, "detail": 0,
 "color": "#34d399",
 "position": [0, 5, 0]}
```

### Lathe (revolution surface)
```python
{"type": "lathe", "id": "vase",
 "points": [[0,0],[2,1],[3,4],[2,8],[3,10],[2,12],[0,13]],  # [x,y] profile
 "segments": 12,
 "color": "#f472b6",
 "position": [0, 0, 0]}
```

### Extrude (2D shape → 3D)
```python
{"type": "extrude", "id": "panel",
 "shape": [                         # polygon points [x, y]
     [0,0],[10,0],[10,5],[0,5]
 ],
 "depth": 3,
 "color": "#64748b",
 "position": [0, 0, 0]}
```

---

## Example: Compound Shape (Bracket)

```python
c.render_scene({
    "title": "Mounting Bracket",
    "objects": [
        # Base plate
        {"type": "box", "id": "base",
         "width": 80, "height": 4, "depth": 40,
         "color": "#10b981", "position": [0, 2, 0]},
        # Vertical wall
        {"type": "box", "id": "wall",
         "width": 80, "height": 30, "depth": 4,
         "color": "#10b981", "position": [0, 19, -18]},
        # Gussets
        {"type": "box", "id": "gusset_l",
         "width": 4, "height": 15, "depth": 18,
         "color": "#059669", "position": [-38, 11, -9],
         "rotation": [0, 0, 30]},
        {"type": "box", "id": "gusset_r",
         "width": 4, "height": 15, "depth": 18,
         "color": "#059669", "position": [38, 11, -9],
         "rotation": [0, 0, -30]},
    ],
    "grid": True,
    "camera": {"position": [80, 60, 80]},
})
```

---

## Export Formats

The viewer exposes **Download** buttons for:

| Button | Format | Use |
|---|---|---|
| **Download STL** | Binary STL | 3D printing (FDM, SLA, SLS) |
| **Download OBJ** | Wavefront OBJ | General 3D apps (Blender, Maya) |
| **Download GLB** | glTF Binary | Web / realtime, Blender, Unity, Unreal |

All exports include **all visible objects** merged into one file.

> **STEP/STP**: Full STEP export requires opencascade.js (large WASM bundle, ~15 MB).
> It is not included by default. For STEP, export GLB and convert offline with
> `FreeCAD`, `Blender + STEPper plugin`, or `Open CASCADE CLI`.

---

## Agent-triggered Exports

```python
# Option 1 — open canvas and let user click export buttons
c.open()
action = c.wait_for_action(timeout=300)
print(f"User triggered: {action['action_id']}")   # e.g. "export_stl"

# Option 2 — trigger export programmatically (downloads in browser)
c.export("stl")   # opens Save dialog in browser
c.export("obj")
c.export("glb")
```

---

## Server Details

- **Port:** 18794 (override: `MODELING3D_PORT` env var)
- **Host:** `localhost` by default (override: `MODELING3D_HOST` env var)
- **Auto-start:** `Canvas3D()` starts the server if not already running
- **Auto-stop:** Server stops after 30 minutes of no WebSocket activity
- **Install dependency:** `pip install websockets`
