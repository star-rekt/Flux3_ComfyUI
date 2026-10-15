# BC FLUX 3 box layout

Two custom nodes, using ComfyUI's existing **Create Bounding Boxes** canvas. No dependencies beyond ComfyUI, no model loading, downloads or core patches.

Open the supplied `bcink_flux3_layout_editor.json`. It has your BC ink scene, three separate character references and six editable activity boxes. You can queue this editor workflow to preview/export the prompt; it has **no sampler** and performs no inference.

1. Drag/resize boxes in **Create Bounding Boxes**. Canvas dimensions must match the base image; the example connects them automatically.
2. Edit each box's description. The format is `unique_id @reference_name | desired activity and appearance`. For example: `yeti_skier @yeti | A lanky yeti skiing downhill with two poles and both feet on skis.` IDs can use letters, digits and underscores, starting with a letter. Reference names come from the connected image order.
3. **BC FLUX 3 · Box Layout Prompt** outputs the complete scene caption with `<id>` citations and the official box JSON format. `edit_scene` uses each box as both source and destination in the base scene. `layout` emits generation boxes. It does not instruct the model to copy the character reference's original pose.
4. The reference manifest shows zero-based indices: scene=0, yeti=1, goat=2, bear=3 in the example. Keep this exact order in the actual FLUX 3 encoder. Each **Named Reference Image** selector exposes its image separately, without a batch or contact sheet.
5. Connect `prompt` and the four image selector outputs to the **official FLUX 3 conditioning workflow** after the ComfyUI update. These nodes do not encode images or replace the native model-specific conditioning node. Do not connect them to a FLUX 2 encoder.

Adding references: connect more image sockets on the layout node and update the comma-separated names to match socket order. Images remain separate and retain their sizes; the native FLUX 3 workflow owns reference resizing. Ten references maximum, as specified by the model. The `plan` output is a custom graph value, not a file containing images. No output-list expansion is used, so connecting references does not accidentally queue one generation per reference.

`boxes_json` is a fallback for API/manual use when the canvas is disconnected. It accepts official canvas-1000 rows, including `from`, `src_bbox` and `tgt_bbox` for advanced edits. A connected canvas takes priority, even when emptied. Editing descriptions and moving boxes do not require changing JSON.

Boxes guide position and scale; they are not hard masks and do not guarantee pose, anatomy or unchanged surroundings. This package does not apply your FLUX 2 BC LoRA to FLUX 3. INT8/MPS inference remains a separate compatibility check.

Source format: [BFL reference bbox implementation](https://github.com/black-forest-labs/flux-3-image-klein/blob/main/src/flux3/bbox.py). The reference CLI accepts fractional boxes and converts them; the **final caption table** used here is on the 0–1000 canvas. [ComfyUI model card](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy#prompting).
