"""CPU-compatible shim for torchmcubes using PyMCubes.

torchmcubes requires CUDA to compile. This shim provides the same
marching_cubes interface using the pure-CPU PyMCubes library instead.
"""

import mcubes
import torch
import numpy as np


def marching_cubes(volume, threshold=0.0):
    """Run marching cubes on a 3D volume tensor.

    Args:
        volume: 3D torch.FloatTensor (NxNxN density field).
        threshold: Isosurface threshold value.

    Returns:
        Tuple of (vertices, faces) as torch tensors.
    """
    if isinstance(volume, torch.Tensor):
        vol_np = volume.detach().cpu().numpy()
    else:
        vol_np = np.asarray(volume)

    vertices, triangles = mcubes.marching_cubes(vol_np, threshold)
    return torch.FloatTensor(vertices), torch.LongTensor(triangles)
