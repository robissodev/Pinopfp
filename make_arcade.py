# ============================================================
# PINORATOR — gera o gabinete arcade no Blender (headless) e
# exporta pinocab.glb. Formato: upright estilo Robotron 2084
# (marquee inclinado no topo, tela quase vertical, deck curto,
# coluna frontal preta, laterais brancas).
# Rodar:  Blender --background --python make_arcade.py
# Eixos Blender: Z = altura, -Y = frente.  (glTF converte p/ Y-up)
# Construido 100% via bmesh/data API — bpy.ops de geometria nao
# sobrevive em background com certos addons instalados.
# ============================================================
import bpy
import bmesh
import math

# ---------- planta (metros) ----------
INNER_W = 0.60           # vao entre as laterais
SIDE_T = 0.032           # espessura da lateral
HEIGHT = 1.85
BACK = -0.40             # z de profundidade (positivo = frente)

TOP_TIP = (0.270, 1.850)     # canto frontal do topo (marquee tip)
MARQ_BOT = (0.155, 1.585)    # base do marquee (inclina p/ tras descendo)
SCR_TOP = (0.155, 1.585)     # topo da tela
SCR_BOT = (0.265, 1.075)     # base da tela (leve inclinacao p/ frente)
DECK_F = (0.440, 1.005)      # frente do deck
LIP_BOT = (0.440, 0.945)     # base da borda do deck
STEP_IN = (0.365, 0.925)     # recuo p/ coluna frontal
FRONT_BOT = (0.365, 0.050)   # base da coluna frontal
KICK = (0.335, 0.000)        # kick no chao

# vidro do monitor (ocupa quase todo o segmento da tela)
MON_TOP = (0.158, 1.578)
MON_BOT = (0.262, 1.085)

DEG = math.radians
OUT = bpy.path.abspath("//pinocab.glb")

# ---------- limpa a cena (data API, sem ops) ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.materials):
    for item in list(block):
        block.remove(item)

# ---------- materiais ----------
def make_mat(name, color, rough=0.6, metal=0.0, emission=0.0, coat=0.0, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emission:
        # neon saturado: base escura, a cor vem da emissao
        bsdf.inputs["Base Color"].default_value = (color[0] * 0.25, color[1] * 0.25, color[2] * 0.25, 1)
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    if coat:
        # verniz glossy por cima (exporta como clearcoat no glTF)
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.08
    if transmission:
        # plastico fosco difusor: transmite luz com blur (frosted)
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1.0:
        # plastico translucido (alphaMode BLEND no glTF)
        c = bsdf.inputs["Base Color"].default_value
        bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], alpha)
        for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    return m

WHITE = make_mat("body_white", (0.92, 0.91, 0.95), rough=0.65)
BLACK = make_mat("front_black", (0.015, 0.015, 0.02), rough=0.75)
DARKP = make_mat("accent_dark", (0.045, 0.035, 0.08), rough=0.85)
GLASS = make_mat("monitor_glass", (0.006, 0.006, 0.01), rough=0.3)
METAL = make_mat("coin_metal", (0.07, 0.07, 0.09), rough=0.35, metal=0.8)
ORANGE = make_mat("coin_light", (0.95, 0.45, 0.05), rough=0.4)
RED = make_mat("joy_red", (0.85, 0.0, 0.18), rough=0.25)
STICK = make_mat("joy_stick", (0.1, 0.1, 0.13), rough=0.35, metal=0.4)
BTN_Y = make_mat("btn_yellow", (0.94, 0.76, 0.05), rough=0.42, coat=1.0, transmission=1.0)
BTN_M = make_mat("btn_magenta", (0.95, 0.14, 0.55), rough=0.42, coat=1.0, transmission=1.0)
BTN_G = make_mat("btn_green", (0.13, 0.95, 0.35), rough=0.42, coat=1.0, transmission=1.0)
LAMP_Y = make_mat("lamp_yellow", (1.0, 0.85, 0.12), emission=5.0)
LAMP_M = make_mat("lamp_magenta", (1.0, 0.2, 0.6), emission=5.0)
LAMP_G = make_mat("lamp_green", (0.2, 1.0, 0.4), emission=5.0)
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

# uv_mode ajusta a orientacao da textura por slot (validado empiricamente
# apos a conversao de eixos do glTF): normal, flipv (marquee/front)
UV_MODES = {
    'normal': ((0, 0), (1, 0), (1, 1), (0, 1)),
    'flipv':  ((0, 1), (1, 1), (1, 0), (0, 0)),
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

# painel inclinado definido por dois pontos (z,y) do perfil:
# top = borda alta, bot = borda baixa; retorna tambem angulo/centro
def slope(top, bot):
    dz = bot[0] - top[0]
    dy = top[1] - bot[1]
    length = math.hypot(dz, dy)
    ang = math.atan2(dy, dz)
    center = (0, -(top[0] + bot[0]) / 2, (top[1] + bot[1]) / 2)
    return length, ang, center

def slope_plane(name, top, bot, mat, uv_mode='normal', offset=0.0):
    length, ang, center = slope(top, bot)
    # offset desloca ao longo da normal da face: N = (0, -sin, cos)
    pos = (0, center[1] - math.sin(ang) * offset, center[2] + math.cos(ang) * offset)
    return make_plane(name, INNER_W, length, pos, (ang, 0, 0), mat, uv_mode)

# ---------- laterais: silhueta Robotron extrudada ----------
profile = [
    (BACK, 0.0), (BACK, HEIGHT),
    TOP_TIP, MARQ_BOT, SCR_BOT, DECK_F, LIP_BOT, STEP_IN, FRONT_BOT, KICK,
]

def make_side(name, x, offset):
    mesh = bpy.data.meshes.new(name)
    verts = [(x, -d, h) for (d, h) in profile]
    mesh.from_pydata(verts, [], [list(range(len(verts)))])
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(WHITE)
    solid = o.modifiers.new("solid", 'SOLIDIFY')
    solid.thickness = SIDE_T
    solid.offset = offset
    bev = o.modifiers.new("bevel", 'BEVEL')
    bev.width = 0.005
    bev.segments = 2
    return o

make_side("side_l", -INNER_W / 2, -1)
make_side("side_r", INNER_W / 2, 1)

# ---------- paineis ----------
# marquee inclinado (topo p/ frente) — fundo escuro; arte vai no art_marquee
slope_plane("marquee_back", TOP_TIP, MARQ_BOT, DARKP)

# topo e traseira
make_box("lid", INNER_W, TOP_TIP[0] - BACK, 0.02,
         (0, -(BACK + TOP_TIP[0]) / 2, HEIGHT), (0, 0, 0), WHITE)
make_box("back", INNER_W, HEIGHT, 0.02,
         (0, -BACK, HEIGHT / 2), (DEG(90), 0, 0), DARKP)

# moldura da tela (bezel escuro) + vidro 'monitor' (ancora da UI)
slope_plane("screen_bezel", SCR_TOP, SCR_BOT, BLACK)
mon_len, mon_ang, mon_c = slope(MON_TOP, MON_BOT)
make_plane("monitor", INNER_W - 0.016, mon_len,
           (0, mon_c[1] - math.cos(mon_ang) * 0.004, mon_c[2] + math.sin(mon_ang) * 0.004),
           (mon_ang, 0, 0), GLASS)

# deck curto e inclinado
slope_plane("deck", SCR_BOT, DECK_F, BLACK)

# borda do deck, recuo e coluna frontal preta
make_box("deck_lip", INNER_W, DECK_F[1] - LIP_BOT[1], 0.02,
         (0, -DECK_F[0], (DECK_F[1] + LIP_BOT[1]) / 2), (DEG(90), 0, 0), BLACK)
slope_plane("step", LIP_BOT, STEP_IN, BLACK)
front_h = STEP_IN[1] - FRONT_BOT[1]
make_box("front", INNER_W, front_h, 0.02,
         (0, -STEP_IN[0], FRONT_BOT[1] + front_h / 2), (DEG(90), 0, 0), BLACK)
slope_plane("kick", FRONT_BOT, KICK, DARKP)

# ---------- coin door (dois slots laranja, estilo Williams) ----------
make_box("coin_door", 0.20, 0.17, 0.024,
         (0, -STEP_IN[0] - 0.012, 0.52), (DEG(90), 0, 0), METAL)
for i, dx in enumerate((-0.045, 0.045)):
    make_box(f"coin_slot_{i}", 0.022, 0.032, 0.02,
             (dx, -STEP_IN[0] - 0.026, 0.565), (DEG(90), 0, 0), ORANGE)

# ---------- joystick + botoes no deck ----------
deck_len, deck_ang, deck_c = slope(SCR_BOT, DECK_F)
sn, cs = math.sin(deck_ang), math.cos(deck_ang)
joy_y = deck_c[1] - sn * 0.012
joy_z = deck_c[2] + cs * 0.012

# cilindros ficam com o eixo alinhado a normal do deck (rot_x = deck_ang)
make_cyl("joy_base", 0.032, 0.012, (-0.16, joy_y, joy_z), (deck_ang, 0, 0), BLACK, segs=24)
make_cyl("joy_stick", 0.008, 0.095, (-0.16, joy_y - sn * 0.05, joy_z + cs * 0.05), (deck_ang + DEG(4), 0, 0), STICK, segs=16)
make_sphere("joy_ball", 0.024, (-0.16, joy_y - sn * 0.10, joy_z + cs * 0.10), RED)

# botoes retangulares iluminados, mais acima no deck (direcao da tela)
UP = 0.045
up_y, up_z = 0.974 * UP, 0.226 * UP
for i, (dx, m, lm) in enumerate(((-0.025, BTN_Y, LAMP_Y), (0.08, BTN_M, LAMP_M), (0.185, BTN_G, LAMP_G))):
    make_box(f"btn_{i}", 0.078, 0.05, 0.028,
             (dx, joy_y + up_y, joy_z + up_z), (deck_ang, 0, 0), m)
    # lampada achatada, totalmente dentro do plastico
    make_sphere(f"btn_lamp_{i}", 0.034, (dx, joy_y + up_y, joy_z + up_z), lm,
                scale=(1.1, 0.72, 0.35), rot=(deck_ang, 0, 0))

# ---------- planos de arte (slots de textura no runtime) ----------
slope_plane("art_marquee", TOP_TIP, MARQ_BOT, ART, uv_mode='flipv', offset=0.012)
make_plane("art_front", INNER_W, front_h,
           (0, -STEP_IN[0] - 0.013, FRONT_BOT[1] + front_h / 2), (DEG(90), 0, 0), ART, uv_mode='flipv')
slope_plane("art_deck", SCR_BOT, DECK_F, ART, offset=0.013)

# laterais construidas direto no espaco final (sem rotacao euler):
# validado: lado direito frente em u=0, esquerdo frente em u=1, v flipado
def side_art(name, x, normal_sign):
    art_f = DECK_F[0]
    pts = [(x, -art_f, 0), (x, -BACK, 0), (x, -BACK, HEIGHT), (x, -art_f, HEIGHT)]
    if normal_sign > 0:
        uvs = [(0, 1), (1, 1), (1, 0), (0, 0)]
    else:
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

# ---------- exporta ----------
print("OBJETOS:", sorted(o.name for o in bpy.context.scene.objects))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_apply=True)
print("EXPORTADO:", OUT)
