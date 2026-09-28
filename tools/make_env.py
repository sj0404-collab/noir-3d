#!/usr/bin/env python3
"""Окружение Ноктиса: набор модульных моделей улицы.

В отличие от процедурной геометрии в `src/scene/NoirStreet.tsx` это настоящие
модели: их можно двигать, анимировать и переиспользовать (`<Clone>` в three
делит геометрию). Флаг rigged — на цепочке костей, клип `Wind` бесшовный.

Модели в `public/models/street_kit.glb` (каждая — узел с именем, меши-детали
внутри по материалам):
  facade_a, facade_b — модульные фасады 5×12×4 м (окна, карнизы, козырёк,
                       вывеска, кондиционеры, пожарная лестница, балкон)
  hydrant, bin, bench, traffic_light, phone_booth, vending, mailbox, crates,
  bollard, manhole, neon_sign — уличный реквизит
  flagpole — флаг на костях (клип Wind)

Запуск:
  blender -b -P tools/make_env.py -- --out public/models
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import noirlib as N  # noqa: E402

TAU = math.pi * 2


class Kit:
    """Сборка моделей по материалам: одна модель = узел + меши по материалам."""

    def __init__(self, M):
        self.M = M
        self.models = {}

    def add(self, name, groups, parent=None):
        node = bpy.data.objects.new(name, None)
        bpy.context.collection.objects.link(node)
        if parent is not None:
            node.parent = parent
        for mat_name, parts in groups:
            parts = [p for p in parts if p is not None]
            if not parts:
                continue
            obj = N.join_parts(parts, f'{name}__{mat_name}')
            N.set_mat(obj, self.M[mat_name])
            obj.parent = node
        self.models[name] = node
        return node


# ---------------------------------------------------------------- фасады
def facade(kit, name, seed=0, balcony=False, seed_off=0.0):
    M = kit.M
    wall, concrete, glass, glass_lit, metal, neon, dark = [], [], [], [], [], [], []
    rnd = (lambda n: (math.sin((seed * 12.9898 + n * 78.233 + seed_off) * 43758.5453) % 1 + 1) % 1)

    # корпус и цоколь
    wall.append(N.box('Wall', (5.0, 4.0, 12.0), (0, 2.0, 6.0), None, bevel=0.06))
    concrete.append(N.box('Plinth', (5.14, 0.36, 2.60), (0, -0.04, 1.30), None, bevel=0.04))
    concrete.append(N.box('Cornice', (5.46, 0.52, 0.46), (0, 0.06, 11.86), None, bevel=0.06))
    concrete.append(N.box('Cornice2', (5.26, 0.34, 0.26), (0, 0.02, 7.30), None, bevel=0.05))
    # водосточная труба
    metal.append(N.cyl('Drain', 0.085, 11.4, (2.34, -0.12, 6.0), None, verts=12))
    metal.append(N.box('DrainBrace', (0.16, 0.20, 0.06), (2.34, -0.06, 8.20), None, bevel=0.02))

    # окна 2×3
    for r, z in enumerate((4.30, 6.55, 9.00)):
        for c, x in enumerate((-1.25, 1.25)):
            n = r * 3 + c
            dark.append(N.box(f'Frame{r}{c}', (1.34, 0.18, 1.82), (x, -0.07, z), None, bevel=0.04))
            (glass_lit if rnd(n) > 0.45 else glass).append(
                N.box(f'Pane{r}{c}', (1.06, 0.10, 1.52), (x, -0.13, z), None, bevel=0.02))
            concrete.append(N.box(f'Sill{r}{c}', (1.54, 0.30, 0.12), (x, -0.16, z - 0.98),
                                  None, bevel=0.03))
            metal.append(N.box(f'Mullion{r}{c}', (0.06, 0.14, 1.52), (x, -0.19, z), None, bevel=0.01))
            if rnd(n + 9) > 0.7:  # кондиционер под окном
                metal.append(N.box(f'AC{r}{c}', (0.72, 0.46, 0.52), (x, -0.30, z - 1.30), None,
                                   bevel=0.04))
                dark.append(N.cyl(f'ACFan{r}{c}', 0.16, 0.08, (x, -0.55, z - 1.30), None,
                                  rot=(math.pi / 2, 0, 0), verts=14))

    # первый этаж: витрина, козырёк, вывеска
    glass.append(N.box('ShopGlass', (4.10, 0.10, 2.00), (0, -0.10, 1.62), None, bevel=0.02))
    dark.append(N.box('ShopFrame', (4.24, 0.16, 0.10), (0, -0.12, 0.62), None, bevel=0.02))
    dark.append(N.box('ShopFrame2', (0.10, 0.16, 2.00), (-2.06, -0.12, 1.62), None, bevel=0.02))
    dark.append(N.box('ShopFrame3', (0.10, 0.16, 2.00), (2.06, -0.12, 1.62), None, bevel=0.02))
    metal.append(N.box('Awning', (4.60, 1.05, 0.10), (0, -0.52, 3.05), None,
                       rot=(-0.28, 0, 0), bevel=0.03))
    for x in (-2.0, 2.0):
        metal.append(N.box(f'AwningArm{x}', (0.06, 0.90, 0.06), (x, -0.46, 2.92), None,
                           rot=(-0.28, 0, 0), bevel=0.02))
    dark.append(N.box('SignBoard', (3.30, 0.16, 0.74), (0, -0.22, 3.66), None, bevel=0.04))
    (neon if seed % 2 == 0 else glass_lit).append(
        N.box('SignGlow', (2.90, 0.08, 0.44), (0, -0.32, 3.66), None, bevel=0.02))
    # фонарь над входом
    metal.append(N.box('LampArm', (0.10, 0.70, 0.10), (0, -0.34, 2.74), None, bevel=0.02))
    glass_lit.append(N.box('Lamp', (0.26, 0.26, 0.30), (0, -0.68, 2.66), None, bevel=0.06))

    # пожарная лестница
    for lvl, z in ((0, 4.30), (1, 6.55)):
        metal.append(N.box(f'Plat{lvl}', (2.70, 1.00, 0.08), (0, -0.52, z - 1.20), None, bevel=0.02))
        metal.append(N.pipe(f'Rail{lvl}', [(-1.30, -0.06, z - 1.14), (-1.30, -1.00, z - 1.14)], 0.035))
        metal.append(N.pipe(f'Rail{lvl}b', [(1.30, -0.06, z - 1.14), (1.30, -1.00, z - 1.14)], 0.035))
        for i in range(4):
            x = -0.98 + i * 0.66
            metal.append(N.pipe(f'Bal{lvl}{i}', [(x, -0.06, z - 1.14), (x, -1.00, z - 1.14)], 0.026))
    for i in range(6):  # лестница между площадками
        z = 5.10 + i * 0.42
        metal.append(N.box(f'Rung{i}', (0.70, 0.05, 0.05), (0, -0.62, z), None, bevel=0.01))
    metal.append(N.pipe('LadderL', [(0.38, -0.62, 4.00), (0.38, -0.62, 6.60)], 0.032))
    metal.append(N.pipe('LadderR', [(-0.38, -0.62, 4.00), (-0.38, -0.62, 6.60)], 0.032))

    if balcony:
        concrete.append(N.box('BalconySlab', (3.00, 1.10, 0.12), (0, -0.56, 5.30), None, bevel=0.03))
        metal.append(N.pipe('BalRail', [(-1.44, -0.10, 6.14), (-1.44, -1.08, 6.14)], 0.035))
        metal.append(N.pipe('BalRail2', [(1.44, -0.10, 6.14), (1.44, -1.08, 6.14)], 0.035))
        for i in range(7):
            x = -1.30 + i * 0.44
            metal.append(N.pipe(f'Bal{i}', [(x, -0.10, 6.14), (x, -1.08, 6.14)], 0.024))
        metal.append(N.pipe('BalTop', [(-1.44, -1.08, 6.14), (1.44, -1.08, 6.14)], 0.030))
        metal.append(N.pipe('BalTop2', [(-1.44, -0.10, 5.70), (1.44, -0.10, 5.70)], 0.030))
        neon.append(N.box('BalPlant', (0.40, 0.30, 0.34), (1.10, -0.70, 5.56), None, bevel=0.06))

    return kit.add(name, [('brick', wall), ('concrete', concrete), ('glass_win', glass),
                          ('glass_lit', glass_lit), ('metal_dark', metal), ('neon_cyan', neon),
                          ('coat_dark', dark)])


# ---------------------------------------------------------------- реквизит
def hydrant(kit):
    metal, red = [], []
    metal.append(N.cyl('Base', 0.24, 0.10, (0, 0, 0.05), None, verts=16))
    red.append(N.cyl('Body', 0.165, 0.52, (0, 0, 0.34), None, verts=18))
    red.append(N.sphere('Dome', 0.17, (0, 0, 0.60), scale=(1, 1, 0.75), seg=16, rings=10))
    metal.append(N.cyl('Bonnet', 0.10, 0.10, (0, 0, 0.70), None, verts=12))
    metal.append(N.sphere('Knob', 0.06, (0, 0, 0.78), seg=10, rings=8))
    for s, sgn in (('L', 1), ('R', -1)):
        metal.append(N.cyl(f'Nozzle{s}', 0.085, 0.22, (sgn * 0.20, 0, 0.40), None,
                           rot=(0, math.pi / 2, 0), verts=12))
        metal.append(N.cyl(f'Cap{s}', 0.095, 0.05, (sgn * 0.31, 0, 0.40), None,
                           rot=(0, math.pi / 2, 0), verts=12))
    metal.append(N.cyl('Ring', 0.175, 0.05, (0, 0, 0.18), None, verts=18))
    return kit.add('hydrant', [('car_body2', red), ('metal_dark', metal)])


def trash_bin(kit):
    metal, dark = [], []
    metal.append(N.cyl('Body', 0.29, 0.78, (0, 0, 0.42), None, verts=18))
    for z in (0.16, 0.68):
        metal.append(N.cyl(f'Ring{z}', 0.305, 0.05, (0, 0, z), None, verts=18))
    dark.append(N.cyl('Lid', 0.31, 0.07, (0, 0, 0.85), None, verts=18))
    dark.append(N.box('Slot', (0.26, 0.10, 0.06), (0, -0.28, 0.85), None, bevel=0.01))
    metal.append(N.cyl('Base', 0.24, 0.06, (0, 0, 0.03), None, verts=14))
    return kit.add('bin', [('metal_dark', metal), ('coat_dark', dark)])


def bench(kit):
    wood, metal = [], []
    for s, sgn in (('L', 1), ('R', -1)):
        metal.append(N.box(f'Leg{s}', (0.09, 0.56, 0.44), (sgn * 0.72, 0, 0.22), None, bevel=0.02))
        metal.append(N.pipe(f'Back{s}', [(sgn * 0.72, 0.24, 0.40), (sgn * 0.72, 0.30, 0.92)], 0.035))
    for i in range(4):
        wood.append(N.box(f'Seat{i}', (1.72, 0.13, 0.055), (0, -0.18 + i * 0.16, 0.46),
                          None, bevel=0.015))
    for i in range(3):
        wood.append(N.box(f'Back{i}', (1.72, 0.055, 0.13), (0, 0.28 + i * 0.02, 0.58 + i * 0.16),
                          None, rot=(-0.16, 0, 0), bevel=0.015))
    return kit.add('bench', [('wood', wood), ('metal_dark', metal)])


def traffic_light(kit):
    metal, red, amber, green = [], [], [], []
    metal.append(N.cyl('Base', 0.20, 0.16, (0, 0, 0.08), None, verts=14))
    metal.append(N.cyl('Pole', 0.075, 4.10, (0, 0, 2.10), None, verts=12))
    metal.append(N.pipe('Arm', [(0, 0, 4.02), (0, -1.30, 4.02)], 0.06))
    metal.append(N.box('Head', (0.34, 0.30, 0.94), (0, -1.34, 3.46), None, bevel=0.05))
    for i, (z, bucket) in enumerate(((3.72, red), (3.46, amber), (3.20, green))):
        bucket.append(N.cyl(f'Lamp{i}', 0.115, 0.08, (0, -1.50, z), None,
                            rot=(math.pi / 2, 0, 0), verts=16))
        metal.append(N.cyl(f'Hood{i}', 0.145, 0.16, (0, -1.58, z + 0.02), None,
                           rot=(math.pi / 2, 0, 0), verts=16, scale=(1, 1, 0.5)))
    metal.append(N.box('Box', (0.30, 0.22, 0.40), (0, -0.24, 2.60), None, bevel=0.04))
    metal.append(N.cyl('PedLamp', 0.09, 0.06, (0, -0.37, 2.72), None, rot=(math.pi / 2, 0, 0), verts=12))
    return kit.add('traffic_light', [('metal_dark', metal), ('neon_pink', red),
                                     ('lamp_warm', amber), ('neon_cyan', green)])


def phone_booth(kit):
    metal, glass, neon = [], [], []
    for sx in (-0.42, 0.42):
        for sy in (-0.28, 0.28):
            metal.append(N.box(f'Post{sx}{sy}', (0.09, 0.09, 2.30), (sx, sy, 1.15), None, bevel=0.02))
    metal.append(N.box('Roof', (1.06, 0.82, 0.14), (0, 0, 2.36), None, bevel=0.05))
    metal.append(N.box('Base', (1.02, 0.78, 0.12), (0, 0, 0.06), None, bevel=0.04))
    for sy in (-0.29, 0.29):
        glass.append(N.box(f'Glass{sy}', (0.74, 0.05, 1.86), (0, sy, 1.20), None, bevel=0.01))
    glass.append(N.box('GlassSide', (0.05, 0.50, 1.86), (-0.43, 0, 1.20), None, bevel=0.01))
    metal.append(N.box('Shelf', (0.70, 0.28, 0.06), (0, 0.10, 1.02), None, bevel=0.02))
    neon.append(N.box('Lamp', (0.60, 0.40, 0.06), (0, 0, 2.20), None, bevel=0.02))
    neon.append(N.box('Sign', (0.70, 0.06, 0.18), (0, -0.34, 2.44), None, bevel=0.02))
    return kit.add('phone_booth', [('metal_dark', metal), ('glass_win', glass), ('neon_cyan', neon)])


def vending(kit):
    body, dark, neon = [], [], []
    body.append(N.box('Body', (0.98, 0.62, 1.88), (0, 0, 0.94), None, bevel=0.06))
    body.append(N.box('Top', (1.04, 0.66, 0.10), (0, 0, 1.90), None, bevel=0.04))
    dark.append(N.box('Front', (0.62, 0.06, 1.10), (-0.10, -0.32, 1.10), None, bevel=0.02))
    neon.append(N.box('Panel', (0.52, 0.04, 0.96), (-0.10, -0.36, 1.10), None, bevel=0.01))
    dark.append(N.box('Slot', (0.22, 0.05, 0.14), (0.32, -0.33, 1.62), None, bevel=0.02))
    dark.append(N.box('Tray', (0.52, 0.10, 0.24), (0, -0.32, 0.34), None, bevel=0.03))
    dark.append(N.box('Leg1', (0.10, 0.10, 0.12), (-0.38, -0.20, 0.06), None, bevel=0.02))
    dark.append(N.box('Leg2', (0.10, 0.10, 0.12), (0.38, -0.20, 0.06), None, bevel=0.02))
    return kit.add('vending', [('car_body', body), ('coat_dark', dark), ('neon_pink', neon)])


def mailbox(kit):
    body, metal = [], []
    metal.append(N.box('Post', (0.12, 0.12, 0.72), (0, 0, 0.36), None, bevel=0.02))
    metal.append(N.box('Foot', (0.44, 0.34, 0.08), (0, 0, 0.04), None, bevel=0.02))
    body.append(N.box('Case', (0.62, 0.52, 0.78), (0, 0, 1.10), None, bevel=0.16))
    body.append(N.cyl('Dome', 0.31, 0.52, (0, 0, 1.48), None, rot=(0, math.pi / 2, 0), verts=18,
                      scale=(1, 1, 0.55)))
    metal.append(N.box('Slot', (0.34, 0.06, 0.05), (0, -0.27, 1.36), None, bevel=0.01))
    metal.append(N.box('Flag', (0.05, 0.20, 0.16), (0.32, 0, 1.24), None, rot=(0, 0, 0.3), bevel=0.02))
    return kit.add('mailbox', [('car_body2', body), ('metal_dark', metal)])


def crates(kit):
    wood, metal = [], []
    wood.append(N.box('Crate1', (0.66, 0.66, 0.60), (0, 0, 0.30), None, rot=(0, 0, 0.22), bevel=0.04))
    wood.append(N.box('Crate2', (0.58, 0.58, 0.52), (0.10, 0.14, 0.86), None, rot=(0, 0, -0.34), bevel=0.04))
    wood.append(N.box('Crate3', (0.52, 0.52, 0.46), (-0.46, -0.22, 0.23), None, rot=(0, 0, 0.62), bevel=0.04))
    for i, (x, y) in enumerate(((0.78, -0.30), (0.66, 0.42))):
        metal.append(N.cyl(f'Barrel{i}', 0.28, 0.86, (x, y, 0.43), None, verts=18))
        for z in (0.24, 0.62):
            metal.append(N.cyl(f'BarrelRing{i}{z}', 0.295, 0.05, (x, y, z), None, verts=18))
    return kit.add('crates', [('wood', wood), ('rust', metal)])


def bollard(kit):
    metal = [N.cyl('Post', 0.10, 0.72, (0, 0, 0.36), None, verts=14),
             N.sphere('Cap', 0.10, (0, 0, 0.72), seg=12, rings=8),
             N.cyl('Base', 0.16, 0.08, (0, 0, 0.04), None, verts=14)]
    return kit.add('bollard', [('metal_dark', metal)])


def manhole(kit):
    metal = [N.cyl('Disc', 0.36, 0.05, (0, 0, 0.015), None, verts=24),
             N.cyl('Inner', 0.24, 0.06, (0, 0, 0.022), None, verts=20)]
    dark = [N.box('Slot', (0.30, 0.05, 0.02), (0, 0, 0.052), None, bevel=0.005)]
    return kit.add('manhole', [('metal_dark', metal), ('coat_dark', dark)])


def neon_sign(kit):
    dark, neon = [], []
    dark.append(N.box('Board', (0.86, 0.16, 2.60), (0, 0, 1.30), None, bevel=0.05))
    dark.append(N.box('Arm1', (0.10, 0.50, 0.10), (0, 0.30, 2.40), None, bevel=0.02))
    dark.append(N.box('Arm2', (0.10, 0.50, 0.10), (0, 0.30, 0.24), None, bevel=0.02))
    # «иероглифы» абстрактными штрихами
    strokes = [(0.0, 2.10, 0.62, 0.10), (0.0, 1.86, 0.30, 0.34), (0.0, 1.42, 0.70, 0.10),
               (-0.16, 1.10, 0.10, 0.56), (0.16, 1.10, 0.10, 0.56), (0.0, 0.72, 0.50, 0.10)]
    for i, (x, z, w, h) in enumerate(strokes):
        neon.append(N.box(f'Stroke{i}', (w, 0.06, h), (x, -0.10, z), None, bevel=0.02))
    return kit.add('neon_sign', [('coat_dark', dark), ('neon_pink', neon)])


# ---------------------------------------------------------------- флаг
FLAG_BONES = [
    ('flag.1', (0, 0, 4.60), (0, 0, 3.30), None),
    ('flag.2', (0, 0, 3.30), (0, 0, 2.00), 'flag.1', True),
    ('flag.3', (0, 0, 2.00), (0, 0, 0.70), 'flag.2', True),
]


def flagpole(kit):
    metal, cloth = [], []
    metal.append(N.cyl('Base', 0.26, 0.20, (0, 0, 0.10), None, verts=16))
    metal.append(N.cyl('Pole', 0.065, 4.70, (0, 0, 2.40), None, verts=12))
    metal.append(N.sphere('Finial', 0.11, (0, 0, 4.80), seg=12, rings=8))
    metal.append(N.cyl('Crossbar', 0.035, 1.00, (0.50, 0, 4.62), None,
                       rot=(0, math.pi / 2, 0), verts=8))
    metal.append(N.box('Banner', (0.06, 0.10, 3.90), (-0.16, 0.04, 2.68), None, bevel=0.02))
    node = kit.add('flagpole', [('metal_dark', metal)])

    rig = N.build_armature(FLAG_BONES, name='FlagRig')
    # ткань: плоскость 6×4 сегмента, веса по высоте -> три кости
    flag = N.grid_mesh('Flag', 0.94, 3.90, 6, 4, (0.50, 0, 2.68), None)
    N.set_mat(flag, kit.M['fabric_red'])
    vgs = {n: flag.vertex_groups.new(name=n) for n in ('flag.1', 'flag.2', 'flag.3')}
    for i, v in enumerate(flag.data.vertices):
        t = (4.62 - v.co.z) / 3.90  # 0 сверху, 1 снизу
        seg = min(2, int(t * 3))
        names = ['flag.1', 'flag.2', 'flag.3']
        w = 1.0 - (t * 3 - seg)
        vgs[names[seg]].add([i], 1.0, 'REPLACE')
        if seg < 2 and w > 0.02:
            vgs[names[seg + 1]].add([i], w, 'REPLACE')
    mod = flag.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    flag.parent = rig
    flag.matrix_parent_inverse = rig.matrix_world.inverted()
    flag.parent = node
    kit.models['flag'] = flag

    action = N.bake_loop(rig, 48, pose_wind, stride=2)
    N.stage_clip(rig, action, 'Wind')
    return rig


def pose_wind(u):
    ph = TAU * u
    return {
        'flag.1': (0, math.sin(ph) * 0.16, 0),
        'flag.2': (0, math.sin(ph - 0.7) * 0.30, 0),
        'flag.3': (0, math.sin(ph - 1.4) * 0.44, 0),
    }


# ---------------------------------------------------------------- main
def main():
    out, only = N.parse_args()
    if only and os.path.basename(__file__).replace('.py', '') not in only:
        print('[SKIP] %s' % os.path.basename(__file__))
        return
    N.reset_scene()
    os.makedirs(out, exist_ok=True)
    N.setup_scene(48)

    M = N.make_materials()
    kit = Kit(M)

    facade(kit, 'facade_a', seed=3)
    facade(kit, 'facade_b', seed=8, balcony=True, seed_off=1.7)
    hydrant(kit)
    trash_bin(kit)
    bench(kit)
    traffic_light(kit)
    phone_booth(kit)
    vending(kit)
    mailbox(kit)
    crates(kit)
    bollard(kit)
    manhole(kit)
    neon_sign(kit)
    rig = flagpole(kit)

    bpy.context.scene.frame_set(1)
    print('[KIT] моделей=%d: %s' % (len(kit.models), ', '.join(sorted(kit.models))))
    N.export_gltf(os.path.join(out, 'street_kit.glb'))
    N.save_blend(os.path.join(out, 'street_kit.blend'))
    N.log_stats(rig)


if __name__ == '__main__':
    main()
