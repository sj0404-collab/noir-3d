#!/usr/bin/env python3
"""Детектив «Нуар-Дет» — аниме-стиль, риг, бесшовные клипы.

Аниме-стиль здесь: голова ~6 ростовых единиц (крупная, как в аниме), худые
конечности, крупные глаза с бликом, чёлка прядями, острые скулы, узкое
пальто с разрезом (не «юбка»). Силуэт держит шляпа, ботинки и лупа.

Риг: 26 костей. Клипы: Idle / Walk / Run / Turn / Point / Scan — все
запечены в бесшовные циклы (см. noirlib.bake_loop), каждый экспортируется
отдельным glTF-клипом.

Запуск:
  blender -b -P tools/make_detective.py -- --out public/models
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import noirlib as N  # noqa: E402

TAU = math.pi * 2
CLIPS = {
    'Idle': 96,
    'Walk': 32,
    'Run': 24,
    'Turn': 40,
    'Point': 24,
    'Scan': 48,
}
STRIDE = {'Idle': 4, 'Walk': 2, 'Run': 2, 'Turn': 3, 'Point': 2, 'Scan': 3}

# ---------------------------------------------------------------- скелет
BONES = [
    ('root', (0, 0, 0), (0, 0, 0.10), None),
    ('hips', (0, 0, 0.88), (0, 0, 0.99), 'root'),
    ('spine', (0, 0, 0.97), (0, 0, 1.09), 'hips'),
    ('chest', (0, 0, 1.07), (0, 0, 1.30), 'spine'),
    ('neck', (0, 0, 1.30), (0, 0, 1.42), 'chest'),
    ('head', (0, 0, 1.40), (0, 0, 1.70), 'neck'),
    # левая рука
    ('shoulder.L', (0.038, 0, 1.290), (0.150, 0, 1.285), 'chest'),
    ('upperarm.L', (0.150, 0, 1.285), (0.152, 0, 1.090), 'shoulder.L'),
    ('forearm.L', (0.152, 0, 1.090), (0.154, 0, 0.900), 'upperarm.L', True),
    ('hand.L', (0.154, 0, 0.900), (0.154, 0, 0.822), 'forearm.L', True),
    # правая рука
    ('shoulder.R', (-0.038, 0, 1.290), (-0.150, 0, 1.285), 'chest'),
    ('upperarm.R', (-0.150, 0, 1.285), (-0.152, 0, 1.090), 'shoulder.R'),
    ('forearm.R', (-0.152, 0, 1.090), (-0.154, 0, 0.900), 'upperarm.R', True),
    ('hand.R', (-0.154, 0, 0.900), (-0.154, 0, 0.822), 'forearm.R', True),
    # ноги
    ('thigh.L', (0.072, 0, 0.860), (0.072, 0, 0.480), 'hips'),
    ('shin.L', (0.072, 0, 0.480), (0.072, 0, 0.110), 'thigh.L', True),
    ('foot.L', (0.072, 0, 0.110), (0.072, -0.160, 0.035), 'shin.L', True),
    ('thigh.R', (-0.072, 0, 0.860), (-0.072, 0, 0.480), 'hips'),
    ('shin.R', (-0.072, 0, 0.480), (-0.072, 0, 0.110), 'thigh.R', True),
    ('foot.R', (-0.072, 0, 0.110), (-0.072, -0.160, 0.035), 'shin.R', True),
    # детали: полы пальто, воротник, поля шляпы, затылочные пряди
    ('coat.L', (0.052, 0, 1.050), (0.052, 0, 0.700), 'hips'),
    ('coat.R', (-0.052, 0, 1.050), (-0.052, 0, 0.700), 'hips'),
    ('collar', (0, 0, 1.300), (0, 0, 1.400), 'chest'),
    ('brim', (0, 0, 1.660), (0, 0, 1.700), 'head'),
    ('hair.back', (0, 0.030, 1.560), (0, 0.085, 1.290), 'head'),
]


def build_rig():
    return N.build_armature(BONES, name='DetectiveRig')


# ---------------------------------------------------------------- тело
def build_body(M):
    """Группы ремешатся ПО ОТДЕЛЬНОСТИ: общий ремеш запаивает суставы
    (так провалилась v2) и ломает деформацию.

    Раскладка по вертикали (рост 1.72 без шляпы, голова 0.285 → ~6 голов):
      подошва 0.00 | ботинок 0.02-0.42 | колено 0.48 | бедро 0.48-0.86
      таз 0.86-0.97 | талия 0.97-1.07 | грудь 1.07-1.30 | шея 1.30-1.42
      подбородок 1.40 | макушка 1.68 | шляпа 1.70-1.82
    """
    groups = {'torso': [], 'arm.L': [], 'arm.R': [], 'leg.L': [], 'leg.R': []}
    props = []

    def add(group, obj, mat):
        N.set_mat(obj, M[mat])
        groups[group].append(obj)
        return obj

    def prop(obj, bone, mat):
        N.set_mat(obj, M[mat])
        obj['bone_hint'] = bone
        props.append(obj)
        return obj

    # ---------------- ТОРС ----------------
    add('torso', N.taper('Pelvis', 0.126, 0.104, 0.17, (0, 0, 0.905), verts=22), 'coat_dark')
    add('torso', N.taper('Waist', 0.104, 0.118, 0.12, (0, 0, 1.010), verts=22), 'coat')
    add('torso', N.taper('Chest', 0.118, 0.132, 0.25, (0, 0, 1.185), verts=22), 'coat')
    # плечевой пояс: он соединяет руки с туловищем
    add('torso', N.taper('Yoke', 0.068, 0.062, 0.300, (0, 0, 1.288), None,
                         rot=(0, math.radians(90), 0), verts=18), 'coat')
    # полы пальто: ДВЕ плоские панели с зазором посередине — читается как
    # пальто с разрезом, а не как юбка (главный косяк v3)
    add('torso', N.taper('CoatFront', 0.122, 0.104, 0.40, (0, -0.038, 0.860), None, verts=16,
                         scale=(1.0, 0.40, 1.0)), 'coat_dark')
    add('torso', N.taper('CoatBack', 0.126, 0.108, 0.40, (0, 0.046, 0.860), None, verts=16,
                         scale=(1.0, 0.42, 1.0)), 'coat_dark')
    add('torso', N.capsule('Neck', 0.042, 0.05, (0, 0, 1.365), None, (1.0, 0.92, 1.0)), 'skin')

    # ---------------- ГОЛОВА (аниме-пропорции) ----------------
    add('torso', N.sphere('Skull', 0.118, (0, 0, 1.552), scale=(0.94, 1.0, 1.06), seg=24, rings=16),
        'skin')
    add('torso', N.sphere('Jaw', 0.084, (0, -0.016, 1.468), scale=(0.86, 0.94, 0.80),
                          seg=20, rings=14), 'skin')
    add('torso', N.sphere('Chin', 0.042, (0, -0.046, 1.418), scale=(0.72, 0.80, 0.62),
                          seg=16, rings=12), 'skin')
    # скулы — аниме-острый силуэт
    for s, sgn in (('L', 1), ('R', -1)):
        add('torso', N.wedge(f'Cheek_{s}', (0.055, 0.030, 0.048), (sgn * 0.052, -0.070, 1.512),
                             rot=(0, 0, 0), bevel=0.010), 'skin')
    add('torso', N.cone('Nose', 0.013, 0.004, 0.032, (0, -0.100, 1.500),
                        rot=(math.radians(96), 0, 0), verts=10), 'skin')
    for s, sgn in (('L', 1), ('R', -1)):
        add('torso', N.sphere(f'Ear_{s}', 0.026, (sgn * 0.108, 0.004, 1.534),
                              scale=(0.45, 0.85, 1.10), seg=12, rings=8), 'skin')

    # ---------------- РУКИ ----------------
    for side, sgn in (('L', 1), ('R', -1)):
        g = f'arm.{side}'
        add(g, N.taper(f'UpperArm_{side}', 0.048, 0.040, 0.20, (sgn * 0.151, 0, 1.190), None, verts=16),
            'coat')
        add(g, N.taper(f'Forearm_{side}', 0.040, 0.030, 0.19, (sgn * 0.153, 0, 0.995), None, verts=16),
            'coat')
        add(g, N.capsule(f'Hand_{side}', 0.036, 0.02, (sgn * 0.154, -0.006, 0.872),
                         None, (0.80, 0.62, 1.15)), 'glove')
        add(g, N.capsule(f'Thumb_{side}', 0.012, 0.013, (sgn * 0.126, -0.026, 0.858)), 'glove')

    # ---------------- НОГИ ----------------
    for side, sgn in (('L', 1), ('R', -1)):
        g = f'leg.{side}'
        add(g, N.taper(f'Thigh_{side}', 0.076, 0.054, 0.38, (sgn * 0.072, 0, 0.670), None, verts=18),
            'coat_dark')
        add(g, N.taper(f'Shin_{side}', 0.054, 0.036, 0.37, (sgn * 0.072, 0, 0.295), None, verts=18),
            'boot')
        add(g, N.sphere(f'Ankle_{side}', 0.042, (sgn * 0.072, 0, 0.115),
                        scale=(1.0, 0.92, 0.85), seg=14, rings=10), 'boot')

    # ---------------- РЕКВИЗИТ ----------------
    # лицо: крупные аниме-глаза с бликом
    for s, sgn in (('L', 1), ('R', -1)):
        prop(N.sphere(f'EyeL_{s}', 0.030, (sgn * 0.050, -0.096, 1.522), None,
                      scale=(1.0, 0.44, 1.30), seg=18, rings=12), 'head', 'eye_white')
        prop(N.sphere(f'Iris_{s}', 0.019, (sgn * 0.050, -0.110, 1.514), None,
                      scale=(1.0, 0.30, 1.15), seg=16, rings=10), 'head', 'eye_iris')
        prop(N.sphere(f'Pupil_{s}', 0.009, (sgn * 0.050, -0.118, 1.512), None,
                      scale=(1.0, 0.30, 1.05), seg=12, rings=8), 'head', 'coat_dark')
        prop(N.sphere(f'Spark_{s}', 0.0085, (sgn * 0.041, -0.122, 1.540), None,
                      seg=10, rings=8), 'head', 'sparkle')
        prop(N.box(f'Lash_{s}', (0.052, 0.010, 0.010), (sgn * 0.050, -0.104, 1.552), None,
                   rot=(0, 0, sgn * 0.10), bevel=0.003), 'head', 'hair')
        prop(N.box(f'Brow_{s}', (0.044, 0.009, 0.008), (sgn * 0.052, -0.098, 1.582), None,
                   rot=(0, sgn * 0.12, sgn * 0.16), bevel=0.003), 'head', 'hair')
    prop(N.box('Mouth', (0.020, 0.008, 0.006), (0, -0.104, 1.452), None, bevel=0.002),
         'head', 'coat_dark')

    # волосы: шапочка + чёлка прядями + боковые пряди + затылок
    prop(N.sphere('HairCap', 0.126, (0, 0.012, 1.596), None, scale=(0.96, 1.0, 1.02),
                  seg=24, rings=16), 'head', 'hair')
    for i, (x, tilt, ln) in enumerate([(-0.062, 0.30, 0.115), (-0.024, 0.18, 0.130),
                                       (0.018, 0.14, 0.135), (0.058, 0.26, 0.110),
                                       (0.092, 0.40, 0.085)]):
        prop(N.cone(f'Bang_{i}', 0.030, 0.005, ln, (x, -0.076, 1.596 - ln * 0.34), None,
                    rot=(math.radians(96) + tilt, 0, 0), verts=10), 'head', 'hair')
        prop(N.cone(f'BangTip_{i}', 0.014, 0.002, 0.040, (x, -0.106, 1.552 - ln * 0.18), None,
                    rot=(math.radians(96) + tilt, 0, 0), verts=8), 'head', 'hair_tip')
    for s, sgn in (('L', 1), ('R', -1)):
        prop(N.taper(f'Lock_{s}', 0.036, 0.012, 0.185, (sgn * 0.108, -0.020, 1.520), None,
                     verts=12), 'head', 'hair')
        prop(N.cone(f'LockTip_{s}', 0.014, 0.002, 0.050, (sgn * 0.112, -0.026, 1.322), None,
                    verts=8), 'head', 'hair_tip')
    prop(N.sphere('HairBack', 0.096, (0, 0.056, 1.480), None, scale=(1.05, 0.80, 1.25),
                  seg=20, rings=14), 'hair.back', 'hair')
    prop(N.cone('HairBackTip', 0.060, 0.010, 0.110, (0, 0.070, 1.330), None,
                rot=(math.radians(-8), 0, 0), verts=12), 'hair.back', 'hair_tip')

    # шляпа
    prop(N.cyl('HatBrim', 0.135, 0.014, (0, -0.008, 1.700), None,
               rot=(math.radians(9), 0, 0), verts=32), 'brim', 'hat')
    prop(N.taper('HatCrown', 0.100, 0.090, 0.090, (0, 0.002, 1.744), None, verts=24), 'brim', 'hat')
    prop(N.taper('HatTop', 0.090, 0.030, 0.045, (0, 0.002, 1.810), None, verts=24), 'brim', 'hat')
    prop(N.cyl('HatBand', 0.102, 0.022, (0, 0.002, 1.712), None, verts=24), 'brim', 'coat_dark')

    # одежда
    prop(N.box('ShirtV', (0.060, 0.016, 0.170), (0, -0.092, 1.360), None, bevel=0.006),
         'chest', 'shirt')
    prop(N.box('Tie', (0.038, 0.011, 0.160), (0, -0.104, 1.340), None, bevel=0.004),
         'chest', 'tie')
    for s, sgn in (('L', 1), ('R', -1)):
        prop(N.box(f'Collar_{s}', (0.078, 0.048, 0.018), (sgn * 0.042, -0.082, 1.452), None,
                   rot=(0.22, 0, sgn * 0.30), bevel=0.005), 'collar', 'coat_dark')
        prop(N.box(f'Lapel_{s}', (0.046, 0.013, 0.190), (sgn * 0.070, -0.084, 1.372), None,
                   rot=(0, sgn * 0.22, sgn * 0.10), bevel=0.005), 'chest', 'coat_dark')
        prop(N.cyl(f'Cuff_{s}', 0.036, 0.024, (sgn * 0.153, 0, 0.920), None, verts=14),
             f'forearm.{s}', 'shirt')
        # высокие ботинки детектива
        prop(N.box(f'BootShaft_{s}', (0.072, 0.170, 0.330), (sgn * 0.072, -0.004, 0.240), None,
                   bevel=0.020), f'shin.{s}', 'boot')
        prop(N.box(f'BootFoot_{s}', (0.076, 0.215, 0.095), (sgn * 0.072, -0.050, 0.062), None,
                   bevel=0.018), f'foot.{s}', 'boot')
        prop(N.box(f'Sole_{s}', (0.084, 0.230, 0.024), (sgn * 0.072, -0.054, 0.016), None,
                   bevel=0.006), f'foot.{s}', 'coat_dark')
    prop(N.box('Belt', (0.250, 0.205, 0.032), (0, 0, 1.028), None, bevel=0.006), 'hips', 'boot')
    prop(N.box('Buckle', (0.046, 0.018, 0.040), (0, -0.112, 1.028), None, bevel=0.005),
         'hips', 'metal')
    prop(N.capsule('Pin', 0.007, 0.003, (0.062, -0.092, 1.402), None, (1.0, 0.4, 1.0)),
         'chest', 'metal')
    # лупа в руке
    prop(N.cyl('MagRing', 0.040, 0.006, (0.212, -0.030, 0.862), None,
               rot=(math.pi / 2, 0, 0), verts=20), 'hand.L', 'metal')
    prop(N.cyl('MagGlass', 0.035, 0.004, (0.212, -0.030, 0.862), None,
               rot=(math.pi / 2, 0, 0), verts=20), 'hand.L', 'lamp_warm')
    prop(N.cyl('MagHandle', 0.008, 0.070, (0.212, -0.062, 0.828), None,
               rot=(0.55, 0, 0), verts=10), 'hand.L', 'metal')
    return groups, props


# ---------------------------------------------------------------- клипы
def _body_base():
    """Нейтраль: плечи опущены, локти согнуты — общая база всех поз."""
    return {
        'shoulder.L': (0, 0, -0.05), 'shoulder.R': (0, 0, 0.05),
        'upperarm.L': (-0.14, 0, 0.05), 'upperarm.R': (-0.14, 0, -0.05),
        'forearm.L': (-0.26, 0, 0), 'forearm.R': (-0.26, 0, 0),
        'thigh.L': (0, 0, 0), 'thigh.R': (0, 0, 0),
        'shin.L': (0, 0, 0), 'shin.R': (0, 0, 0),
        'foot.L': (0, 0, 0), 'foot.R': (0, 0, 0),
        'hips': (0, 0, 0), 'spine': (0, 0, 0), 'chest': (0, 0, 0),
        'neck': (0, 0, 0), 'head': (0, 0, 0), 'root': (0, 0, 0, (0, 0, 0)),
        'coat.L': (0, 0, 0), 'coat.R': (0, 0, 0), 'collar': (0, 0, 0),
        'brim': (0, 0, 0), 'hair.back': (0, 0, 0),
    }


def pose_idle(u):
    p = _body_base()
    ph = TAU * u
    sway = math.sin(ph)
    breath = math.sin(ph * 2)
    slow = math.sin(ph * 0.5)
    p['root'] = (0, sway * 0.030, 0, (0, 0, breath * 0.010))
    p['spine'] = (breath * 0.030, sway * 0.035, 0)
    p['chest'] = (breath * 0.022, -sway * 0.022, 0)
    p['neck'] = (breath * 0.020, sway * 0.028, 0)
    p['head'] = (-breath * 0.030 + 0.015, slow * 0.080, slow * 0.030)
    p['shoulder.L'] = (0, 0, -0.05 - breath * 0.020)
    p['shoulder.R'] = (0, 0, 0.05 - breath * 0.020)
    p['upperarm.L'] = (-0.14 - breath * 0.030, 0, 0.05)
    p['upperarm.R'] = (-0.14 - breath * 0.030, 0, -0.05)
    p['forearm.L'] = (-0.26, 0, 0)
    p['forearm.R'] = (-0.26, 0, 0)
    p['coat.L'] = (math.sin(ph + 0.6) * 0.040, 0, 0)
    p['coat.R'] = (math.sin(ph + 1.1) * 0.040, 0, 0)
    p['hair.back'] = (math.sin(ph - 0.4) * 0.030, math.sin(ph) * 0.040, 0)
    p['brim'] = (math.sin(ph - 0.4) * 0.020, 0, 0)
    return p


def _knee(u_leg, amp, base=0.04):
    """Сгиб колена. max(0,-cos) имеет излом в фазе проноса — берём квадрат,
    тогда кривая гладкая (C1) и стык цикла не дёргает ногу."""
    return base + amp * (max(0.0, -math.cos(TAU * u_leg)) ** 2)


def pose_walk(u):
    p = _body_base()
    ph = TAU * u
    s, c = math.sin(ph), math.cos(ph)
    p['thigh.L'] = (s * 0.50, 0, 0.02)
    p['thigh.R'] = (-s * 0.50, 0, -0.02)
    p['shin.L'] = (_knee((u + 0.25) % 1.0, 0.95), 0, 0)
    p['shin.R'] = (_knee((u + 0.75) % 1.0, 0.95), 0, 0)
    p['foot.L'] = (-s * 0.20, 0, 0)
    p['foot.R'] = (s * 0.20, 0, 0)
    p['root'] = (0.02, 0, c * 0.055, (0, 0, -0.012 + 0.024 * math.cos(2 * ph)))
    p['hips'] = (0, c * 0.075, c * 0.040)
    p['spine'] = (0.03, -c * 0.040, 0)
    p['chest'] = (0, -c * 0.085, 0)
    p['neck'] = (0.02, c * 0.045, 0)
    p['head'] = (0, c * 0.050, 0)
    p['shoulder.L'] = (0, 0, -0.05)
    p['shoulder.R'] = (0, 0, 0.05)
    p['upperarm.L'] = (-s * 0.40 - 0.10, 0, 0.06)
    p['upperarm.R'] = (s * 0.40 - 0.10, 0, -0.06)
    p['forearm.L'] = (-0.22 - max(0.0, s) ** 2 * 0.35, 0, 0)
    p['forearm.R'] = (-0.22 - max(0.0, -s) ** 2 * 0.35, 0, 0)
    p['coat.L'] = (-math.sin(ph - 0.5) * 0.15, 0, 0)
    p['coat.R'] = (-math.sin(ph - 0.5) * 0.15, 0, 0)
    p['hair.back'] = (math.sin(ph - 0.8) * 0.045, math.sin(ph - 0.6) * 0.050, 0)
    p['brim'] = (math.sin(ph - 0.8) * 0.030, 0, 0)
    p['collar'] = (0, 0, math.sin(ph - 0.5) * 0.020)
    return p


def pose_run(u):
    p = _body_base()
    ph = TAU * u
    s, c = math.sin(ph), math.cos(ph)
    p['thigh.L'] = (s * 0.92, 0, 0.03)
    p['thigh.R'] = (-s * 0.92, 0, -0.03)
    p['shin.L'] = (_knee((u + 0.20) % 1.0, 1.75, base=0.10), 0, 0)
    p['shin.R'] = (_knee((u + 0.70) % 1.0, 1.75, base=0.10), 0, 0)
    p['foot.L'] = (-s * 0.38, 0, 0)
    p['foot.R'] = (s * 0.38, 0, 0)
    p['root'] = (0.16, 0, c * 0.080, (0, 0, -0.030 + 0.055 * math.cos(2 * ph)))
    p['hips'] = (0, c * 0.130, c * 0.050)
    p['spine'] = (0.10, -c * 0.070, 0)
    p['chest'] = (0.06, -c * 0.150, 0)
    p['neck'] = (0.05, c * 0.070, 0)
    p['head'] = (-0.06, c * 0.080, 0)
    p['shoulder.L'] = (0, 0, -0.07)
    p['shoulder.R'] = (0, 0, 0.07)
    p['upperarm.L'] = (-s * 0.90 - 0.30, 0, 0.10)
    p['upperarm.R'] = (s * 0.90 - 0.30, 0, -0.10)
    p['forearm.L'] = (-0.95 - max(0.0, s) ** 2 * 0.45, 0, 0)
    p['forearm.R'] = (-0.95 - max(0.0, -s) ** 2 * 0.45, 0, 0)
    p['coat.L'] = (-math.sin(ph - 0.4) * 0.34, 0, 0)
    p['coat.R'] = (-math.sin(ph - 0.4) * 0.34, 0, 0)
    p['hair.back'] = (math.sin(ph - 1.1) * 0.085, math.sin(ph - 0.9) * 0.075, 0)
    p['brim'] = (math.sin(ph - 1.0) * 0.050, 0, 0)
    return p


def pose_turn(u):
    """Оглядывание: поворот влево-вправо через плечо. Цикл."""
    p = _body_base()
    ph = TAU * u
    k = math.sin(ph)
    p['root'] = (0, k * 0.480, 0, (0, 0, 0))
    p['hips'] = (0, k * 0.200, 0)
    p['spine'] = (0, -k * 0.130, 0)
    p['chest'] = (0, -k * 0.170, 0)
    p['neck'] = (0, k * 0.400, 0)
    p['head'] = (0, k * 0.520, k * 0.060)
    p['brim'] = (0, k * 0.180, 0)
    p['coat.L'] = (0, k * 0.120, 0)
    p['coat.R'] = (0, k * 0.120, 0)
    p['hair.back'] = (0, k * 0.160, 0)
    p['upperarm.L'] = (-0.10, 0, 0.08)
    p['upperarm.R'] = (-0.10, 0, -0.08)
    return p


def _smoothstep(x):
    """Гладкий 0→1 с нулевыми производными на концах — без рывка в стыке цикла."""
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def pose_point(u):
    """Нуар-указание: рука вперёд, палец на «виновника». Цикл."""
    p = _body_base()
    ph = TAU * u
    if u < 0.35:
        t = _smoothstep(u / 0.35)
    elif u < 0.60:
        t = 1.0
    else:
        t = 1.0 - _smoothstep((u - 0.60) / 0.40)
    p['shoulder.R'] = (0, 0, 0.05 + t * 0.10)
    p['upperarm.R'] = (-0.14 - t * 1.05, 0, -0.05 - t * 0.10)
    p['forearm.R'] = (-0.26 - t * 0.30, 0, 0)
    p['chest'] = (0, -t * 0.14, 0)
    p['neck'] = (0, t * 0.10, 0)
    p['head'] = (0, t * 0.16, 0)
    p['spine'] = (0, -t * 0.06, 0)
    p['root'] = (0, 0, 0, (0, 0, t * 0.012))
    p['upperarm.L'] = (-0.20 - t * 0.06, 0, 0.05)
    p['coat.L'] = (math.sin(ph) * 0.03, 0, 0)
    p['coat.R'] = (-t * 0.12 + math.sin(ph) * 0.03, 0, 0)
    p['hair.back'] = (0, math.sin(ph) * 0.04, 0)
    return p


def pose_scan(u):
    """Осматривается: голова ходит из стороны в сторону, лёгкий присед. Цикл."""
    p = _body_base()
    ph = TAU * u
    k = math.sin(ph)
    slow = math.sin(ph * 0.5)
    p['root'] = (0.04, 0, 0, (0, 0, -0.020 + 0.012 * math.cos(2 * ph)))
    p['hips'] = (0.02, k * 0.060, 0)
    p['spine'] = (0.03, -k * 0.050, 0)
    p['chest'] = (0.04, -k * 0.090, 0)
    p['neck'] = (0.03, k * 0.200, 0)
    p['head'] = (0.02, k * 0.520, slow * 0.060)
    p['brim'] = (0, k * 0.200, slow * 0.040)
    p['upperarm.L'] = (-0.20, 0, 0.10)
    p['upperarm.R'] = (-0.20, 0, -0.10)
    p['forearm.L'] = (-0.55, 0, 0)
    p['forearm.R'] = (-0.55, 0, 0)
    p['thigh.L'] = (-0.10, 0, 0.04)
    p['thigh.R'] = (-0.10, 0, -0.04)
    p['shin.L'] = (0.22, 0, 0)
    p['shin.R'] = (0.22, 0, 0)
    p['coat.L'] = (k * 0.10, 0, 0)
    p['coat.R'] = (k * 0.10, 0, 0)
    p['hair.back'] = (k * 0.070, k * 0.080, 0)
    return p


POSES = {
    'Idle': pose_idle,
    'Walk': pose_walk,
    'Run': pose_run,
    'Turn': pose_turn,
    'Point': pose_point,
    'Scan': pose_scan,
}


# ---------------------------------------------------------------- сборка
def main():
    out, only = N.parse_args()
    if only and os.path.basename(__file__).replace('.py', '') not in only:
        print('[SKIP] %s' % os.path.basename(__file__))
        return
    N.reset_scene()
    os.makedirs(out, exist_ok=True)
    N.setup_scene(max(CLIPS.values()))

    M = N.make_materials()
    M['sparkle'] = N.mat('sparkle', (1.0, 1.0, 1.0, 1.0), rough=0.05,
                         emit=(1.0, 1.0, 1.0, 1.0), emit_strength=4.0)
    M['hair_tip'] = N.mat('hair_tip', (0.30, 0.34, 0.56, 1.0), rough=0.45,
                          emit=(0.16, 0.20, 0.40, 1.0), emit_strength=0.5)
    M['eye_iris'] = N.mat('eye_iris', (0.18, 0.62, 0.80, 1.0), rough=0.15,
                          emit=(0.10, 0.45, 0.70, 1.0), emit_strength=1.4)
    M['eye_white'] = N.mat('eye_white', (0.94, 0.95, 0.98, 1.0), rough=0.18,
                           emit=(0.55, 0.60, 0.70, 1.0), emit_strength=0.5)

    rig = build_rig()
    groups, props = build_body(M)
    bpy.context.view_layer.update()

    bodies = []
    for gname, parts in groups.items():
        if not parts:
            continue
        g = N.fuse_body(parts, name='Body_' + gname.replace('.', '_'), voxel=0.011)
        N.skin_character(g, rig, hint=gname)
        bodies.append(g)
        print('[GROUP] %-6s вершин=%d' % (gname, len(g.data.vertices)))

    bones = {b.name for b in rig.data.bones}
    for p in props:
        hint = p.get('bone_hint', 'chest')
        if hint not in bones:
            hint = 'chest'
        N.bind_rigid(p, rig, hint)
    print('[PROPS] привязано=%d' % len(props))

    clips = {}
    for name, fn in POSES.items():
        action = N.bake_loop(rig, CLIPS[name], fn, stride=STRIDE[name])
        N.stage_clip(rig, action, name)
        clips[name] = action
    bpy.context.scene.frame_set(1)

    N.export_gltf(os.path.join(out, 'detective.glb'))
    N.save_blend(os.path.join(out, 'detective.blend'))
    N.log_stats(rig, clips)


if __name__ == '__main__':
    main()
