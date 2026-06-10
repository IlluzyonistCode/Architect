import os
from build123d import *
from build123d import scale as b123d_scale
from datetime import date

def _project_safe(part, eye, up, look_at, origin_x, origin_y, sf):
    try:
        vis, hid = part.project_to_viewport(eye, up, look_at=look_at)
        vis_s = b123d_scale(vis, sf)
        hid_s = b123d_scale(hid, sf)
        vis_out = ShapeList([s.locate(Location((origin_x, origin_y, 0))) for s in vis_s])
        hid_out = ShapeList([s.locate(Location((origin_x, origin_y, 0))) for s in hid_s])

        return vis_out, hid_out
    except Exception as e:
        print(f'    projection error: {e}')

        return ShapeList(), ShapeList()

def export_drawing(part, out_path, title, subtitle, number, model_h,
                   drawing_scale=0.65, iso_scale_factor=0.7, spacing=45):

    print('  Creating border...')

    border = TechnicalDrawing(
        title=title,
        sub_title=subtitle,
        page_size=PageSize.A1,
        designed_by='GOST 2.305-2008',
        design_date=date.today(),
        drawing_number=number,
        sheet_number=1,
        drawing_scale=1
    )

    page = border.bounding_box().size
    margin = 20

    bmin = border.bounding_box().min
    bmax = border.bounding_box().max

    ix_min = bmin.X + margin
    ix_max = bmax.X - margin
    iy_min = bmin.Y + margin
    iy_max = bmax.Y - margin

    iw = ix_max - ix_min
    ih = iy_max - iy_min

    ds = drawing_scale
    iso_s = ds * iso_scale_factor

    bbox = part.bounding_box()
    pw = (bbox.max.X - bbox.min.X) * ds
    ph = model_h * ds

    total_w3 = pw * 3 + spacing * 2
    sx = ix_min + (iw - total_w3) / 2
    top_y = iy_max - ph - 40

    vfx = sx + pw / 2
    vfy = top_y + ph / 2

    vtx = sx + pw + spacing + pw / 2
    vty = top_y + ph / 2

    vrx = sx + pw * 2 + spacing * 2 + pw / 2
    vry = top_y + ph / 2

    iso_w = max(bbox.max.X - bbox.min.X,
                bbox.max.Y - bbox.min.Y,
                model_h) * iso_s

    vix = ix_min + iso_w / 2 + 80
    viy = iy_min + iso_w / 2 + 60

    look = (0, 0, model_h / 2)

    print('  Front view...')

    vv_f, vh_f = _project_safe(part, (0, -5000, 0), (0, 0, 1), look, vfx, vfy, ds)

    print('  Top view...')

    vv_t, vh_t = _project_safe(part, (0, 0, 5000), (-1, 0, 0), look, vtx, vty, ds)

    print('  Right view...')

    vv_r, vh_r = _project_safe(part, (5000, 0, 0), (0, 0, 1), look, vrx, vry, ds)

    print('  Isometric view...')
    
    vv_i, vh_i = _project_safe(part, (3000, -3000, 2500), (0, 0, 1), look, vix, viy, iso_s)

    all_vis = vv_f + vv_t + vv_r + vv_i
    all_hid = vh_f + vh_t + vh_r + vh_i

    print(f'  Lines: {len(all_vis)} visible, {len(all_hid)} hidden')

    exporter = ExportSVG(unit=Unit.MM, scale=1.0)
    exporter.add_layer('Visible', line_color=Color(0, 0, 0))
    exporter.add_layer('Hidden', line_color=Color(0.3, 0.3, 0.3), line_type=LineType.ISO_DOT)
    exporter.add_shape(all_vis, layer='Visible')
    exporter.add_shape(all_hid, layer='Hidden')
    exporter.add_shape(border, layer='Visible')
    exporter.write(out_path)

    with open(out_path, 'r') as f:
        svg = f.read()

    svg = svg.replace('<svg', '<svg style="stroke-linecap:round;stroke-linejoin:round"')
    svg = svg.replace('stroke="#000000"', 'stroke="#000000" stroke-width="2.5"')
    svg = svg.replace('stroke="#4c4c4c"', 'stroke="#4c4c4c" stroke-width="1.2" stroke-dasharray="4,4"')
    svg = svg.replace('stroke="#808080"', 'stroke="#555555" stroke-width="1.2" stroke-dasharray="4,4"')

    with open(out_path, 'w') as f:
        f.write(svg)

    print(f'  Saved: {out_path}')
