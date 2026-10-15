# FLUX 3 Layout Prompt

A general-purpose ComfyUI custom node for FLUX 3 bounding-box prompting. No character presets, style presets, image-reference sockets, dependencies or model loading.

Install this folder in your ComfyUI `custom_nodes` directory and restart ComfyUI. Search for **FLUX 3 Layout Prompt** under **FLUX 3**.

1. Add ComfyUI's **Create Bounding Boxes** node and draw boxes with descriptions. An image is not required by this custom node.
2. Connect the canvas's `elements` output to `elements`.
3. Enter a scene prompt. Refer to boxes as `<obj_1>`, `<obj_2>`, etc., in canvas order.
4. Connect the output prompt to your FLUX 3 text encoding path.

For example: `A dog <obj_1> beside a bicycle <obj_2> in a park.` Box descriptions can be `A sitting dog` and `A parked bicycle`.

Without a canvas, `boxes_json` accepts a list such as:

```json
[{"bbox": [200, 100, 800, 450], "desc": "A sitting dog"}]
```

Coordinates are `[top, left, bottom, right]` on the 0–1000 canvas. A connected canvas takes priority over JSON, including when the canvas is empty. Formatting delegates to ComfyUI's native FLUX 3 layout node, so this package requires a ComfyUI version with FLUX 3 support.

This node prepares a prompt; your normal model loaders, encoder and sampler perform generation. Boxes guide layout and are not hard masks. Any optional reference images belong in your model's conditioning workflow, separately from this node.
