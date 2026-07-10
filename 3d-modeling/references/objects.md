# 3D Object Reference

Quick reference for all supported object types in the 3D Modeling Canvas skill.

## Primitives Cheatsheet

| Type | Required Params | Optional Params |
|---|---|---|
| `box` | — | width, height, depth, wireframe |
| `sphere` | — | radius, widthSegments, heightSegments |
| `cylinder` | — | radiusTop, radiusBottom, height, radialSegments |
| `cone` | — | radius, height, radialSegments |
| `torus` | — | radius, tube, radialSegments, tubularSegments |
| `torus_knot` | — | radius, tube, p, q, tubularSegments, radialSegments |
| `plane` | — | width, height |
| `capsule` | — | radius, length, capSegments, radialSegments |
| `icosahedron` | — | radius, detail |
| `octahedron` | — | radius, detail |
| `dodecahedron` | — | radius, detail |
| `tetrahedron` | — | radius, detail |
| `lathe` | points (array of [x,y]) | segments |
| `extrude` | shape (array of [x,y]) | depth, bevel |
| `ring` | — | innerRadius, outerRadius, thetaSegments |
| `tube` | path (array of [x,y,z]) | radius, tubularSegments, radialSegments |

## Common Object Properties

All objects support these common properties:

```python
{
  "type": "...",        # required: object type
  "id":   "...",        # optional: unique identifier
  "color": "#10b981",  # hex color (default: green)
  "wireframe": False,  # show edges only
  "opacity": 1.0,      # 0.0 = invisible, 1.0 = opaque
  "shininess": 60,     # Phong shininess (0-100+)
  "position": [x, y, z],   # world position (default: [0,0,0])
  "rotation": [x, y, z],   # rotation in degrees (default: [0,0,0])
  "scale":    [x, y, z],   # scale factors (default: [1,1,1])
}
```

## Common Presets

### Ground Plane
```python
{"type": "plane", "width": 200, "height": 200, "color": "#1a2a1a",
 "rotation": [-90, 0, 0], "position": [0, 0, 0]}
```

### Translucent Glass
```python
{"type": "box", "width": 20, "height": 20, "depth": 5,
 "color": "#3b82f6", "opacity": 0.4}
```

### Hollow Ring / Washer
```python
{"type": "torus", "radius": 10, "tube": 2, "color": "#6b7280"}
```

### Elongated Cylinder (Pipe/Rod)
```python
{"type": "cylinder", "radiusTop": 2, "radiusBottom": 2,
 "height": 50, "color": "#94a3b8"}
```

### Vase Profile (Lathe)
```python
{"type": "lathe", "segments": 24,
 "points": [[0,0],[1.5,1],[2.5,4],[2,8],[2.5,10],[1.5,12],[0,13]],
 "color": "#e879f9"}
```

### Extruded L-Bracket
```python
{"type": "extrude", "depth": 5,
 "shape": [[0,0],[20,0],[20,4],[4,4],[4,15],[0,15]],
 "color": "#10b981"}
```

## Color Palette (Glassmorphism Friendly)

| Name | Hex |
|---|---|
| Emerald (primary) | `#10b981` |
| Blue | `#3b82f6` |
| Purple | `#8b5cf6` |
| Amber | `#f59e0b` |
| Red | `#ef4444` |
| Cyan | `#06b6d4` |
| Pink | `#f472b6` |
| Orange | `#f97316` |
| Slate | `#64748b` |
| Dark green | `#059669` |

## Coordinate System

- **Y-axis is UP** (standard Three.js coordinate system)
- Positive X → right
- Positive Z → toward the viewer (front)
- Units are arbitrary — treat them as millimeters for 3D printing
- Grid is in the XZ plane at Y=0

## Tips for 3D Printing Prep

1. Position objects so they rest on Y=0 (the ground plane)
2. Use `height/2` as the Y position for boxes, cylinders, cones
3. Use `radius` as Y position for spheres
4. For complex shapes, build from multiple primitives stacked/combined
5. Export as STL for FDM/SLA printers
6. Export as OBJ or GLB to import into Blender for post-processing
