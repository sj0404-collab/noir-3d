#!/usr/bin/env python3
"""
Генератор стилизованного нуар-детектива для «Нуар-Дет».

Собирает персонажа из примитивов с настоящим арматурным скелетом
и процедурными анимациями (покой / шаг / бег), экспортирует в glTF.

Запуск:
  blender -b -P tools/make_detective.py -- --out public/models
"""
import bpy
import math
import os
import sys
from mathutils import Vector

# ---------------------------------------------------------------- параметры
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[ARGS.index('--out') + 1] if '--out' in ARGS else 'public/models'
FPS = 30
# кадры анимаций (в кадрах при FPS)
CLIPS = {
    'Idle': 96,
    'Walk': 32,
    'Run': 24,
    'Turn': 40,
}

# палитра нуар-стиля
C_COAT = (0.055, 0.060, 0.075, 1.0)
C_COAT_DARK = (0.028, 0.031, 0.040, 1.0)
C_SHIRT = (0.52, 0.50, 0.46, 1.0)
C_TIE = (0.28, 0.055, 0.070, 1.0)
C_SKIN = (0.66, 0.48, 0.38, 1.0)
C_HAT = (0.045, 0.048, 0.060, 1.0)
C_BOOT = (0.030, 0.030, 0.036, 1.0)
C_GLOVE = (0.10, 0.09, 0.10, 1.0)
C_HAIR = (0.10, 0.085, 0.075, 1.0)
C_METAL = (0.62, 0.50, 0.24, 1.0)


def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions,
                  bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            block.remove(item)


def mat(name, color, rough=0.55, metal=0.0, emit=None, emit_strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit is not None:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emit
            bsdf.inputs['Emission Strength'].default_value = emit_strength
        else:
            bsdf.inputs['Emission'].default_value = emit
    return m


def apply_all(obj):
    """Впечатывает location/scale/rotation в данные меша: узел остаётся единичным.
    Иначе glTF-узлы несут масштабы и ломают скиннинг."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def shade_smooth(obj, angle=0.6):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    # auto-smooth через модификатор (в 4.1+ shade_auto_smooth)
    try:
        bpy.ops.object.shade_auto_smooth(angle=angle)
    except Exception:
        mod = obj.modifiers.new('SmoothByAngle', 'SMOOTH_BY_ANGLE')
        mod.angle = angle


def capsule(name, radius, length, material, location=(0, 0, 0), scale=(1, 1, 1)):
    """Капсула вдоль Z: используется и как кость-«труба», и как деталь."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=20, ring_count=12)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (scale[0], scale[1], scale[2] * (1 + length / max(radius, 1e-4)))
    if material:
        obj.data.materials.append(material)
    shade_smooth(obj)
    apply_all(obj)
    return obj


def taper(name, r_bottom, r_top, length, location, material, rot=(0, 0, 0), verts=18):
    """Сужающаяся труба вдоль локальной Z — основа конечностей и торса.
    Капсулы давали «картошку», конус с разными радиусами даёт силуэт."""
    bpy.ops.mesh.primitive_cone_add(radius1=r_bottom, radius2=r_top, depth=length,
                                    location=location, rotation=rot, vertices=verts)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    shade_smooth(obj)
    apply_all(obj)
    return obj


def box(name, size, location, material, rot=(0, 0, 0), bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    if material:
        obj.data.materials.append(material)
    if bevel:
        b = obj.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = 2
        b.limit_method = 'ANGLE'
    apply_all(obj)
    return obj


def cone(name, r1, r2, depth, location, material, rot=(0, 0, 0), verts=20):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth,
                                    location=location, rotation=rot, vertices=verts)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    shade_smooth(obj)
    apply_all(obj)
    return obj


def cyl(name, r, depth, location, material, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=location,
                                        rotation=rot, vertices=verts)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    shade_smooth(obj)
    apply_all(obj)
    return obj


# ---------------------------------------------------------------- скелет
def build_armature():
    arm_data = bpy.data.armatures.new('DetectiveRig')
    rig = bpy.data.objects.new('DetectiveRig', arm_data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')

    eb = arm_data.edit_bones

    def bone(name, head, tail, parent=None, connected=False):
        b = eb.new(name)
        b.head = head
        b.tail = tail
        if parent:
            b.parent = eb[parent]
            b.use_connect = connected
        return b

    # корень
    bone('root', (0, 0, 0), (0, 0, 0.1))
    # таз
    bone('hips', (0, 0, 0.98), (0, 0, 1.08), 'root')
    # позвоночник
    bone('spine', (0, 0, 1.06), (0, 0, 1.20), 'hips')
    bone('chest', (0, 0, 1.18), (0, 0, 1.44), 'spine')
    bone('neck', (0, 0, 1.42), (0, 0, 1.56), 'chest')
    bone('head', (0, 0, 1.54), (0, 0, 1.80), 'neck')

    # плечи -> руки (рука висит до 0.86)
    bone('shoulder.L', (0.045, 0, 1.43), (0.165, 0, 1.42), 'chest')
    bone('upperarm.L', (0.165, 0, 1.42), (0.168, 0, 1.20), 'shoulder.L')
    bone('forearm.L', (0.168, 0, 1.20), (0.170, 0, 0.98), 'upperarm.L', connected=True)
    bone('hand.L', (0.170, 0, 0.98), (0.170, 0, 0.90), 'forearm.L', connected=True)
    bone('shoulder.R', (-0.045, 0, 1.43), (-0.165, 0, 1.42), 'chest')
    bone('upperarm.R', (-0.165, 0, 1.42), (-0.168, 0, 1.20), 'shoulder.R')
    bone('forearm.R', (-0.168, 0, 1.20), (-0.170, 0, 0.98), 'upperarm.R', connected=True)
    bone('hand.R', (-0.170, 0, 0.98), (-0.170, 0, 0.90), 'forearm.R', connected=True)

    # ноги: подошва 0.0, бедро до 0.92
    bone('thigh.L', (0.078, 0, 0.92), (0.078, 0, 0.50), 'hips')
    bone('shin.L', (0.078, 0, 0.50), (0.078, 0, 0.12), 'thigh.L', connected=True)
    bone('foot.L', (0.078, 0, 0.12), (0.078, -0.17, 0.04), 'shin.L', connected=True)
    bone('thigh.R', (-0.078, 0, 0.92), (-0.078, 0, 0.50), 'hips')
    bone('shin.R', (-0.078, 0, 0.50), (-0.078, 0, 0.12), 'thigh.R', connected=True)
    bone('foot.R', (-0.078, 0, 0.12), (-0.078, -0.17, 0.04), 'shin.R', connected=True)

    # детали: полы пальто, воротник, поля шляпы
    bone('coat.L', (0.055, 0, 1.16), (0.055, 0, 0.80), 'hips')
    bone('coat.R', (-0.055, 0, 1.16), (-0.055, 0, 0.80), 'hips')
    bone('brim', (0, 0, 1.78), (0, 0, 1.82), 'head')
    bone('collar', (0, 0, 1.44), (0, 0, 1.50), 'chest')

    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    return rig


# ---------------------------------------------------------------- меши
def build_body(rig):
    """Строим две группы: цельное ТЕЛО (ремешится вorganичный силуэт)
    и РЕКВИЗИТ (шляпа, галстук, лупа — остаётся жёстко привязан к костям).

    Пропорции: рост 1.78 при голове ~0.235 -> ~7.5 голов, как у стилизованных
    героев, а не 5-головый chibi из шаров.
    """
    body_parts = []
    prop_parts = []
    M = {
        'coat': mat('Coat', C_COAT, rough=0.62),
        'coat_dark': mat('CoatDark', C_COAT_DARK, rough=0.7),
        'shirt': mat('Shirt', C_SHIRT, rough=0.75),
        'tie': mat('Tie', C_TIE, rough=0.6),
        'skin': mat('Skin', C_SKIN, rough=0.62),
        'hat': mat('Hat', C_HAT, rough=0.58),
        'boot': mat('Boot', C_BOOT, rough=0.45),
        'glove': mat('Glove', C_GLOVE, rough=0.6),
        'hair': mat('Hair', C_HAIR, rough=0.75),
        'metal': mat('Metal', C_METAL, rough=0.28, metal=1.0),
        'lamp': mat('LampGlass', (0.9, 0.75, 0.45, 1.0), rough=0.15,
                    emit=(1.0, 0.72, 0.35, 1.0), emit_strength=3.0),
        'eye': mat('Eye', (0.85, 0.88, 0.95, 1.0), rough=0.1,
                   emit=(0.75, 0.85, 1.0, 1.0), emit_strength=0.6),
    }

    def b(obj, mat_name):
        obj.data.materials.clear()
        obj.data.materials.append(M[mat_name])
        body_parts.append(obj)
        return obj

    def p(obj, bone_name, mat_name):
        obj.data.materials.clear()
        obj.data.materials.append(M[mat_name])
        obj['bone_hint'] = bone_name
        prop_parts.append(obj)
        return obj

    Y = 'Y_UP'
    # ---------------- ТЕЛО ----------------
    # таз -> талия -> грудь: три конуса разной ширины дают перепад силуэта
    b(taper('Pelvis', 0.135, 0.118, 0.16, (0, 0, 0.97), None, verts=20), 'coat_dark')
    b(taper('Waist', 0.118, 0.132, 0.14, (0, 0, 1.11), None, verts=20), 'coat')
    b(taper('Chest', 0.132, 0.150, 0.24, (0, 0, 1.33), None, verts=20), 'coat')
    # плечевой пояс — именно он даёт плечи, без него руки висят отдельно
    b(taper('ShoulderYoke', 0.075, 0.070, 0.34, (0, 0, 1.435), None,
            rot=(0, math.radians(90), 0), verts=16), 'coat')
    b(capsule('Neck', 0.049, 0.05, None, (0, 0, 1.52), (1.0, 0.92, 1.0)), 'skin')
    # голова: чуть вытянута вперёд, челюсть отдельным объёмом
    b(capsule('Head', 0.093, 0.07, None, (0, -0.004, 1.645), (0.9, 0.98, 1.08)), 'skin')
    b(capsule('Jaw', 0.070, 0.03, None, (0, -0.022, 1.598), (0.86, 0.92, 0.75)), 'skin')
    b(capsule('CheekL', 0.045, 0.02, None, (0.042, -0.05, 1.612), (0.9, 0.9, 0.9)), 'skin')
    b(capsule('CheekR', 0.045, 0.02, None, (-0.042, -0.05, 1.612), (0.9, 0.9, 0.9)), 'skin')

    # руки: сужаются от плеча к запястью
    for side, sgn in (('L', 1), ('R', -1)):
        b(taper(f'Shoulder_{side}', 0.070, 0.058, 0.10, (sgn * 0.155, 0, 1.425), None,
                rot=(0, math.radians(90 * sgn), 0), verts=14), 'coat')
        b(taper(f'UpperArm_{side}', 0.058, 0.046, 0.24, (sgn * 0.175, 0, 1.285), None, verts=14), 'coat')
        b(taper(f'Forearm_{side}', 0.046, 0.036, 0.22, (sgn * 0.175, 0, 1.045), None, verts=14), 'coat')
        b(capsule(f'Hand_{side}', 0.042, 0.02, None, (sgn * 0.175, -0.008, 0.915), (0.8, 0.66, 1.15)),
          'glove')
        b(capsule(f'Thumb_{side}', 0.013, 0.014, None, (sgn * 0.140, -0.026, 0.898)), 'glove')

    # ноги: длинные, сужаются к щиколотке
    for side, sgn in (('L', 1), ('R', -1)):
        b(taper(f'Thigh_{side}', 0.082, 0.060, 0.40, (sgn * 0.078, 0, 0.755), None, verts=16), 'coat_dark')
        b(taper(f'Shin_{side}', 0.060, 0.040, 0.38, (sgn * 0.078, 0, 0.360), None, verts=16), 'boot')
        b(capsule(f'Calf_{side}', 0.052, 0.02, None, (sgn * 0.078, -0.022, 0.330), (1.0, 0.9, 0.8)),
          'boot')

    # полы пальто — расширяются книзу, читаются как плащ
    for side, sgn in (('L', 1), ('R', -1)):
        b(taper(f'CoatTail_{side}', 0.115, 0.150, 0.42, (sgn * 0.055, 0.004, 0.945), None,
                verts=4, ), 'coat_dark') if False else None
    b(taper('CoatSkirtF', 0.150, 0.125, 0.44, (0, -0.055, 0.945), None, verts=4), 'coat_dark')
    b(taper('CoatSkirtB', 0.140, 0.115, 0.44, (0, 0.055, 0.945), None, verts=4), 'coat_dark')

    # ---------------- РЕКВИЗИТ ----------------
    # фетровая шляпа: тулья + наклонные поля + лента
    p(cyl('HatBrim', 0.150, 0.013, (0, -0.004, 1.742), None, rot=(math.radians(7), 0, 0), verts=30),
      'brim', 'hat')
    p(taper('HatCrown', 0.098, 0.092, 0.10, (0, 0.002, 1.795), None, verts=24), 'brim', 'hat')
    p(taper('HatTop', 0.092, 0.040, 0.045, (0, 0.002, 1.862), None, verts=24), 'brim', 'hat')
    p(cyl('HatBand', 0.100, 0.022, (0, 0.002, 1.752), None, verts=24), 'brim', 'coat_dark')
    # волосы и черты лица
    p(capsule('HairCap', 0.096, 0.03, None, (0, 0.012, 1.690), (0.9, 0.96, 1.0)), 'head', 'hair')
    p(box('SideburnL', (0.011, 0.028, 0.052), (0.076, -0.012, 1.648), None, bevel=0.004), 'head', 'hair')
    p(box('SideburnR', (0.011, 0.028, 0.052), (-0.076, -0.012, 1.648), None, bevel=0.004), 'head', 'hair')
    p(capsule('EyeL', 0.013, 0.004, None, (0.036, -0.070, 1.664), (1.0, 0.45, 0.75)), 'head', 'eye')
    p(capsule('EyeR', 0.013, 0.004, None, (-0.036, -0.070, 1.664), (1.0, 0.45, 0.75)), 'head', 'eye')
    p(box('BrowL', (0.038, 0.010, 0.007), (0.037, -0.074, 1.690), None, rot=(0, 0.14, 0), bevel=0.003),
      'head', 'hair')
    p(box('BrowR', (0.038, 0.010, 0.007), (-0.037, -0.074, 1.690), None, rot=(0, -0.14, 0), bevel=0.003),
      'head', 'hair')
    p(capsule('Nose', 0.015, 0.010, None, (0, -0.083, 1.632), (0.75, 0.85, 1.05)), 'head', 'skin')
    # рубашка, галстук, воротник, лацканы
    p(box('ShirtV', (0.070, 0.018, 0.20), (0, -0.098, 1.36), None, bevel=0.006), 'chest', 'shirt')
    p(box('Tie', (0.042, 0.012, 0.18), (0, -0.112, 1.335), None, bevel=0.004), 'chest', 'tie')
    p(box('CollarL', (0.085, 0.055, 0.020), (0.045, -0.085, 1.472), None, rot=(0.25, 0, 0.30), bevel=0.005),
      'collar', 'coat_dark')
    p(box('CollarR', (0.085, 0.055, 0.020), (-0.045, -0.085, 1.472), None, rot=(0.25, 0, -0.30), bevel=0.005),
      'collar', 'coat_dark')
    p(box('LapelL', (0.052, 0.014, 0.20), (0.078, -0.086, 1.395), None, rot=(0, 0.22, 0.12), bevel=0.005),
      'chest', 'coat_dark')
    p(box('LapelR', (0.052, 0.014, 0.20), (-0.078, -0.086, 1.395), None, rot=(0, -0.22, -0.12), bevel=0.005),
      'chest', 'coat_dark')
    p(box('Belt', (0.30, 0.24, 0.035), (0, 0, 1.045), None, bevel=0.006), 'hips', 'boot')
    p(box('Buckle', (0.055, 0.020, 0.045), (0, -0.125, 1.045), None, bevel=0.006), 'hips', 'metal')
    # манжеты и ботинки
    for side, sgn in (('L', 1), ('R', -1)):
        p(cyl(f'Cuff_{side}', 0.048, 0.028, (sgn * 0.175, 0, 0.960), None, verts=14), f'forearm.{side}', 'shirt')
        p(box(f'Boot_{side}', (0.078, 0.215, 0.075), (sgn * 0.078, -0.052, 0.062), None, bevel=0.016),
          f'foot.{side}', 'boot')
        p(box(f'Sole_{side}', (0.086, 0.230, 0.024), (sgn * 0.078, -0.056, 0.024), None, bevel=0.006),
          f'foot.{side}', 'coat_dark')
    # лупа в правой руке + булавка
    p(cyl('MagnifierRing', 0.046, 0.006, (0.235, -0.03, 0.905), None, rot=(math.pi / 2, 0, 0), verts=20),
      'hand.L', 'metal')
    p(cyl('MagnifierGlass', 0.041, 0.004, (0.235, -0.03, 0.905), None, rot=(math.pi / 2, 0, 0), verts=20),
      'hand.L', 'lamp')
    p(cyl('MagnifierHandle', 0.009, 0.075, (0.235, -0.068, 0.868), None, rot=(0.55, 0, 0), verts=10),
      'hand.L', 'metal')
    p(capsule('LapelPin', 0.008, 0.003, None, (0.070, -0.095, 1.425), (1.0, 0.4, 1.0)), 'chest', 'metal')

    return body_parts, prop_parts, M



# ---------------------------------------------------------------- скиннинг
def bone_segments(rig):
    """Кость -> (head, tail) в мировых координатах (арматура в нуле)."""
    out = []
    for b in rig.data.bones:
        out.append((b.name, Vector(b.head_local), Vector(b.tail_local)))
    return out


def dist_point_segment(p, a, b):
    ab = b - a
    denom = ab.dot(ab)
    if denom < 1e-9:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / denom))
    return (p - (a + ab * t)).length


def skin_character(body, rig, k=4, power=3.0, falloff=0.28):
    """Веса вершин по K ближайшим костям. Детерминированно, без heat-weighting:
    генератор не может упасть, а для стилизованной фигуры этого достаточно."""
    segs = bone_segments(rig)
    groups = {}
    for name, _h, _t in segs:
        groups[name] = body.vertex_groups.new(name=name)

    for i, v in enumerate(body.data.vertices):
        p = rig.matrix_world @ v.co
        dists = []
        for name, h, t in segs:
            dists.append((dist_point_segment(p, h, t), name))
        dists.sort(key=lambda x: x[0])
        picked = dists[:k]
        # обнуляем слишком далёкие кости, чтобы не было «размазанных» конечностей
        weights = []
        for d, name in picked:
            w = 1.0 / ((d + 1e-4) ** power)
            if d > falloff + picked[0][0]:
                w = 0.0
            weights.append((name, w))
        total = sum(w for _n, w in weights)
        if total <= 0:
            weights = [(picked[0][1], 1.0)]
            total = 1.0
        for name, w in weights:
            if w > 0:
                groups[name].add([i], w / total, 'REPLACE')

    mod = body.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    mod.use_vertex_groups = True
    body.parent = rig
    body.matrix_parent_inverse = rig.matrix_world.inverted()
    return body


def fuse_body(parts, name='DetectiveBody', voxel=0.022):
    """Джойн + воксельный ремеш: детали спекаются в одну гладкую поверхность.
    Без этого тело читается как набор шаров, а не как фигура."""
    obj = join_parts(parts, name)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.voxel_remesh()
    obj.data.remesh_voxel_size = voxel
    obj.data.remesh_voxel_adaptivity = 0.0
    obj.data.use_remesh_fix_poles = True
    bpy.ops.object.voxel_remesh()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.4, repeat=3)
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode='OBJECT')
    smooth_mod = obj.modifiers.new('Smooth', 'SMOOTH')
    smooth_mod.factor = 0.5
    smooth_mod.iterations = 2
    shade_smooth(obj, 0.9)
    return obj


def bind_rigid(obj, rig, bone_name):
    """Реквизит жёстко садится на кость: 100% веса."""
    if obj.type != 'MESH':
        return
    vg = obj.vertex_groups.new(name=bone_name)
    for i in range(len(obj.data.vertices)):
        vg.add([i], 1.0, 'REPLACE')
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()


def join_parts(parts, name='DetectiveBody'):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    return obj


# ---------------------------------------------------------------- анимации
def clear_anim(obj):
    obj.animation_data_clear()


def set_keys(rig, frames_keys, interp='BEZIER'):
    """frames_keys: {bone_name: [(frame, (rx,ry,rz), loc_offset|None), ...]}"""
    for bone_name, keys in frames_keys.items():
        pb = rig.pose.bones[bone_name]
        for f, rot, loc in keys:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = rot
            if loc is not None:
                pb.location = loc
            pb.keyframe_insert('rotation_euler', frame=f)
            if loc is not None:
                pb.keyframe_insert('location', frame=f)


def smooth_curves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'


def key(rig, bone, f, rx=0, ry=0, rz=0, loc=None):
    pb = rig.pose.bones[bone]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (rx, ry, rz)
    pb.keyframe_insert('rotation_euler', frame=f)
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert('location', frame=f)


def anim_idle(rig, n=96):
    clear_anim(rig)
    for f in (1, 24, 48, 72, 96):
        t = (f - 1) / n * 2 * math.pi
        sway = math.sin(t) * 0.05
        breath = math.sin(t * 2) * 0.022
        key(rig, 'root', f, 0, sway * 0.35, 0, loc=(0, 0, breath * 0.4))
        key(rig, 'spine', f, breath * 0.6, sway * 0.5, 0)
        key(rig, 'chest', f, breath * 0.4, -sway * 0.3, 0)
        key(rig, 'neck', f, breath * 0.3, sway * 0.4, 0)
        key(rig, 'head', f, -breath * 0.4 + 0.02, math.sin(t * 0.7) * 0.09, math.sin(t * 0.5) * 0.03)
        key(rig, 'shoulder.L', f, 0, 0, -0.06 - breath)
        key(rig, 'shoulder.R', f, 0, 0, 0.06 - breath)
        key(rig, 'upperarm.L', f, -0.12 - breath * 0.8, 0, 0.05)
        key(rig, 'upperarm.R', f, -0.12 - breath * 0.8, 0, -0.05)
        key(rig, 'forearm.L', f, -0.22, 0, 0)
        key(rig, 'forearm.R', f, -0.22, 0, 0)
        key(rig, 'thigh.L', f, 0, 0, 0)
        key(rig, 'thigh.R', f, 0, 0, 0)
        key(rig, 'shin.L', f, 0, 0, 0)
        key(rig, 'shin.R', f, 0, 0, 0)
        key(rig, 'coat.L', f, math.sin(t + 0.6) * 0.05, 0, 0)
        key(rig, 'coat.R', f, math.sin(t + 1.1) * 0.05, 0, 0)
    smooth_curves(rig)


def anim_walk(rig, n=32):
    clear_anim(rig)
    step = n // 2
    for half in (0, 1):
        for i, f in enumerate(range(1 + half * step, n + 1, step)):
            ph = (i * math.pi) % (2 * math.pi)
            s = math.sin(ph)
            c = math.cos(ph)
            # противофаза ног
            key(rig, 'thigh.L', f, s * 0.52, 0, 0.02)
            key(rig, 'thigh.R', f, -s * 0.52, 0, -0.02)
            key(rig, 'shin.L', f, max(0, -c) * 0.85 + 0.05, 0, 0)
            key(rig, 'shin.R', f, max(0, c) * 0.85 + 0.05, 0, 0)
            key(rig, 'foot.L', f, -s * 0.22, 0, 0)
            key(rig, 'foot.R', f, s * 0.22, 0, 0)
            # таз: вверх-вниз + разворот плеч против таза
            key(rig, 'root', f, 0, 0, c * 0.06, loc=(0, 0, abs(s) * 0.022 - 0.011))
            key(rig, 'hips', f, 0, c * 0.09, 0)
            key(rig, 'spine', f, 0.03, -c * 0.05, 0)
            key(rig, 'chest', f, 0, -c * 0.10, 0)
            key(rig, 'neck', f, 0.02, c * 0.05, 0)
            key(rig, 'head', f, 0, c * 0.06, 0)
            # руки в противофазе ногам
            key(rig, 'shoulder.L', f, 0, 0, -0.05)
            key(rig, 'shoulder.R', f, 0, 0, 0.05)
            key(rig, 'upperarm.L', f, -s * 0.42, 0, 0.06)
            key(rig, 'upperarm.R', f, s * 0.42, 0, -0.06)
            key(rig, 'forearm.L', f, -0.20 - max(0, s) * 0.35, 0, 0)
            key(rig, 'forearm.R', f, -0.20 - max(0, -s) * 0.35, 0, 0)
            # полы пальто отстают
            key(rig, 'coat.L', f, -s * 0.16, 0, 0)
            key(rig, 'coat.R', f, s * 0.16, 0, 0)
    smooth_curves(rig)


def anim_run(rig, n=24):
    clear_anim(rig)
    step = n // 2
    for half in (0, 1):
        for i, f in enumerate(range(1 + half * step, n + 1, step)):
            ph = (i * math.pi) % (2 * math.pi)
            s = math.sin(ph)
            c = math.cos(ph)
            key(rig, 'thigh.L', f, s * 0.95, 0, 0.03)
            key(rig, 'thigh.R', f, -s * 0.95, 0, -0.03)
            key(rig, 'shin.L', f, max(0, -c) * 1.7, 0, 0)
            key(rig, 'shin.R', f, max(0, c) * 1.7, 0, 0)
            key(rig, 'foot.L', f, -s * 0.4, 0, 0)
            key(rig, 'foot.R', f, s * 0.4, 0, 0)
            key(rig, 'root', f, 0.10, 0, c * 0.10, loc=(0, 0, abs(s) * 0.05 - 0.02))
            key(rig, 'hips', f, 0, c * 0.16, 0)
            key(rig, 'spine', f, 0.12, -c * 0.09, 0)
            key(rig, 'chest', f, 0.05, -c * 0.18, 0)
            key(rig, 'neck', f, 0.06, c * 0.08, 0)
            key(rig, 'head', f, -0.05, c * 0.09, 0)
            key(rig, 'shoulder.L', f, 0, 0, -0.07)
            key(rig, 'shoulder.R', f, 0, 0, 0.07)
            key(rig, 'upperarm.L', f, -s * 0.95 - 0.35, 0, 0.10)
            key(rig, 'upperarm.R', f, s * 0.95 - 0.35, 0, -0.10)
            key(rig, 'forearm.L', f, -0.85 - max(0, s) * 0.5, 0, 0)
            key(rig, 'forearm.R', f, -0.85 - max(0, -s) * 0.5, 0, 0)
            key(rig, 'coat.L', f, -s * 0.38, 0, 0)
            key(rig, 'coat.R', f, s * 0.38, 0, 0)
    smooth_curves(rig)


def anim_turn(rig, n=40):
    clear_anim(rig)
    for i, f in enumerate(range(1, n + 1, 5)):
        t = i / (n / 5)
        # разворот на месте с оглядкой через плечо
        key(rig, 'root', f, 0, math.sin(t * math.pi) * 0.55, 0)
        key(rig, 'hips', f, 0, math.sin(t * math.pi) * 0.22, 0)
        key(rig, 'spine', f, 0, -math.sin(t * math.pi) * 0.14, 0)
        key(rig, 'chest', f, 0, -math.sin(t * math.pi) * 0.18, 0)
        key(rig, 'neck', f, 0, math.sin(t * math.pi) * 0.42, 0)
        key(rig, 'head', f, 0, math.sin(t * math.pi) * 0.55, 0)
        key(rig, 'upperarm.L', f, -0.1, 0, 0.08)
        key(rig, 'upperarm.R', f, -0.1, 0, -0.08)
        key(rig, 'forearm.L', f, -0.3, 0, 0)
        key(rig, 'forearm.R', f, -0.3, 0, 0)
    smooth_curves(rig)


ANIMS = {'Idle': anim_idle, 'Walk': anim_walk, 'Run': anim_run, 'Turn': anim_turn}


# ---------------------------------------------------------------- экспорт
def export_gltf(path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH', 'ARMATURE'}:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_animations=True,
        export_animation_mode='SCENE',
        export_bake_animation=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
        export_skins=True,
    )


def main():
    reset_scene()
    os.makedirs(OUT, exist_ok=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = CLIPS['Idle']

    rig = build_armature()
    body_parts, prop_parts, _mats = build_body(rig)
    bpy.context.view_layer.update()

    body = fuse_body(body_parts)
    print('[BODY] вершин после ремеша=%d' % len(body.data.vertices))
    skin_character(body, rig)

    for pr in prop_parts:
        bone_hint = pr.get('bone_hint', 'chest')
        if bone_hint not in rig.data.bones:
            bone_hint = 'chest'
        bind_rigid(pr, rig, bone_hint)
    print('[PROPS] привязано=%d' % len(prop_parts))

    # готовим NLA-дорожки: каждая анимация — отдельный action
    tmp_actions = {}
    for name, fn in ANIMS.items():
        fn(rig, CLIPS[name])
        action = rig.animation_data.action
        action.name = f'{name}_action'
        tmp_actions[name] = action
        # «схлопываем» в NLA, чтобы glTF-экспорт увидел все клипы
        track = rig.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 1, action)
        strip.action_frame_start = 1
        strip.action_frame_end = CLIPS[name]
        strip.frame_start = 1
        strip.frame_end = CLIPS[name]
        rig.animation_data.action = None

    # возвращаем в T-pose для экспорта скелета
    scene.frame_set(1)

    out_glb = os.path.join(OUT, 'detective.glb')
    export_gltf(out_glb)
    print(f'[OK] glTF: {out_glb} ({os.path.getsize(out_glb)} bytes)')

    # .blend тоже — чтобы можно было править дальше
    out_blend = os.path.join(OUT, 'detective.blend')
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print(f'[OK] blend: {out_blend}')

    print('[STATS] meshes=%d bones=%d actions=%d' % (
        len([o for o in bpy.context.scene.objects if o.type == 'MESH']),
        len(rig.data.bones),
        len(tmp_actions),
    ))
    for name, a in tmp_actions.items():
        print(f'   clip {name}: {a.frame_range[1] - a.frame_range[0] + 1} frames')


if __name__ == '__main__':
    main()
