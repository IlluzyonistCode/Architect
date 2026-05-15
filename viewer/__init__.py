import json
import os
import webbrowser
import tempfile


_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Architect Viewer — {name}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box }}
body {{ background:#111; color:#eee; font-family:monospace; overflow:hidden }}
canvas {{ display:block }}
#ui {{
  position:fixed; top:16px; left:16px; z-index:10;
  background:rgba(0,0,0,.7); padding:12px 16px; border-radius:8px;
  border:1px solid #333; min-width:200px
}}
#ui h2 {{ font-size:13px; color:#7cf; margin-bottom:8px; letter-spacing:.05em }}
#ui p {{ font-size:11px; color:#888; margin:2px 0 }}
#ui .val {{ color:#eee }}
#controls {{
  position:fixed; bottom:16px; left:16px; z-index:10;
  background:rgba(0,0,0,.7); padding:10px 14px; border-radius:8px;
  border:1px solid #333; font-size:11px; color:#666
}}
#controls span {{ color:#aaa }}
</style>
</head>
<body>
<div id="ui">
  <h2>◈ {name}</h2>
  <p>Size: <span class="val">{w} × {d} × {h} {unit}</span></p>
  <p>Primitives: <span class="val">{pcount}</span></p>
  <p>Drawing: <span class="val">{drawing_number}</span></p>
</div>
<div id="controls">
  <span>LMB</span> rotate &nbsp; <span>RMB</span> pan &nbsp; <span>Scroll</span> zoom &nbsp; <span>R</span> reset
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const MODEL = {model_json};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111111);
scene.fog = new THREE.Fog(0x111111, 2000, 6000);

const W = window.innerWidth, H = window.innerHeight;
const camera = new THREE.PerspectiveCamera(45, W/H, 1, 10000);
camera.position.set(MODEL.width*2, -MODEL.depth*2.5, MODEL.height*2);
camera.up.set(0, 0, 1);
camera.lookAt(0, 0, MODEL.height/2);

const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setPixelRatio(devicePixelRatio);
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const sun = new THREE.DirectionalLight(0xffffff, 0.9);
sun.position.set(400, -300, 600);
sun.castShadow = true;
scene.add(sun);
const fill = new THREE.DirectionalLight(0x8899ff, 0.3);
fill.position.set(-400, 400, 200);
scene.add(fill);

const grid = new THREE.GridHelper(2000, 40, 0x333333, 0x222222);
grid.rotation.x = Math.PI/2;
scene.add(grid);

const axesHelper = new THREE.AxesHelper(80);
scene.add(axesHelper);

const COLORS = [
  0x4488cc, 0x44aacc, 0x44ccaa, 0x88cc44,
  0xcc8844, 0xcc4488, 0x8844cc, 0x44cc88
];
const MAT_WIRE = new THREE.MeshStandardMaterial({{
  color: 0x4488cc, roughness:0.4, metalness:0.1,
  transparent:true, opacity:0.82, side:THREE.DoubleSide
}});

const group = new THREE.Group();

MODEL.primitives.forEach((p, i) => {{
  let geo = null;
  const t = p.type;

  if (t === 'box' || t === 'panel' || t === 'roof' || t === 'grid') {{
    geo = new THREE.BoxGeometry(p.w || 10, p.d || 10, p.h || 10);
  }} else if (t === 'cylinder' || t === 'pipe') {{
    geo = new THREE.CylinderGeometry(p.radius||5, p.radius||5, p.h||10, 32);
  }} else if (t === 'sphere') {{
    geo = new THREE.SphereGeometry(p.radius||5, 32, 32);
  }} else if (t === 'arch') {{
    const shape = new THREE.Shape();
    const or = (p.w||20)/2, ir = or - (p.depth||3);
    shape.absarc(0, 0, or, 0, Math.PI, false);
    shape.lineTo(-ir, 0);
    shape.absarc(0, 0, ir, Math.PI, 0, true);
    shape.lineTo(or, 0);
    geo = new THREE.ExtrudeGeometry(shape, {{depth: p.d||10, bevelEnabled:false}});
  }} else if (t === 'logo' || t === 'text') {{
    geo = new THREE.BoxGeometry(p.w||20, p.depth||2, p.h||20);
  }}

  if (!geo) return;

  const mat = new THREE.MeshStandardMaterial({{
    color: p.subtract ? 0xff4444 : COLORS[i % COLORS.length],
    roughness: 0.4, metalness: 0.15,
    transparent: p.subtract,
    opacity: p.subtract ? 0.3 : 0.85,
    side: THREE.DoubleSide,
    wireframe: false,
  }});

  const mesh = new THREE.Mesh(geo, mat);

  if (t === 'cylinder' || t === 'pipe') {{
    mesh.rotation.x = Math.PI/2;
    mesh.position.set(p.x||0, p.y||0, (p.z||0) + (p.h||10)/2);
  }} else {{
    mesh.position.set(p.x||0, p.y||0, (p.z||0) + (p.h||p.depth||10)/2);
  }}

  if (p.rotate_x) mesh.rotation.x += p.rotate_x * Math.PI/180;
  if (p.rotate_y) mesh.rotation.y += p.rotate_y * Math.PI/180;
  if (p.rotate_z) mesh.rotation.z += p.rotate_z * Math.PI/180;

  const edges = new THREE.EdgesGeometry(geo, 15);
  const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{color:0xffffff, opacity:0.15, transparent:true}}));
  line.position.copy(mesh.position);
  line.rotation.copy(mesh.rotation);

  group.add(mesh);
  group.add(line);
}});

group.rotation.x = 0;
scene.add(group);

let isDragging = false, isRMB = false;
let prevX = 0, prevY = 0;
let rotX = 0.3, rotZ = 0.5;
let panX = 0, panY = 0;
let zoom = 1;
const camDist = camera.position.length();

function updateCamera() {{
  const r = camDist * zoom;
  camera.position.set(
    r * Math.sin(rotX) * Math.cos(rotZ) + panX,
    r * Math.sin(rotX) * Math.sin(rotZ) + panY,
    r * Math.cos(rotX)
  );
  camera.up.set(0, 0, 1);
  camera.lookAt(panX, panY, MODEL.height/2);
}}

renderer.domElement.addEventListener('mousedown', e => {{
  isDragging = true; isRMB = e.button === 2;
  prevX = e.clientX; prevY = e.clientY;
}});
renderer.domElement.addEventListener('contextmenu', e => e.preventDefault());
window.addEventListener('mouseup', () => isDragging = false);
window.addEventListener('mousemove', e => {{
  if (!isDragging) return;
  const dx = e.clientX - prevX, dy = e.clientY - prevY;
  if (isRMB) {{ panX -= dx * 0.5; panY += dy * 0.5; }}
  else {{ rotZ += dx * 0.008; rotX = Math.max(0.05, Math.min(Math.PI-0.05, rotX + dy * 0.008)); }}
  prevX = e.clientX; prevY = e.clientY;
  updateCamera();
}});
renderer.domElement.addEventListener('wheel', e => {{
  zoom *= e.deltaY > 0 ? 1.1 : 0.9;
  zoom = Math.max(0.1, Math.min(10, zoom));
  updateCamera();
}});
window.addEventListener('keydown', e => {{
  if (e.key === 'r' || e.key === 'R') {{ rotX=0.3; rotZ=0.5; panX=0; panY=0; zoom=1; updateCamera(); }}
}});

window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

updateCamera();

(function animate() {{
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}})();
</script>
</body>
</html>'''


def render_html(model, out_path=None, open_browser=True):
    model_json = model.to_json()
    pcount = len(model.primitives)

    html = _TEMPLATE.format(
        name=model.name,
        w=model.width, d=model.depth, h=model.height,
        unit=model.unit,
        pcount=pcount,
        drawing_number=model.drawing_number,
        model_json=model_json,
    )

    if out_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False,
                                          prefix=f'architect_{model.name}_')
        out_path = tmp.name
        tmp.write(html.encode('utf-8'))
        tmp.close()
    else:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f'Viewer: {out_path}')

    if open_browser:
        webbrowser.open(f'file://{os.path.abspath(out_path)}')

    return out_path
