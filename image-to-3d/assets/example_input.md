# Example: Converting the Snorty Foam Mascot

The Snorty foam mascot images in `/opt/n8n-copilot-shim/` are perfect test inputs
for the image-to-3D skill.

## Available Snorty Images

```
snorty_final.png          - Clean final render
snorty_final_clean.png    - Clean version
snorty_front.png          - Front view
snorty_back.png           - Back view
snorty_v1.png through snorty_v13.png  - Various iterations
```

## Example Conversion

```python
import sys
sys.path.insert(0, '/opt/skills/image-to-3d/claude/implementation')
from image_to_3d import ImageTo3D

converter = ImageTo3D()

# Best single-view result
result = converter.convert(
    image="/opt/n8n-copilot-shim/snorty_final_clean.png",
    output_format="glb",
    quality="standard",
    preview=True
)

print(f"Snorty 3D model: {result['model_path']}")
print(f"Vertices: {result['metadata']['vertices']}")
print(f"Time: {result['inference_time_ms']}ms")
```

## Tips for Best Results

1. **Use the cleanest image** — `snorty_final_clean.png` has the best background
2. **Front view works best** — Single-view reconstruction works best with front-facing images
3. **Higher quality for detail** — Use `quality="high"` for the foam texture detail
4. **STL for 3D printing** — Use `output_format="stl"` to print your own Snorty!

## Expected Output

- GLB file (~5-15MB) with textured mesh
- Approximately 30,000-80,000 faces
- 1024x1024 texture resolution (standard quality)
- Auto-opens in 3D Canvas at http://localhost:18794
