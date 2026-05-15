import sys
import os
import argparse
import json


def cmd_build(args):
    from .aml import AMLModel
    from .builder import build_aml

    model = AMLModel.load(args.file)
    out_dir = args.out or os.path.dirname(os.path.abspath(args.file))
    build_aml(model, output_dir=out_dir, draw=not args.nodraw, exports=not args.noexport)


def cmd_view(args):
    from .aml import AMLModel
    from .viewer import render_html

    model = AMLModel.load(args.file)
    out = args.out or None
    render_html(model, out_path=out, open_browser=True)


def cmd_validate(args):
    from .aml import AMLModel

    model = AMLModel.load(args.file)
    print(model.summary())
    errs = model.validate()
    if not errs:
        print('\nOK — no errors.')
    else:
        print(f'\n{len(errs)} error(s) found.')
        sys.exit(1)


def cmd_ai(args):
    from .aml import AMLModel
    from . import ai

    key = args.key or os.environ.get('OPENROUTER_API_KEY', '')
    if not key:
        print('Error: set OPENROUTER_API_KEY or pass --key')
        sys.exit(1)

    model = None
    if args.image:
        model = ai.from_image(args.image, prompt=args.prompt or 'Generate a 3D model from this sketch.', api_key=key)
    elif args.pdf:
        model = ai.from_pdf(args.pdf, prompt=args.prompt or 'Generate a 3D model from this technical drawing.', api_key=key)
    else:
        if not args.prompt:
            print('Error: provide --prompt, --image, or --pdf')
            sys.exit(1)
        model = ai.from_text(args.prompt, api_key=key)

    out = args.out or f'{model.name}.aml.json'
    model.save(out)
    print(f'Saved: {out}')
    print(model.summary())


def cmd_refine(args):
    from .aml import AMLModel
    from . import ai

    key = args.key or os.environ.get('OPENROUTER_API_KEY', '')
    model = AMLModel.load(args.file)
    refined = ai.refine(model, args.feedback, api_key=key)
    out = args.out or args.file
    refined.save(out)
    print(f'Saved: {out}')
    print(refined.summary())


def main():
    parser = argparse.ArgumentParser(prog='architect', description='Architect 3D platform')
    sub = parser.add_subparsers(dest='cmd')

    p_build = sub.add_parser('build', help='Build AML model to STEP+STL+SVG')
    p_build.add_argument('file')
    p_build.add_argument('--out', help='Output directory')
    p_build.add_argument('--nodraw', action='store_true')
    p_build.add_argument('--noexport', action='store_true')

    p_view = sub.add_parser('view', help='Open interactive 3D viewer in browser')
    p_view.add_argument('file')
    p_view.add_argument('--out', help='Save HTML to path')

    p_val = sub.add_parser('validate', help='Validate AML file')
    p_val.add_argument('file')

    p_ai = sub.add_parser('ai', help='Generate AML from image/text via Claude')
    p_ai.add_argument('--prompt', help='Text description')
    p_ai.add_argument('--image', help='Path to sketch/photo (PNG, JPG, WEBP)')
    p_ai.add_argument('--pdf', help='Path to technical drawing PDF')
    p_ai.add_argument('--out', help='Output .aml.json path')
    p_ai.add_argument('--key', help='Anthropic API key')

    p_ref = sub.add_parser('refine', help='Refine existing AML model via AI')
    p_ref.add_argument('file')
    p_ref.add_argument('feedback')
    p_ref.add_argument('--out', help='Output path (overwrites input if omitted)')
    p_ref.add_argument('--key', help='Anthropic API key')

    args = parser.parse_args()

    if args.cmd == 'build':
        cmd_build(args)
    elif args.cmd == 'view':
        cmd_view(args)
    elif args.cmd == 'validate':
        cmd_validate(args)
    elif args.cmd == 'ai':
        cmd_ai(args)
    elif args.cmd == 'refine':
        cmd_refine(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
