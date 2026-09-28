#!/usr/bin/env python3
"""Транспорт Ноктиса: седан и трамвай.

Колёса висят на костях (как у настоящего рига), поэтому крутятся, а не
«плывут» текстурой. Анимации: `Drive` (езда, бесшовный цикл), `Idle`
(стоянка, дрожь мотора), `Siren` (мигалка), у трамвая — `Run`.

Запуск:
  blender -b -P tools/make_vehicles.py -- --out public/models
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import noirlib as N  # noqa: E402

TAU = math.pi * 2
CAR_CLIPS = {'Idle': 48, 'Drive': 48, 'Siren': 24}
TRAM_CLIPS = {'Run': 60}


# ---------------------------------------------------------------- СЕДАН
CAR_BONES = [
    ('root', (0, 0, 0), (0, 0, 0.12), None),
    ('chassis', (0, 0, 0.30), (0, 0, 0.95), 'root'),
    ('beacon', (0, 0.35, 1.62), (0, 0.20, 1.62), 'chassis'),
    ('wheel.FL', (0.60, 1.32, 0.34), (0.95, 1.32, 0.34), 'chassis'),
    ('wheel.FR', (-0.60, 1.32, 0.34), (-0.95, 1.32, 0.34), 'chassis'),
    ('wheel.RL', (0.60, -1.30, 0.34), (0.95, -1.30, 0.34), 'chassis'),
    ('wheel.RR', (-0.60, -1.30, 0.34), (-0.95, -1.30, 0.34), 'chassis'),
]


def build_car(M):
    rig = N.build_armature(CAR_BONES, name='CarRig')
    parts = []

    # ---------------- кузов ----------------
    parts.append(N.box('BodyLower', (1.78, 4.24, 0.56), (0, 0, 0.66), None, bevel=0.16))
    parts.append(N.box('BodySill', (1.86, 3.60, 0.20), (0, 0, 0.44), None, bevel=0.07))
    parts.append(N.box('Hood', (1.68, 1.44, 0.26), (0, 1.32, 0.98), None,
                       rot=(-0.10, 0, 0), bevel=0.12))
    parts.append(N.box('Trunk', (1.66, 1.16, 0.24), (0, -1.52, 0.98), None,
                       rot=(0.08, 0, 0), bevel=0.10))
    parts.append(N.box('Cabin', (1.62, 2.16, 0.62), (0, -0.22, 1.22), None, bevel=0.24))
    parts.append(N.box('Roof', (1.44, 1.70, 0.12), (0, -0.28, 1.56), None, bevel=0.06))
    # острые «аниме» скулы кузова
    for s, sgn in (('L', 1), ('R', -1)):
        parts.append(N.wedge(f'Flare_{s}', (0.10, 1.30, 0.26), (sgn * 0.86, -0.20, 0.80),
                             rot=(0, 0, 0), bevel=0.04))
        parts.append(N.box(f'Mirror_{s}', (0.16, 0.24, 0.10), (sgn * 0.92, 0.72, 1.28), None,
                           rot=(0, 0, sgn * 0.20), bevel=0.03))
        parts.append(N.box(f'Handle_{s}', (0.06, 0.20, 0.05), (sgn * 0.86, 0.10, 1.00), None,
                           bevel=0.02))
    # бампера и решётка
    parts.append(N.box('BumperF', (1.84, 0.26, 0.24), (0, 2.12, 0.62), None, bevel=0.07))
    parts.append(N.box('BumperR', (1.84, 0.24, 0.24), (0, -2.12, 0.62), None, bevel=0.07))
    parts.append(N.box('Grille', (1.10, 0.10, 0.20), (0, 2.16, 0.86), None, bevel=0.03))
    parts.append(N.cyl('Exhaust', 0.07, 0.30, (0.42, -2.20, 0.44), None,
                       rot=(math.pi / 2, 0, 0), verts=10))

    body_parts = list(parts)
    glass_parts, trim_parts = [], []
    # ---------------- стёкла ----------------
    glass_parts.append(N.box('Windshield', (1.44, 0.08, 0.60), (0, 0.86, 1.24), None,
                             rot=(-0.62, 0, 0), bevel=0.03))
    glass_parts.append(N.box('RearGlass', (1.40, 0.08, 0.52), (0, -1.32, 1.24), None,
                             rot=(0.58, 0, 0), bevel=0.03))
    for s, sgn in (('L', 1), ('R', -1)):
        glass_parts.append(N.box(f'SideGlass_{s}', (0.06, 1.86, 0.48), (sgn * 0.80, -0.22, 1.26),
                                 None, bevel=0.02))
    # ---------------- свет ----------------
    head_parts, tail_parts = [], []
    for s, sgn in (('L', 1), ('R', -1)):
        head_parts.append(N.cyl(f'Head_{s}', 0.15, 0.10, (sgn * 0.58, 2.10, 0.84), None,
                                rot=(math.pi / 2, 0, 0), verts=16))
        tail_parts.append(N.box(f'Tail_{s}', (0.30, 0.08, 0.12), (sgn * 0.62, -2.14, 0.86),
                                None, bevel=0.02))
    # мигалка на крыше: корпус на кости beacon, стекло мигает масштабом
    beacon = N.box('BeaconBar', (0.92, 0.24, 0.10), (0, 0.28, 1.66), None, bevel=0.03)
    beacon_glass = N.box('BeaconGlass', (0.76, 0.18, 0.08), (0, 0.28, 1.70), None, bevel=0.02)
    trim_parts.append(N.box('BeaconBase', (1.02, 0.32, 0.06), (0, 0.28, 1.62), None, bevel=0.02))

    # ---------------- колёса ----------------
    wheels = []
    for name, (x, y, z) in (('FL', (0.84, 1.32, 0.34)), ('FR', (-0.84, 1.32, 0.34)),
                            ('RL', (0.84, -1.30, 0.34)), ('RR', (-0.84, -1.30, 0.34))):
        tire = N.cyl(f'Wheel{name}', 0.34, 0.22, (x, y, z), None, rot=(0, math.pi / 2, 0), verts=24)
        rim = N.cyl(f'Rim{name}', 0.20, 0.24, (x, y, z), None, rot=(0, math.pi / 2, 0), verts=18)
        spokes = []
        for i in range(5):
            a = TAU * i / 5
            spokes.append(N.box(f'Spoke{name}{i}', (0.05, 0.17, 0.045),
                                (x + 0.02 * (1 if x > 0 else -1), y + math.cos(a) * 0.10,
                                 z + math.sin(a) * 0.10), None, rot=(-a, 0, 0), bevel=0.01))
        spoke_obj = N.join_parts(spokes, f'Spokes{name}')
        spoke_obj.data.materials.clear()
        spoke_obj.data.materials.append(M['chrome'])
        wheels.append((f'wheel.{"".join(name)}', tire, rim, spoke_obj))

    # ---------------- сборка по материалам ----------------
    body = N.join_parts(body_parts, 'CarBody')
    N.set_mat(body, M['car_body'])
    glass = N.join_parts(glass_parts, 'CarGlass')
    N.set_mat(glass, M['glass'])
    trim = N.join_parts(trim_parts, 'CarTrim')
    N.set_mat(trim, M['metal_dark'])
    head = N.join_parts(head_parts, 'CarHead')
    N.set_mat(head, M['lamp_warm'])
    tail = N.join_parts(tail_parts, 'CarTail')
    N.set_mat(tail, M['neon_pink'])
    N.set_mat(beacon, M['metal_dark'])
    N.set_mat(beacon_glass, M['neon_cyan'])

    for bone, tire, rim, spoke in wheels:
        N.bind_rigid(tire, rig, bone)
        N.bind_rigid(rim, rig, bone)
        N.bind_rigid(spoke, rig, bone)

    for obj in (body, glass, trim, head, tail):
        N.bind_rigid(obj, rig, 'chassis')
    N.bind_rigid(beacon, rig, 'beacon')
    N.bind_rigid(beacon_glass, rig, 'beacon')
    return rig


def pose_car_idle(u):
    ph = TAU * u
    buzz = math.sin(ph * 6)
    return {
        'chassis': (buzz * 0.002, math.sin(ph * 3 + 0.5) * 0.002, 0, (0, 0, buzz * 0.004)),
        'beacon': (0, 0, 0),
    }


def pose_car_drive(u):
    ph = TAU * u
    spin = -TAU * 2.0 * u  # два оборота за цикл: ровно целое число -> бесшовность
    bump = math.sin(ph * 2)
    p = {
        'chassis': (math.sin(ph) * 0.006, math.sin(ph * 2 + 0.7) * 0.005, math.sin(ph) * 0.004,
                    (0, 0, bump * 0.012)),
        'beacon': (0, 0, 0),
    }
    for b in ('wheel.FL', 'wheel.FR', 'wheel.RL', 'wheel.RR'):
        p[b] = (0, spin, 0)
    return p


def pose_car_siren(u):
    """Мигалка: масштаб стекла мигает — в glTF нет анимации эмиссии."""
    ph = TAU * u
    on_a = 1.0 if (u < 0.25 or (0.5 <= u < 0.75)) else 0.12
    on_b = 1.0 if (0.25 <= u < 0.5 or u >= 0.75) else 0.12
    p = {
        'chassis': (0, 0, 0, (0, 0, math.sin(ph * 6) * 0.003)),
        'beacon': (0, 0, 0, (0, 0, 0), (1, on_b, 1)),
    }
    for b in ('wheel.FL', 'wheel.FR', 'wheel.RL', 'wheel.RR'):
        p[b] = (0, 0, 0)
    p['root'] = (0, 0, 0, (0, 0, 0), (1, 1, 1))
    return p


# ---------------------------------------------------------------- ТРАМВАЙ
TRAM_BONES = [
    ('root', (0, 0, 0), (0, 0, 0.15), None),
    ('chassis', (0, 0, 0.30), (0, 0, 1.10), 'root'),
    ('body', (0, 0, 1.10), (0, 0, 2.20), 'chassis'),
    ('panto', (0, 1.60, 3.42), (0, 1.10, 3.86), 'body'),
    ('wheel.FL', (0.70, 3.60, 0.42), (0.98, 3.60, 0.42), 'chassis'),
    ('wheel.FR', (-0.70, 3.60, 0.42), (-0.98, 3.60, 0.42), 'chassis'),
    ('wheel.ML', (0.70, 2.90, 0.42), (0.98, 2.90, 0.42), 'chassis'),
    ('wheel.MR', (-0.70, 2.90, 0.42), (-0.98, 2.90, 0.42), 'chassis'),
    ('wheel.BL', (0.70, -3.60, 0.42), (0.98, -3.60, 0.42), 'chassis'),
    ('wheel.BR', (-0.70, -3.60, 0.42), (-0.98, -3.60, 0.42), 'chassis'),
    ('wheel.AL', (0.70, -2.90, 0.42), (0.98, -2.90, 0.42), 'chassis'),
    ('wheel.AR', (-0.70, -2.90, 0.42), (-0.98, -2.90, 0.42), 'chassis'),
]


def build_tram(M):
    rig = N.build_armature(TRAM_BONES, name='TramRig')
    body_parts, glass_parts, trim_parts, head_parts, sign_parts, panto_parts = [], [], [], [], [], []

    # ---------------- кузов ----------------
    body_parts.append(N.box('Shell', (2.42, 11.20, 2.30), (0, 0, 2.10), None, bevel=0.30))
    body_parts.append(N.box('Skirt', (2.30, 10.60, 0.52), (0, 0, 1.16), None, bevel=0.12))
    body_parts.append(N.box('RoofArc', (2.20, 10.40, 0.44), (0, 0, 3.30), None, bevel=0.20))
    for s, sgn in (('F', 1), ('B', -1)):
        body_parts.append(N.box(f'Nose_{s}', (2.20, 0.60, 1.90), (0, sgn * 5.70, 2.20), None,
                                rot=(sgn * 0.10, 0, 0), bevel=0.26))
    # окна по бортам
    for s, sgn in (('L', 1), ('R', -1)):
        for i in range(5):
            y = -4.30 + i * 2.15
            glass_parts.append(N.box(f'Win_{s}{i}', (0.10, 1.86, 1.02), (sgn * 1.22, y, 2.52),
                                     None, bevel=0.04))
        # двери
        for i, y in enumerate((-3.0, 0.2, 3.4)):
            trim_parts.append(N.box(f'Door_{s}{i}', (0.10, 1.10, 1.90), (sgn * 1.24, y, 1.98),
                                    None, bevel=0.05))
            glass_parts.append(N.box(f'DoorGlass_{s}{i}', (0.08, 0.86, 0.90),
                                     (sgn * 1.27, y, 2.60), None, bevel=0.02))
    glass_parts.append(N.box('WinFront', (1.90, 0.12, 1.02), (0, 5.62, 2.52), None,
                             rot=(0.18, 0, 0), bevel=0.04))
    glass_parts.append(N.box('WinBack', (1.90, 0.12, 1.02), (0, -5.62, 2.52), None,
                             rot=(-0.18, 0, 0), bevel=0.04))
    # лобовое стекло водителя ниже
    glass_parts.append(N.box('CabGlass', (1.70, 0.10, 0.70), (0, 5.70, 1.72), None,
                             rot=(0.16, 0, 0), bevel=0.03))
    # фары и destination-табло
    for s, sgn in (('F', 1), ('B', -1)):
        for sx, sg in (('L', 1), ('R', -1)):
            head_parts.append(N.cyl(f'Head_{s}{sx}', 0.13, 0.10,
                                    (sg * 0.78, sgn * 5.92, 1.30), None,
                                    rot=(math.pi / 2, 0, 0), verts=14))
    sign_parts.append(N.box('Sign', (1.70, 0.10, 0.30), (0, 5.86, 3.02), None, bevel=0.03))
    trim_parts.append(N.box('RoofVent', (1.20, 3.20, 0.22), (0, 0, 3.54), None, bevel=0.08))
    trim_parts.append(N.box('Coupler', (0.42, 0.70, 0.30), (0, -6.20, 1.10), None, bevel=0.06))

    # ---------------- пантограф ----------------
    panto_parts.append(N.box('PantoBase', (1.40, 1.20, 0.12), (0, 1.60, 3.56), None, bevel=0.04))
    panto_parts.append(N.box('PantoArm1', (0.08, 1.90, 0.08), (0, 1.05, 3.80), None,
                             rot=(-0.62, 0, 0), bevel=0.02))
    panto_parts.append(N.box('PantoArm2', (0.08, 1.90, 0.08), (0, 2.15, 3.80), None,
                             rot=(0.62, 0, 0), bevel=0.02))
    panto_parts.append(N.box('PantoBar', (1.60, 0.10, 0.06), (0, 1.60, 3.94), None, bevel=0.02))

    body = N.join_parts(body_parts, 'TramBody')
    N.set_mat(body, M['tram_body'])
    glass = N.join_parts(glass_parts, 'TramGlass')
    N.set_mat(glass, M['glass'])
    trim = N.join_parts(trim_parts, 'TramTrim')
    N.set_mat(trim, M['tram_trim'])
    head = N.join_parts(head_parts, 'TramHead')
    N.set_mat(head, M['lamp_warm'])
    sign = N.join_parts(sign_parts, 'TramSign')
    N.set_mat(sign, M['neon_cyan'])
    panto = N.join_parts(panto_parts, 'Pantograph')
    N.set_mat(panto, M['metal_dark'])

    for obj in (body, glass, trim, head, sign):
        N.bind_rigid(obj, rig, 'body')
    N.bind_rigid(panto, rig, 'panto')

    for name, (x, y, z) in (('FL', (0.86, 3.60, 0.42)), ('FR', (-0.86, 3.60, 0.42)),
                            ('ML', (0.86, 2.90, 0.42)), ('MR', (-0.86, 2.90, 0.42)),
                            ('BL', (0.86, -3.60, 0.42)), ('BR', (-0.86, -3.60, 0.42)),
                            ('AL', (0.86, -2.90, 0.42)), ('AR', (-0.86, -2.90, 0.42))):
        tire = N.cyl(f'Wheel{name}', 0.42, 0.20, (x, y, z), None, rot=(0, math.pi / 2, 0), verts=22)
        rim = N.cyl(f'Rim{name}', 0.24, 0.22, (x, y, z), None, rot=(0, math.pi / 2, 0), verts=16)
        spokes = []
        for i in range(6):
            a = TAU * i / 6
            spokes.append(N.box(f'Spoke{name}{i}', (0.05, 0.20, 0.045),
                                (x + 0.02 * (1 if x > 0 else -1), y + math.cos(a) * 0.12,
                                 z + math.sin(a) * 0.12), None, rot=(-a, 0, 0), bevel=0.01))
        spoke_obj = N.join_parts(spokes, f'Spokes{name}')
        N.set_mat(spoke_obj, M['chrome'])
        for obj in (tire, rim, spoke_obj):
            N.bind_rigid(obj, rig, f'wheel.{name}')

    # тележки: рычаги подвески на костях chassis
    for sgn in (1, -1):
        for sx in (1, -1):
            N.bind_rigid(N.box(f'Bogey_{sgn}{sx}', (0.16, 1.30, 0.20),
                               (sx * 0.94, sgn * 3.25, 0.62), None, bevel=0.04), rig, 'chassis')
    return rig


def pose_tram_run(u):
    ph = TAU * u
    spin = -TAU * 1.5 * u  # полтора оборота -> целое за цикл
    p = {
        'chassis': (math.sin(ph) * 0.004, math.sin(ph * 2) * 0.003, 0,
                    (0, 0, math.sin(ph * 2 + 0.4) * 0.016)),
        'body': (math.sin(ph) * 0.006, math.sin(ph) * 0.010, math.sin(ph) * 0.004),
        'panto': (math.sin(ph + 0.9) * 0.010, 0, 0),
    }
    for b in ('wheel.FL', 'wheel.FR', 'wheel.ML', 'wheel.MR',
              'wheel.BL', 'wheel.BR', 'wheel.AL', 'wheel.AR'):
        p[b] = (0, spin, 0)
    return p


# ---------------------------------------------------------------- main
def main():
    out, only = N.parse_args()
    if only and os.path.basename(__file__).replace('.py', '') not in only:
        print('[SKIP] %s' % os.path.basename(__file__))
        return
    os.makedirs(out, exist_ok=True)
    N.setup_scene(60)

    # ---------------- седан ----------------
    N.reset_scene()
    M = N.make_materials()
    rig = build_car(M)
    car_clips = {}
    for name, fn in (('Idle', pose_car_idle), ('Drive', pose_car_drive), ('Siren', pose_car_siren)):
        action = N.bake_loop(rig, CAR_CLIPS[name], fn, stride=2)
        N.stage_clip(rig, action, name)
        car_clips[name] = action
    bpy.context.scene.frame_set(1)
    N.export_gltf(os.path.join(out, 'car.glb'))
    N.log_stats(rig, car_clips)
    N.save_blend(os.path.join(out, 'car.blend'))

    # ---------------- трамвай ----------------
    N.reset_scene()
    M = N.make_materials()
    rig = build_tram(M)
    tram_clips = {}
    action = N.bake_loop(rig, TRAM_CLIPS['Run'], pose_tram_run, stride=3)
    N.stage_clip(rig, action, 'Run')
    tram_clips['Run'] = action
    bpy.context.scene.frame_set(1)
    N.export_gltf(os.path.join(out, 'tram.glb'))
    N.log_stats(rig, tram_clips)
    N.save_blend(os.path.join(out, 'tram.blend'))


if __name__ == '__main__':
    main()
