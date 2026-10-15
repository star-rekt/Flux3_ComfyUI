from comfy_api.latest import ComfyExtension, io

from .layout import prepare, select_reference

Plan = io.Custom('BC_FLUX3_PLAN')


class BCFlux3LayoutPrompt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id='BCFlux3LayoutPrompt',
            display_name='BC FLUX 3 · Box Layout Prompt',
            category='BC ink/FLUX 3',
            description='Turn drawn boxes and named references into a FLUX 3 caption and box table. No inference.',
            inputs=[
                io.String.Input('caption', multiline=True, default='A sparse black ink illustration on white.'),
                io.Combo.Input('mode', options=['edit_scene', 'layout'], default='edit_scene'),
                io.String.Input('reference_names', default='scene,yeti,goat,bear',
                                tooltip='One name per connected image, in socket order. The manifest shows exact zero-based indices.'),
                io.String.Input('source_reference', default='scene'),
                io.String.Input('boxes_json', multiline=True, default='[]',
                                tooltip='Fallback canvas-1000 box list. Ignored when elements is connected.'),
                io.Array.Input('elements', optional=True,
                               tooltip='Connect Create Bounding Boxes → elements. Description syntax: skier @yeti | skiing downhill.'),
                io.Autogrow.Input('images', template=io.Autogrow.TemplatePrefix(
                    io.Image.Input('image'), prefix='image_', min=0, max=10),
                    tooltip='Separate images in order; do not use a contact sheet. FLUX 3 supports ten references.'),
            ],
            outputs=[io.String.Output(display_name='prompt'), Plan.Output(display_name='plan'),
                     io.String.Output(display_name='boxes_json'), io.String.Output(display_name='reference_manifest')],
        )

    @classmethod
    def execute(cls, caption, mode, reference_names, source_reference, boxes_json, elements=None, images=None):
        return io.NodeOutput(*prepare(caption, mode, source_reference, reference_names, boxes_json, elements, images))


class BCFlux3ReferenceImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id='BCFlux3ReferenceImage',
            display_name='BC FLUX 3 · Named Reference Image',
            category='BC ink/FLUX 3',
            description='Select one image from a layout plan by name, with its exact FLUX 3 reference index.',
            inputs=[Plan.Input('plan'), io.String.Input('reference_name', default='scene')],
            outputs=[io.Image.Output(display_name='image'), io.Int.Output(display_name='reference_index')],
        )

    @classmethod
    def execute(cls, plan, reference_name):
        return io.NodeOutput(*select_reference(plan, reference_name))


class BCFlux3LayoutExtension(ComfyExtension):
    async def get_node_list(self):
        return [BCFlux3LayoutPrompt, BCFlux3ReferenceImage]


async def comfy_entrypoint():
    return BCFlux3LayoutExtension()
