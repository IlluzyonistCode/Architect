import json
import base64
import os
import urllib.request

from ..aml import AMLModel


OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_MODEL = 'qwen/qwen-2.5-72b-instruct'

SYSTEM_PROMPT = '''You are Architect AI — a 3D model generator.
Given a sketch, photo, description, or text prompt, you output a valid ArchitectML JSON model.

ArchitectML format:
{
  "name": "model_name",
  "width": 100,
  "depth": 100,
  "height": 100,
  "unit": "mm",
  "drawing_title": "TITLE",
  "drawing_subtitle": "subtitle",
  "drawing_number": "M.001.000",
  "primitives": [
    {
      "type": "box|cylinder|pipe|sphere|panel|roof|arch|grid|logo|text",
      "label": "human readable name",
      "x": 0, "y": 0, "z": 0,
      "w": 10, "d": 10, "h": 10,
      "radius": 5,
      "depth": 2,
      "rotate_x": 0, "rotate_y": 0, "rotate_z": 0,
      "face": "top|front|back|left|right|bottom",
      "svg": "path/to/logo.svg",
      "text": "TEXT",
      "font_size": 8,
      "rows": 3, "cols": 3, "spacing": 5,
      "subtract": false
    }
  ]
}

All dimensions in mm. Origin is center bottom of the model.
Z axis is up. Primitives stack on Z=0 floor.
subtract:true cuts the shape out of the model.
face determines which surface the primitive is oriented toward.

Return ONLY valid JSON. No markdown, no explanation, no code fences.'''


def _call(messages, api_key=None, model=None):
    key = api_key or os.environ.get('OPENROUTER_API_KEY', '')
    if not key:
        raise RuntimeError('No API key. Set OPENROUTER_API_KEY env var or pass api_key=')

    mdl = model or os.environ.get('ARCHITECT_MODEL', DEFAULT_MODEL)

    body = json.dumps({
        'model': mdl,
        'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages,
        'temperature': 0.3,
        'max_tokens': 4096,
    }).encode('utf-8')

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
            'HTTP-Referer': 'http://localhost',
            'X-Title': 'Architect',
        },
        method='POST',
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    if 'error' in data:
        raise RuntimeError(f"OpenRouter error: {data['error'].get('message', data['error'])}")

    return data['choices'][0]['message']['content']


def from_text(prompt, api_key=None, model=None):
    print('Architect AI: generating from text...')
    messages = [{'role': 'user', 'content': prompt}]
    raw = _call(messages, api_key, model)
    return _parse_response(raw)


def from_image(image_path, prompt='Generate a 3D model from this sketch.', api_key=None, model=None):
    print(f'Architect AI: generating from image: {image_path}')

    with open(image_path, 'rb') as f:
        img_data = base64.standard_b64encode(f.read()).decode('utf-8')

    ext = os.path.splitext(image_path)[1].lower()
    media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                   '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
    media_type = media_types.get(ext, 'image/png')

    messages = [{
        'role': 'user',
        'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:{media_type};base64,{img_data}'}},
            {'type': 'text', 'text': prompt},
        ]
    }]

    mdl = model or os.environ.get('ARCHITECT_MODEL', 'google/gemini-2.0-flash-001')
    raw = _call(messages, api_key, mdl)
    return _parse_response(raw)


def from_pdf(pdf_path, prompt='Generate a 3D model from this technical drawing.', api_key=None, model=None):
    print(f'Architect AI: generating from PDF: {pdf_path}')

    with open(pdf_path, 'rb') as f:
        pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')

    messages = [{
        'role': 'user',
        'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:application/pdf;base64,{pdf_data}'}},
            {'type': 'text', 'text': prompt},
        ]
    }]

    mdl = model or os.environ.get('ARCHITECT_MODEL', 'google/gemini-2.0-flash-001')
    raw = _call(messages, api_key, mdl)
    return _parse_response(raw)


def refine(model, feedback, api_key=None, ai_model=None):
    print('Architect AI: refining model...')
    messages = [{
        'role': 'user',
        'content': f'Current model:\n{model.to_json()}\n\nModify it: {feedback}'
    }]
    raw = _call(messages, api_key, ai_model)
    return _parse_response(raw)


def _parse_response(raw):
    text = raw.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

    data = json.loads(text)
    result = AMLModel.from_dict(data)

    errs = result.validate()
    if errs:
        print('Validation warnings:')
        for e in errs:
            print(f'  ! {e}')

    return result
