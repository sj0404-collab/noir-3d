"""noirlib — общая библиотека генераторов 3D-моделей «Нуар-Дет».

Используется генераторами:
  tools/make_detective.py  — персонаж (аниме-стиль, риг, клипы)
  tools/make_vehicles.py   — транспорт (колёса на костях, клипы езды)
  tools/make_env.py        — окружение (фасады, уличный реквизит, флаги)

Всё детерминировано: генератор не падает и не зависит от внешних ассетов.
Запуск (из корня репозитория):
  blender -b -P tools/make_detective.py -- --out public/models
"""
import bpy
import math
import os
import sys
from mathutils import Vector

FPS = 30
TAU = math.pi * 2


# ------------------------------------------------------------------ палитра
def palette():
    """Нуар + аниме-акценты. Аниме-стиль: чистые тона, холодные тени,
    тёплые источники света, минимум PBR-шероховатости."""
    return {
        'coat':       ((0.055, 0.062, 0.082, 1.0), 0.62),
        'coat_dark':  ((0.026, 0.029, 0.040, 1.0), 0.70),
        'coat_inner': ((0.115, 0.075, 0.070, 1.0), 0.68),
        'shirt':      ((0.62, 0.60, 0.55, 1.0), 0.72),
        'tie':        ((0.32, 0.055, 0.075, 1.0), 0.58),
        'skin':       ((0.86, 0.72, 0.63, 1.0), 0.55),
        'skin_shade': ((0.80, 0.63, 0.55, 1.0), 0.55),
        'hair':       ((0.105, 0.095, 0.130, 1.0), 0.52),
        'hair_tip':   ((0.28, 0.32, 0.52, 1.0), 0.45),
        'hat':        ((0.040, 0.043, 0.056, 1.0), 0.55),
        'boot':       ((0.028, 0.028, 0.036, 1.0), 0.42),
        'glove':      ((0.095, 0.085, 0.095, 1.0), 0.58),
        'metal':      ((0.66, 0.53, 0.26, 1.0), 0.24),
        'metal_dark': ((0.20, 0.21, 0.24, 1.0), 0.30),
        'glass':      ((0.10, 0.14, 0.20, 1.0), 0.10),
        'eye_white':  ((0.94, 0.95, 0.98, 1.0), 0.20),
        'eye_iris':   ((0.20, 0.62, 0.78, 1.0), 0.20),
        'lamp_warm':  ((1.00, 0.74, 0.38, 1.0), 0.20),
        'neon_cyan':  ((0.22, 0.88, 1.00, 1.0), 0.20),
        'neon_pink':  ((1.00, 0.36, 0.58, 1.0), 0.20),
        'brick':      ((0.175, 0.150, 0.185, 1.0), 0.85),
        'concrete':   ((0.155, 0.160, 0.175, 1.0), 0.88),
        'asphalt':    ((0.075, 0.080, 0.095, 1.0), 0.90),
        'wood':       ((0.190, 0.120, 0.085, 1.0), 0.75),
        'rust':       ((0.235, 0.130, 0.080, 1.0), 0.85),
        'glass_win':  ((0.085, 0.105, 0.150, 1.0), 0.12),
        'glass_lit':  ((0.420, 0.320, 0.150, 1.0), 0.12),
        'car_body':   ((0.055, 0.070, 0.105, 1.0), 0.32),
        'car_body2':  ((0.320, 0.055, 0.075, 1.0), 0.32),
        'tram_body':  ((0.180, 0.190, 0.205, 1.0), 0.40),
        'tram_trim':  ((0.520, 0.180, 0.130, 1.0), 0.45),
        'rubber':     ((0.020, 0.020, 0.024, 1.0), 0.85),
        'chrome':     ((0.700, 0.720, 0.750, 1.0), 0.16),
        'fabric_red': ((0.420, 0.090, 0.110, 1.0), 0.80),
    }


# ------------------------------------------------------------------ сцена
def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions,
                  bpy.data.materials, bpy.data.cameras, bpy.data.lights,
                  bpy.data.images, bpy.data.curves):
        for item in list(block):
            try:
                block.remove(item)
            except Exception:
                pass


def make_materials(pal=None):
    """Создаёт все материалы палитры -> {имя: материал}."""
    pal = pal or palette()
    out = {}
    for name, (color, rough) in pal.items():
        out[name] = mat(name, color, rough=rough)
    # акценты со свечением
    out['lamp_warm'].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1.0, 0.72, 0.35, 1.0)
    out['lamp_warm'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0
    out['neon_cyan'].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (0.25, 0.9, 1.0, 1.0)
    out['neon_cyan'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0
    out['neon_pink'].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1.0, 0.35, 0.6, 1.0)
    out['neon_pink'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 2.6
    out['glass_lit'].node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1.0, 0.66, 0.30, 1.0)
    out['glass_lit'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.9
    return out


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


def set_mat(obj, material):
    if material is not None and obj.type == 'MESH':
        obj.data.materials.clear()
        obj.data.materials.append(material)
    return obj


# ------------------------------------------------------------------ утилиты
def apply_all(obj):
    """Впечатывает location/rotation/scale в данные меша: узел остаётся единичным.
    Иначе glTF-узлы несут масштабы и ломают скиннинг."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def shade_smooth(obj, angle=0.6):
    activate(obj)
    bpy.ops.object.shade_smooth()
    try:
        bpy.ops.object.shade_auto_smooth(angle=angle)
    except Exception:
        mod = obj.modifiers.new('SmoothByAngle', 'SMOOTH_BY_ANGLE')
        mod.angle = angle
    return obj


def shade_flat(obj):
    activate(obj)
    bpy.ops.object.shade_flat()
    return obj


# ------------------------------------------------------------------ примитивы
def _finish(obj, name, material, rot=(0, 0, 0), smooth=True, angle=0.6, scale=None):
    obj.name = name
    if scale:
        obj.scale = scale
    set_mat(obj, material)
    if smooth:
        shade_smooth(obj, angle)
    apply_all(obj)
    return obj


def sphere(name, r, loc, material=None, scale=(1, 1, 1), rot=(0, 0, 0), seg=20, rings=12,
           smooth=True, angle=0.6):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, rotation=rot,
                                         segments=seg, ring_count=rings)
    return _finish(bpy.context.active_object, name, material, smooth=smooth, angle=angle, scale=scale)


def capsule(name, r, length, loc, material=None, scale=(1, 1, 1), rot=(0, 0, 0),
            seg=20, rings=12, smooth=True):
    """Капсула вдоль локальной Z: и кость-«труба», и деталь."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, rotation=rot,
                                         segments=seg, ring_count=rings)
    return _finish(bpy.context.active_object, name, material, smooth=smooth,
                   scale=(scale[0], scale[1], scale[2] * (1 + length / max(r, 1e-4))))


def taper(name, r_bottom, r_top, length, loc, material=None, rot=(0, 0, 0), verts=18,
          scale=(1, 1, 1), smooth=True, angle=0.6):
    """Сужающаяся труба вдоль локальной Z. `scale` сплющивает сечение — так
    получаются плоские полы пальто, а не «юбка»."""
    bpy.ops.mesh.primitive_cone_add(radius1=r_bottom, radius2=r_top, depth=length,
                                    location=loc, rotation=rot, vertices=verts)
    return _finish(bpy.context.active_object, name, material, rot=rot, smooth=smooth,
                   angle=angle, scale=scale)


def box(name, size, loc, material=None, rot=(0, 0, 0), bevel=0.012, segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    set_mat(obj, material)
    if bevel:
        b = obj.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = segments
        b.limit_method = 'ANGLE'
    apply_all(obj)
    return obj


def cyl(name, r, depth, loc, material=None, rot=(0, 0, 0), verts=16, scale=(1, 1, 1),
        smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    return _finish(bpy.context.active_object, name, material, rot=rot, smooth=smooth,
                   scale=scale)


def cone(name, r1, r2, depth, loc, material=None, rot=(0, 0, 0), verts=20, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, location=loc,
                                    rotation=rot, vertices=verts)
    return _finish(bpy.context.active_object, name, material, rot=rot, scale=scale)


def torus(name, R, r, loc, material=None, rot=(0, 0, 0), major=20, minor=8):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc,
                                     rotation=rot, major_segments=major, minor_segments=minor)
    return _finish(bpy.context.active_object, name, material, rot=rot)


def plate(name, size, loc, material=None, rot=(0, 0, 0), bevel=0.006):
    return box(name, size, loc, material, rot, bevel)


def pipe(name, points, radius, material=None, verts=10):
    """Труба по ломаной: поручни, лестницы, рамы, пантограф."""
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = max(1, verts // 4)
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, p in enumerate(points):
        spline.points[i].co = (p[0], p[1], p[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    set_mat(obj, material)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    return bpy.context.active_object


def wedge(name, size, loc, material=None, rot=(0, 0, 0), bevel=0.008):
    """Клин: скулы, козырёк, скос крыши."""
    w, h, d = size
    verts = [(0, 0, 0), (w, 0, 0), (0, 0, d), (w, 0, d), (0, h, 0), (w, h, 0)]
    faces = [(0, 1, 3, 2), (4, 5, 3, 2), (0, 2, 4), (1, 3, 5), (0, 1, 5, 4)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    set_mat(obj, material)
    if bevel:
        b = obj.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = 2
        b.limit_method = 'ANGLE'
    apply_all(obj)
    shade_smooth(obj, 0.5)
    return obj


# ------------------------------------------------------------------ сборка
def grid_mesh(name, w, h, nx, ny, loc, material=None, rot=(0, 0, 0)):
    """Плоскость с сеткой (nx+1)x(ny+1) — ткань флага, вывески, стёкла."""
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            verts.append((-w / 2 + w * i / nx, 0.0, -h / 2 + h * j / ny))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b = a + 1
            c = a + (nx + 1)
            d = c + 1
            faces.append((a, b, d, c))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    set_mat(obj, material)
    apply_all(obj)
    return obj


def join_parts(parts, name='Part'):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    return obj


def fuse_body(parts, name='Body', voxel=0.012, smooth_iters=3):
    """Джойн + воксельный ремеш: детали спекаются в одну поверхность."""
    obj = join_parts(parts, name)
    activate(obj)
    bpy.ops.object.voxel_remesh()
    obj.data.remesh_voxel_size = voxel
    obj.data.remesh_voxel_adaptivity = 0.0
    obj.data.use_remesh_fix_poles = True
    bpy.ops.object.voxel_remesh()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.4, repeat=smooth_iters)
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode='OBJECT')
    sm = obj.modifiers.new('Smooth', 'SMOOTH')
    sm.factor = 0.5
    sm.iterations = 2
    shade_smooth(obj, 0.9)
    return obj


def duplicate(parts, name):
    """Копии деталей (для второй стороны/цвета) — глубокая копия меша."""
    out = []
    for p in parts:
        c = p.copy()
        c.data = p.data.copy()
        c.name = name + '_' + p.name
        bpy.context.collection.objects.link(c)
        out.append(c)
    return out


# ------------------------------------------------------------------ скелет
def build_armature(bones, name='Rig', collection=None):
    """bones: список (имя, head, tail, parent|None, connected|False)."""
    arm_data = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, arm_data)
    (collection or bpy.context.collection).objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    for b in bones:
        spec = b if isinstance(b, dict) else {'name': b[0], 'head': b[1], 'tail': b[2],
                                              'parent': b[3] if len(b) > 3 else None,
                                              'connected': b[4] if len(b) > 4 else False}
        bone = eb.new(spec['name'])
        bone.head = Vector(spec['head'])
        bone.tail = Vector(spec['tail'])
        if spec.get('parent'):
            bone.parent = eb[spec['parent']]
            bone.use_connect = bool(spec.get('connected'))
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    return rig


def bone_segments(rig):
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


def group_bones(hint, rig):
    """Какие кости участвуют в скиннинге группы деталей."""
    names = {b.name for b in rig.data.bones}
    if hint is None:
        return None
    if hint == 'torso':
        want = ['hips', 'spine', 'chest', 'neck', 'head', 'collar', 'coat.L', 'coat.R', 'root']
    elif hint.startswith('arm.'):
        s = hint[-1]
        want = ['shoulder.' + s, 'upperarm.' + s, 'forearm.' + s, 'hand.' + s, 'chest']
    elif hint.startswith('leg.'):
        s = hint[-1]
        want = ['thigh.' + s, 'shin.' + s, 'foot.' + s, 'hips']
    else:
        want = [hint]
    return [n for n in want if n in names]


def skin_character(body, rig, k=4, power=3.0, falloff=0.28, hint=None, groups=None):
    """Веса вершин по K ближайшим костям. Детерминированно, без heat-weighting."""
    segs = bone_segments(rig)
    wanted = group_bones(hint, rig)
    if wanted is not None:
        segs = [sg for sg in segs if sg[0] in wanted]
    vgs = {name: body.vertex_groups.new(name=name) for name, _h, _t in segs}

    for i, v in enumerate(body.data.vertices):
        p = rig.matrix_world @ v.co
        dists = sorted(((dist_point_segment(p, h, t), name) for name, h, t in segs))
        if not dists:
            continue
        picked = dists[:k]
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
                vgs[name].add([i], w / total, 'REPLACE')

    mod = body.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    mod.use_vertex_groups = True
    body.parent = rig
    body.matrix_parent_inverse = rig.matrix_world.inverted()
    return body


def bind_rigid(obj, rig, bone_name, weight=1.0):
    """Реквизит жёстко садится на кость."""
    if obj.type != 'MESH':
        return obj
    vg = obj.vertex_groups.get(bone_name) or obj.vertex_groups.new(name=bone_name)
    for i in range(len(obj.data.vertices)):
        vg.add([i], weight, 'REPLACE')
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    return obj


def skin_hierachy(objs, rig, bone, weight=1.0):
    """Привязать объект с детьми (машина, трамвай) к одной кости."""
    for o in objs:
        bind_rigid(o, rig, bone, weight)
    return objs


# ------------------------------------------------------------------ анимации
def clear_anim(obj):
    if obj.animation_data:
        obj.animation_data_clear()
    for t in list(obj.animation_data_nla_tracks()) if hasattr(obj, 'animation_data_nla_tracks') else []:
        obj.nla_tracks.remove(t)


def key(rig, bone, f, rx=0.0, ry=0.0, rz=0.0, loc=None, scale=None):
    pb = rig.pose.bones[bone]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (rx, ry, rz)
    pb.keyframe_insert('rotation_euler', frame=f)
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert('location', frame=f)
    if scale is not None:
        pb.scale = scale
        pb.keyframe_insert('scale', frame=f)


def finalize_curves(rig, cyclic=True, interp='BEZIER'):
    """AUTO-хендлы + циклический Fmodifier: цикл ровно бесшовный,
    хвост и голова кривой продолжают движение, а не замирают."""
    ad = rig.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            kp.handle_left_type = 'AUTO'
            kp.handle_right_type = 'AUTO'
        if cyclic and not any(m.type == 'CYCLES' for m in fc.modifiers):
            mod = fc.modifiers.new('CYCLES')
            mod.mode_before = 'REPEAT'
            mod.mode_after = 'REPEAT'


def bake_loop(rig, n_frames, pose_fn, stride=2, cyclic=True, interp='BEZIER'):
    """Ключи по N кадрам. pose_fn(u) -> {bone: (rx, ry, rz[, loc[, scale]])}, u=(f-1)/n.

    Ключ ставится на кадры 1..n, u никогда не доходит до 1.0 — последний кадр НЕ
    дублирует первый, поэтому в glTF нет «затычка» на стыке цикла. Бесшовность
    обеспечивает CYCLES-модификатор: кривая продолжается за пределы диапазона.
    """
    clear_anim(rig)
    frames = list(range(1, n_frames + 1, stride))
    if frames[-1] != n_frames:
        frames.append(n_frames)
    for f in frames:
        u = (f - 1) / float(n_frames)
        for bone, val in pose_fn(u).items():
            rx, ry, rz = val[0], val[1], val[2]
            loc = val[3] if len(val) > 3 else None
            scale = val[4] if len(val) > 4 else None
            key(rig, bone, f, rx, ry, rz, loc, scale)
    finalize_curves(rig, cyclic=cyclic, interp=interp)
    return rig.animation_data.action


def bake_once(rig, n_frames, pose_fn, keys=8, interp='BEZIER'):
    """Одноразовое движение (начало = конец, но не цикл)."""
    clear_anim(rig)
    for i in range(keys + 1):
        f = 1 + round(i * (n_frames - 1) / keys)
        u = i / keys
        for bone, val in pose_fn(u).items():
            rx, ry, rz = val[0], val[1], val[2]
            loc = val[3] if len(val) > 3 else None
            scale = val[4] if len(val) > 4 else None
            key(rig, bone, f, rx, ry, rz, loc, scale)
    finalize_curves(rig, cyclic=False, interp=interp)
    return rig.animation_data.action


def stage_clip(rig, action, name, frame_start=1):
    """Кладёт action в NLA-дорожку с уникальным именем — чтобы экспорт увидел
    клипы по отдельности (иначе SCENE-режим сливает всё в одну анимацию)."""
    action.name = name
    action.use_fake_user = True
    if rig.animation_data is None:
        return action
    rig.animation_data.action = None
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, frame_start, action)
    strip.action_frame_start = 1
    strip.action_frame_end = int(action.frame_range[1])
    strip.frame_start = frame_start
    strip.frame_end = frame_start + int(action.frame_range[1]) - 1
    return action


# ------------------------------------------------------------------ экспорт
def export_gltf(path, name_hint=None):
    """Каждый action -> отдельный glTF-клип (export_animation_mode='ACTIONS')."""
    bpy.ops.object.select_all(action='DESELECT')
    meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH', 'ARMATURE'}:
            obj.select_set(True)
            meshes.append(obj)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_animations=True,
        export_animation_mode='ACTIONS',
        export_nla_strips=False,
        export_bake_animation=True,
        export_anim_slide_to_zero=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
        export_skins=True,
        export_optimize_animation_size=False,
    )
    print(f'[OK] glTF: {path} ({os.path.getsize(path)} bytes)')
    return path


def save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f'[OK] blend: {path} ({os.path.getsize(path)} bytes)')
    return path


def setup_scene(frame_end=96):
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = frame_end
    return scene


def parse_args(default_out='public/models'):
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = default_out
    if '--out' in argv:
        out = argv[argv.index('--out') + 1]
    only = None
    if '--only' in argv:
        only = argv[argv.index('--only') + 1].split(',')
    return os.path.abspath(out), only


def log_stats(rig=None, clips=None):
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        o.data.calc_loop_triangles()
    tris = sum(len(o.data.loop_triangles) for o in meshes)
    verts = sum(len(o.data.vertices) for o in meshes)
    print('[STATS] meshes=%d вершин=%d треугольников=%d' % (len(meshes), verts, tris))
    if rig:
        print('[STATS] костей=%d' % len(rig.data.bones))
    for name, action in (clips or {}).items():
        a0, a1 = action.frame_range
        print('   клип %-8s кадров=%-4d  %.2fs' % (name, int(a1 - a0 + 1), (a1 - a0 + 1) / FPS))
