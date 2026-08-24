# ============================================================
# PINORATOR — gera o gabinete arcade no Blender (headless) e
# exporta pinocab.glb. Planta tirada do GLB de referencia.
# Rodar:  Blender --background --python make_arcade.py
# Eixos Blender: Z = altura, -Y = frente.  (glTF converte p/ Y-up)
# Construido 100% via bmesh/data API — bpy.ops de geometria nao
# sobrevive em background com certos addons instalados.
# ============================================================
import bpy
import bmesh
import math

# ---------- planta (metros) ----------
INNER_W = 0.713          # vao entre as laterais
SIDE_T = 0.04            # espessura da lateral
HEIGHT = 1.826
BACK = -0.429            # z de profundidade (positivo = frente)
MARQ_F = 0.253
MARQ_TOP = 1.820
MARQ_BOT = 1.513
MON_TOP = (-0.330, 1.276)   # (z, altura) borda alta/tras do vidro
MON_BOT = (0.242, 1.051)    # (z, altura) borda baixa/frente
DECK_F = 0.490
DECK_TOP = 1.029
LIP_BOT = 0.955
FRONT_Z = 0.363
FRONT_TOP = 0.930
KICK_Z = 0.330

DEG = math.radians
OUT = bpy.path.abspath("//pinocab.glb")

# ---------- limpa a cena (data API, sem ops) ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.materials):
    for item in list(block):
        block.remove(item)

# ---------- materiais ----------
def make_mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m

WHITE = make_mat("body_white", (0.92, 0.91, 0.95), rough=0.7)
YELLOW = make_mat("side_yellow", (0.94, 0.76, 0.05), rough=0.55)
DARK = make_mat("accent_dark", (0.055, 0.04, 0.1), rough=0.85)
GLASS = make_mat("monitor_glass", (0.006, 0.006, 0.01), rough=0.3)
METAL = make_mat("coin_metal", (0.08, 0.08, 0.1), rough=0.35, metal=0.8)
RED = make_mat("joy_red", (0.85, 0.0, 0.18), rough=0.25)
STICK = make_mat("joy_stick", (0.1, 0.1, 0.13), rough=0.35, metal=0.4)
BTN_Y = make_mat("btn_yellow", (0.94, 0.76, 0.05), rough=0.3)
BTN_M = make_mat("btn_magenta", (0.95, 0.14, 0.55), rough=0.3)
BTN_G = make_mat("btn_green", (0.13, 0.95, 0.35), rough=0.3)
ART = make_mat("art_neutral", (0.5, 0.5, 0.5), rough=0.8)

# ---------- helpers (bmesh -> objeto linkado) ----------
def obj_from_bm(name, bm, mat):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o

# uv_mode ajusta a orientacao da textura por slot (achado empiricamente
# apos a conversao de eixos do glTF): normal, flip (180), cw, ccw
UV_MODES = {
    'normal': ((0, 0), (1, 0), (1, 1), (0, 1)),
    'flip':   ((1, 1), (0, 1), (0, 0), (1, 0)),
    'flipv':  ((0, 1), (1, 1), (1, 0), (0, 0)),
    'cw':     ((0, 1), (0, 0), (1, 0), (1, 1)),
    'ccw':    ((1, 0), (1, 1), (0, 1), (0, 0)),
}

def make_plane(name, w, h, pos, rot=(0, 0, 0), mat=WHITE, uv_mode='normal'):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in
          ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for loop, coord in zip(f.loops, UV_MODES[uv_mode]):
        loop[uv].uv = coord
    o = obj_from_bm(name, bm, mat)
    o.rotation_euler = rot
    o.location = pos
    return o

def make_box(name, sx, sy, sz, pos, rot=(0, 0, 0), mat=WHITE):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    o = obj_from_bm(name, bm, mat)
    o.scale = (sx, sy, sz)
    o.rotation_euler = rot
    o.location = pos
    return o

def make_cyl(name, r, depth, pos, rot=(0, 0, 0), mat=WHITE, segs=20):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=depth)
    o = obj_from_bm(name, bm, mat)
    o.rotation_euler = rot
    o.location = pos
    return o

def make_sphere(name, r, pos, mat, scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=r)
    o = obj_from_bm(name, bm, mat)
    o.scale = scale
    o.rotation_euler = rot
    o.location = pos
    return o

# ---------- laterais: silhueta extrudada ----------
profile = [
    (BACK, 0.0), (BACK, HEIGHT), (MARQ_F, HEIGHT), (MARQ_F, MARQ_BOT),
    (MON_TOP[0], MON_TOP[1]), (MON_BOT[0], MON_BOT[1]),
    (DECK_F, DECK_TOP), (DECK_F, LIP_BOT), (FRONT_Z, FRONT_TOP),
    (FRONT_Z, 0.093), (KICK_Z, 0.0),
]

def make_side(name, x, offset):
    mesh = bpy.data.meshes.new(name)
    verts = [(x, -d, h) for (d, h) in profile]
    mesh.from_pydata(verts, [], [list(range(len(verts)))])
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(YELLOW)
    solid = o.modifiers.new("solid", 'SOLIDIFY')
    solid.thickness = SIDE_T
    solid.offset = offset
    bev = o.modifiers.new("bevel", 'BEVEL')
    bev.width = 0.006
    bev.segments = 2
    return o

make_side("side_l", -INNER_W / 2, -1)
make_side("side_r", INNER_W / 2, 1)

# ---------- paineis ----------
marq_h = MARQ_TOP - MARQ_BOT
make_box("marquee_back", INNER_W, marq_h, 0.02,
         (0, -MARQ_F, MARQ_BOT + marq_h / 2), (DEG(90), 0, 0), DARK)

make_box("lid", INNER_W, MARQ_F - BACK, 0.02,
         (0, -(BACK + MARQ_F) / 2, HEIGHT), (0, 0, 0), WHITE)
make_box("back", INNER_W, HEIGHT, 0.02,
         (0, -BACK, HEIGHT / 2), (DEG(90), 0, 0), DARK)

# vidro do monitor — nome 'monitor' e o ancora da UI no three.js
mon_dz = MON_BOT[0] - MON_TOP[0]
mon_dy = MON_TOP[1] - MON_BOT[1]
mon_len = math.hypot(mon_dz, mon_dy)
mon_ang = math.atan2(mon_dy, mon_dz)
mon_c = (0, -(MON_TOP[0] + MON_BOT[0]) / 2, (MON_TOP[1] + MON_BOT[1]) / 2)
make_plane("monitor", INNER_W, mon_len, mon_c, (mon_ang, 0, 0), GLASS)

# painel de controle (deck)
deck_len = DECK_F - MON_BOT[0]
deck_ang = math.atan2(MON_BOT[1] - DECK_TOP, deck_len)
deck_c = (0, -(MON_BOT[0] + DECK_F) / 2, (MON_BOT[1] + DECK_TOP) / 2)
make_box("deck", INNER_W, deck_len, 0.02, deck_c, (deck_ang, 0, 0), WHITE)

# borda do deck, prateleira, painel frontal e kick
make_box("deck_lip", INNER_W, DECK_TOP - LIP_BOT, 0.02,
         (0, -DECK_F, (DECK_TOP + LIP_BOT) / 2), (DEG(90), 0, 0), DARK)
shelf_len = math.hypot(DECK_F - FRONT_Z, LIP_BOT - FRONT_TOP)
shelf_ang = math.atan2(LIP_BOT - FRONT_TOP, DECK_F - FRONT_Z)
make_box("shelf", INNER_W, shelf_len, 0.02,
         (0, -(DECK_F + FRONT_Z) / 2, (LIP_BOT + FRONT_TOP) / 2), (shelf_ang + DEG(90), 0, 0), WHITE)
front_h = FRONT_TOP - 0.093
make_box("front", INNER_W, front_h, 0.02,
         (0, -FRONT_Z, 0.093 + front_h / 2), (DEG(90), 0, 0), WHITE)
kick_len = math.hypot(FRONT_Z - KICK_Z, 0.093)
kick_ang = math.atan2(0.093, FRONT_Z - KICK_Z)
make_box("kick", INNER_W, kick_len, 0.02,
         (0, -(FRONT_Z + KICK_Z) / 2, 0.0465), (DEG(90) - kick_ang, 0, 0), DARK)

# ---------- coin door ----------
make_box("coin_door", 0.21, 0.165, 0.024,
         (0, -FRONT_Z - 0.012, 0.46), (DEG(90), 0, 0), METAL)
for i, dx in enumerate((-0.05, 0.05)):
    make_box(f"coin_slot_{i}", 0.016, 0.045, 0.02,
             (dx, -FRONT_Z - 0.026, 0.46), (DEG(90), 0, 0), DARK)

# ---------- joystick + botoes no deck ----------
deck_surf_z = (MON_BOT[1] + DECK_TOP) / 2 + 0.012
deck_surf_y = -(MON_BOT[0] + DECK_F) / 2

make_cyl("joy_base", 0.036, 0.014, (-0.19, deck_surf_y, deck_surf_z), (deck_ang, 0, 0), DARK, segs=24)
make_cyl("joy_stick", 0.009, 0.105, (-0.19, deck_surf_y + 0.005, deck_surf_z + 0.055), (deck_ang + DEG(4), 0, 0), STICK, segs=16)
make_sphere("joy_ball", 0.027, (-0.19, deck_surf_y + 0.009, deck_surf_z + 0.112), RED)

for i, (dx, m) in enumerate(((0.10, BTN_Y), (0.175, BTN_M), (0.25, BTN_G))):
    make_sphere(f"btn_{i}", 0.023, (dx, deck_surf_y, deck_surf_z + 0.004), m,
                scale=(1, 1, 0.5), rot=(deck_ang, 0, 0))

# ---------- planos de arte (slots de textura no runtime) ----------
# laterais construidas direto no espaco final (sem rotacao euler):
# u=0 atras, u=1 na frente, v=0 embaixo, v=1 em cima
def side_art(name, x, normal_sign):
    pts = [(x, -DECK_F, 0), (x, -BACK, 0), (x, -BACK, HEIGHT), (x, -DECK_F, HEIGHT)]
    if normal_sign > 0:
        # lado direito: visto de fora, a frente fica a esquerda -> u=0 na frente
        uvs = [(0, 1), (1, 1), (1, 0), (0, 0)]
    else:
        # lado esquerdo: visto de fora, a frente fica a direita -> u=1 na frente
        uvs = [(1, 1), (0, 1), (0, 0), (1, 0)]
    if normal_sign < 0:
        pts = pts[::-1]
        uvs = uvs[::-1]
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    face = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for loop, c in zip(face.loops, uvs):
        loop[uv].uv = c
    obj_from_bm(name, bm, ART)

side_art("art_side_l", -INNER_W / 2 - SIDE_T - 0.002, -1)
side_art("art_side_r", INNER_W / 2 + SIDE_T + 0.002, 1)
make_plane("art_marquee", INNER_W, marq_h,
           (0, -MARQ_F - 0.013, MARQ_BOT + marq_h / 2), (DEG(90), 0, 0), ART, uv_mode='flipv')
make_plane("art_front", INNER_W, front_h,
           (0, -FRONT_Z - 0.013, 0.093 + front_h / 2), (DEG(90), 0, 0), ART, uv_mode='flipv')
make_plane("art_deck", INNER_W, deck_len,
           (deck_c[0], deck_c[1], deck_c[2] + 0.014), (deck_ang, 0, 0), ART)

# ---------- exporta ----------
print("OBJETOS:", sorted(o.name for o in bpy.context.scene.objects))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_apply=True)
print("EXPORTADO:", OUT)
