#!/usr/bin/env python3
"""Проверка бесшовности клипов в glTF (без внешних зависимостей).

Идея: у бесшовного цикла шаг «последний кадр → первый кадр» должен быть
не больше обычного шага между соседними кадрами. Если цикл «прыгает» на
стыке, этот шаг выделяется в разы.

usage: python3 tools/check_loops.py public/models/detective.glb [...]
"""
import json
import math
import struct
import sys

COMP = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2),
        5125: ('I', 4), 5126: ('f', 4)}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load(path):
    data = open(path, 'rb').read()
    if data[:4] != b'glTF':
        raise SystemExit('%s: не GLB' % path)
    js = None
    binary = b''
    off = 12  # заголовок GLB
    while off + 8 <= len(data):
        clen, ctype = struct.unpack_from('<II', data, off)
        chunk = data[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942:
            binary = chunk
        off += 8 + clen + ((4 - clen % 4) % 4)
    if js is None:
        raise SystemExit('%s: нет JSON-чанка' % path)
    return js, binary


def read_accessor(js, data, idx):
    acc = js['accessors'][idx]
    n = NCOMP[acc['type']]
    fmt, size = COMP[acc['componentType']]
    count = acc['count']
    out = []
    bv = js['bufferViews'][acc['bufferView']]
    base = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = bv.get('byteStride') or size * n
    for i in range(count):
        o = base + i * stride
        out.append(struct.unpack_from('<' + fmt * n, data, o))
    return out


def quat_align(a, b):
    """Кватернионы q и -q — одна и та же поза; выравниваем знак, иначе
    кажется, что поза скачет на 180°."""
    if sum(x * y for x, y in zip(a, b)) < 0:
        return tuple(-x for x in a)
    return a


def quat_angle(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return 2 * math.acos(min(1.0, d))


def check(path):
    """Метрика: «какой была бы следующая кадровая поза, если бы цикл продолжался».
    У бесшовного цикла она совпадает с последним шагом — стык незаметен."""
    js, data = load(path)
    print('== %s: %d клип(ов), %d узлов' % (path, len(js.get('animations', [])),
                                            len(js.get('nodes', []))))
    total = 0
    for anim in js.get('animations', []):
        worst = (0.0, 0.0, '')
        jumps = []
        for ch in anim.get('channels', []):
            node = js['nodes'][ch['target']['node']].get('name', '?')
            kind = ch['target']['path']
            if kind == 'weights':
                continue
            s = anim['samplers'][ch['sampler']]
            times = read_accessor(js, data, s['input'])
            vals = read_accessor(js, data, s['output'])
            m = min(len(times), len(vals))
            if m < 4:
                continue
            if kind == 'rotation':
                vals = [tuple(vals[0])] + [quat_align(vals[i], vals[i - 1])
                                           for i in range(1, m)]
                d = [quat_angle(vals[i], vals[i + 1]) for i in range(m - 1)]
                nxt = [2 * vals[-1][i] - vals[-2][i] for i in range(4)]
                norm = math.sqrt(sum(x * x for x in nxt)) or 1.0
                seam = quat_angle(vals[-1], [x / norm for x in nxt])
            else:
                d = [math.dist(vals[i], vals[i + 1]) for i in range(m - 1)]
                nxt = [2 * vals[-1][i] - vals[-2][i] for i in range(len(vals[-1]))]
                seam = math.dist(vals[-1], nxt)
            avg = sum(d) / len(d)
            last = d[-1]
            if avg > 1e-4 and seam > max(3.0 * last, 0.02):
                jumps.append('%s.%s seam=%.3f шаг=%.3f' % (node, kind, seam, last))
            if seam > worst[0]:
                worst = (seam, last, '%s.%s' % (node, kind))
        flag = 'OK  ' if not jumps else 'JUMP'
        print('   %s %-10s кадров=%-4d стык=%.3f (последний шаг %.3f) худший=%s'
              % (flag, anim.get('name'), m, worst[0], worst[1], worst[2]))
        for j in jumps[:6]:
            print('        -> ' + j)
        total += len(jumps)
    return total


if __name__ == '__main__':
    paths = sys.argv[1:] or ['public/models/detective.glb']
    total = sum(check(p) for p in paths)
    print('ИТОГО скачков на стыках цикла: %d' % total)
    sys.exit(0)
