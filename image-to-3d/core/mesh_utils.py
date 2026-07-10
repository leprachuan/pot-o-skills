"""Mesh post-processing and format conversion utilities."""

import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("image-to-3d.mesh_utils")


def get_mesh_metadata(mesh_path: str) -> dict:
    """Extract metadata from a mesh file using trimesh."""
    try:
        import trimesh

        mesh = trimesh.load(mesh_path)

        if isinstance(mesh, trimesh.Scene):
            # Scene with multiple meshes
            total_vertices = sum(g.vertices.shape[0] for g in mesh.geometry.values() if hasattr(g, "vertices"))
            total_faces = sum(g.faces.shape[0] for g in mesh.geometry.values() if hasattr(g, "faces"))
            bounds = mesh.bounds if mesh.bounds is not None else [[0, 0, 0], [0, 0, 0]]
        else:
            total_vertices = mesh.vertices.shape[0]
            total_faces = mesh.faces.shape[0]
            bounds = mesh.bounds.tolist()

        file_size = os.path.getsize(mesh_path)

        return {
            "vertices": total_vertices,
            "faces": total_faces,
            "file_size_bytes": file_size,
            "bounding_box": {
                "min": bounds[0] if isinstance(bounds[0], list) else bounds[0].tolist(),
                "max": bounds[1] if isinstance(bounds[1], list) else bounds[1].tolist(),
            },
        }
    except ImportError:
        # trimesh not available, return basic info
        return {
            "vertices": -1,
            "faces": -1,
            "file_size_bytes": os.path.getsize(mesh_path) if os.path.exists(mesh_path) else 0,
        }
    except Exception as e:
        logger.warning(f"Could not extract mesh metadata: {e}")
        return {
            "vertices": -1,
            "faces": -1,
            "file_size_bytes": os.path.getsize(mesh_path) if os.path.exists(mesh_path) else 0,
            "error": str(e),
        }


def convert_mesh_format(input_path: str, output_format: str, output_path: Optional[str] = None) -> str:
    """Convert a mesh file between formats (GLB, OBJ, STL, PLY)."""
    try:
        import trimesh
    except ImportError:
        raise RuntimeError("trimesh is required for format conversion. Install with: pip install trimesh")

    mesh = trimesh.load(input_path)

    if output_path is None:
        stem = Path(input_path).stem
        output_dir = str(Path(input_path).parent)
        output_path = os.path.join(output_dir, f"{stem}.{output_format}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    format_map = {
        "glb": "glb",
        "gltf": "gltf",
        "obj": "obj",
        "stl": "stl",
        "ply": "ply",
        "off": "off",
    }

    fmt = format_map.get(output_format.lower())
    if fmt is None:
        raise ValueError(f"Unsupported format: {output_format}. Supported: {list(format_map.keys())}")

    if isinstance(mesh, trimesh.Scene):
        mesh.export(output_path, file_type=fmt)
    else:
        mesh.export(output_path, file_type=fmt)

    logger.info(f"Converted {input_path} → {output_path} ({fmt})")
    return output_path
