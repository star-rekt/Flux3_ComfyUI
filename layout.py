"""Build FLUX 3's caption + 0–1000 box table; no model or device code."""
import json
import math
import re

IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
HEADER = re.compile(r"(?:(?P<id>[A-Za-z][A-Za-z0-9_]*)\s+)?@(?P<reference>[A-Za-z][A-Za-z0-9_]*)")
REF_TAG = re.compile(r"<ref_image_(\d+)>")


def reference_order(reference_names, images):
    names = [name.strip() for name in reference_names.split(',') if name.strip()]
    keys = sorted((key for key, value in images.items() if value is not None),
                  key=lambda key: int(key.rsplit('_', 1)[1]))
    if len(names) != len(keys):
        raise ValueError(f"There are {len(keys)} connected images but {len(names)} reference names. "
                         "List one name per connected image, in socket order.")
    if len(set(names)) != len(names) or any(not IDENTIFIER.fullmatch(name) for name in names):
        raise ValueError('Reference names must be unique letters/numbers/underscores, starting with a letter.')
    # A tuple keeps different image sizes separate. Do not concatenate them into a batch or contact sheet.
    return tuple((name, images[key]) for name, key in zip(names, keys))


def canvas_box(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f'{label} must be [top, left, bottom, right] on the 0–1000 canvas.')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError(f'{label} must contain four finite numbers.')
    top, left, bottom, right = value
    if not (0 <= top < bottom <= 1000 and 0 <= left < right <= 1000):
        raise ValueError(f'{label} has invalid canvas coordinates: {value}')
    return list(value)


def description_parts(element, index):
    """Canvas descriptions use: optional_id @reference | target activity."""
    text = str(element.get('desc') or element.get('text') or '').strip()
    row_id = str(element.get('id') or f'element_{index + 1:02d}')
    reference = element.get('reference')
    if '|' in text:
        header, remainder = text.split('|', 1)
        header = header.strip()
        match = HEADER.fullmatch(header)
        if match:
            row_id = match.group('id') or row_id
            reference = match.group('reference')
            text = remainder.strip()
        elif IDENTIFIER.fullmatch(header):
            row_id, text = header, remainder.strip()
    if not IDENTIFIER.fullmatch(row_id):
        raise ValueError(f'Invalid element id {row_id!r}; use letters/numbers/underscores, starting with a letter.')
    return row_id, reference, text


def build_prompt(caption, mode, source_reference, elements, references):
    indices = {name: index for index, (name, _) in enumerate(references)}
    if mode not in ('edit_scene', 'layout'):
        raise ValueError(f'Unknown mode: {mode}')
    if mode == 'edit_scene' and source_reference not in indices:
        raise ValueError(f'Connect and name the source scene reference {source_reference!r}.')
    rows, phrases, seen = [], [], set()
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            raise ValueError(f'Element {index + 1} must be a JSON object.')
        row_id, reference, desc = description_parts(element, index)
        if row_id in seen:
            raise ValueError(f'Duplicate element id: {row_id}')
        seen.add(row_id)
        if reference:
            if reference not in indices:
                raise ValueError(f'Unknown reference @{reference}; connected names: {", ".join(indices)}')
            desc = f'Character design from <ref_image_{indices[reference]}>: {desc}'
        if mode == 'layout' and 'bbox' in element:
            row = {'id': row_id, 'bbox': canvas_box(element['bbox'], row_id), 'desc': desc}
        else:
            # Default edit: replace the scene subject at the same coordinates. Character identity is
            # described separately so this does not instruct the model to copy a reference's pose.
            bbox = element.get('bbox')
            origin = element.get('from', f'ref_image_{indices[source_reference]}' if mode == 'edit_scene' else 'target')
            if origin in indices:
                origin = f'ref_image_{indices[origin]}'
            if not re.fullmatch(r'ref_image_\d+|target', origin):
                raise ValueError(f'{row_id}: from must be a reference name, ref_image_N or target.')
            if origin != 'target' and int(origin.rsplit('_', 1)[1]) >= len(references):
                raise ValueError(f'{row_id}: source reference index is not connected.')
            src = element.get('src_bbox', bbox if origin != 'target' else None)
            tgt = element.get('tgt_bbox', bbox)
            src = canvas_box(src, f'{row_id}.src_bbox') if src is not None else None
            tgt = canvas_box(tgt, f'{row_id}.tgt_bbox') if tgt is not None else None
            if (src is None and tgt is None) or (origin == 'target') == (src is not None):
                raise ValueError(f'{row_id}: a reference edit needs src_bbox; a target-only addition needs tgt_bbox.')
            row = {'id': row_id, 'from': origin, 'src_bbox': src, 'tgt_bbox': tgt, 'desc': desc}
        rows.append(row)
        phrases.append(f'{desc} <{row_id}>.')
    text = caption.strip()
    if mode == 'edit_scene':
        text = f'The scene from <ref_image_{indices[source_reference]}> with the following subjects. {text}'
    text = ' '.join([text, *phrases]).strip()
    for tag in REF_TAG.findall(text):
        if int(tag) >= len(references):
            raise ValueError(f'The caption references ref_image_{tag}, which is not connected.')
    boxes_json = json.dumps(rows, ensure_ascii=False, indent=2)
    prompt = f'{text}\n{json.dumps(rows, ensure_ascii=False)}' if rows else text
    manifest = [{'name': name, 'index': index, 'tag': f'<ref_image_{index}>'}
                for index, (name, _) in enumerate(references)]
    plan = {'prompt': prompt, 'boxes': rows, 'references': references, 'reference_manifest': manifest}
    return prompt, plan, boxes_json, json.dumps(manifest, ensure_ascii=False, indent=2)


def prepare(caption, mode, source_reference, reference_names, boxes_json, elements=None, images=None):
    references = reference_order(reference_names, images or {})
    # Connected canvas output is authoritative, including an intentionally emptied canvas.
    if elements is None:
        elements = json.loads(boxes_json or '[]')
    if not isinstance(elements, list):
        raise ValueError('Elements must be a JSON list or the Create Bounding Boxes elements output.')
    return build_prompt(caption, mode, source_reference, elements, references)


def select_reference(plan, name):
    for index, (label, image) in enumerate(plan['references']):
        if label == name:
            return image, index
    raise ValueError(f'Unknown reference {name!r}; choose one of: ' +
                     ', '.join(label for label, _ in plan['references']))
