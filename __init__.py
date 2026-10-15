import json

from comfy_api.latest import ComfyExtension, io
from comfy_extras.nodes_flux import Flux3LayoutPrompt


class Flux3BoxPrompt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Flux3BoxPrompt",
            display_name="FLUX 3 Layout Prompt",
            category="FLUX 3",
            description="Combine a scene prompt and bounding boxes using ComfyUI's native FLUX 3 layout formatter.",
            inputs=[
                io.String.Input("prompt", multiline=True, default="",
                                tooltip="Describe the scene. Cite boxes as <obj_1>, <obj_2>, etc."),
                io.Array.Input("elements", optional=True,
                               tooltip="Connect the elements output from Create Bounding Boxes."),
                io.String.Input("boxes_json", multiline=True, default="[]",
                                tooltip="Optional box list when no canvas is connected. Each row needs bbox and desc. Coordinates: [top, left, bottom, right], 0–1000."),
            ],
            outputs=[io.String.Output(display_name="prompt")],
        )

    @classmethod
    def execute(cls, prompt, elements=None, boxes_json="[]"):
        if elements is None:
            elements = json.loads(boxes_json or "[]")
        if not isinstance(elements, list):
            raise ValueError("Bounding boxes must be a JSON list or the elements output from Create Bounding Boxes.")
        return Flux3LayoutPrompt.execute(prompt, elements)


class Flux3LayoutExtension(ComfyExtension):
    async def get_node_list(self):
        return [Flux3BoxPrompt]


async def comfy_entrypoint():
    return Flux3LayoutExtension()
