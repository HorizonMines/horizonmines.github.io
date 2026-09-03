#!/usr/bin/env python3
"""Generate the isometric block icons used on the server rows.

    python3 tools/make-block-icons.py

Textures
--------
Drop 16x16 PNGs into tools/textures/ and they are used as-is:

    grass_block_top.png
    grass_block_side.png
    bedrock.png

Anything missing falls back to a generated stand-in. If you supply the
game's own grass_block_top.png, note that it ships greyscale and is
tinted per-biome at runtime, so a grass tint is applied to it here --
see GRASS_TINT. Whether a given texture may be redistributed on a
public site depends on where it came from; that is a licensing call for
whoever owns the site, which is why nothing is bundled here.

Rendering
---------
Built the way the game builds an item render: the 16x16 face texture is
projected through a 2:1 isometric transform by inverse-mapping every
output pixel, and each face takes a brightness multiplier. Texture
pixels land as rhombi on the top face and sheared squares on the sides.

Output is a 64-unit grid, 4 units per texture pixel, and the CSS shows
it at 64px so the mapping is exactly 1:1. 48px would put the geometry
on 0.75px steps and the edges would wobble; 32px (1:2) is the only
other clean size.
"""

import os
import random

N, SZ = 16, 64
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
OUT = os.path.join(os.path.dirname(HERE), 'images')

# Face shading is per block. Grass is fine on the game's own values because
# its green and brown hues already separate the faces; an all-grey bedrock
# needs a wider spread or the cube stops reading as a cube.
GRASS_SHADE = (1.0, 0.80, 0.60)
BEDROCK_SHADE = (1.0, 0.70, 0.45)
GRASS_TINT = (0.48, 0.74, 0.35)      # biome tint for a greyscale grass top


def load_png(name):
    """Return a 16x16 RGB grid, or None if the file isn't there."""
    path = os.path.join(TEX, name)
    if not os.path.exists(path):
        return None
    from PIL import Image
    img = Image.open(path).convert('RGBA')
    if img.size != (N, N):
        img = img.resize((N, N), Image.NEAREST)
    px = img.load()
    return [[px[x, y][:3] for x in range(N)] for y in range(N)]


def is_greyscale(tex):
    return all(abs(max(p) - min(p)) <= 6 for row in tex for p in row)


def tint(tex, k):
    return [[tuple(min(255, int(c * m)) for c, m in zip(p, k)) for p in row]
            for row in tex]


def value_noise(seed, cells):
    """Smooth noise from a cells x cells lattice, sampled up to 16x16.

    Wraps, since block textures tile.
    """
    rnd = random.Random(seed)
    g = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            fx, fy = x / N * cells, y / N * cells
            x0, y0 = int(fx), int(fy)
            x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
            tx, ty = fx - x0, fy - y0
            sx, ty_ = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * sx
            b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * sx
            out[y][x] = a + (b - a) * ty_
    return out


def fractal(seed, octaves, contrast=1.0):
    """Sum several octaves of value noise.

    This is the piece that was missing. A single octave of per-pixel noise
    is television static, and averaging it flat is fog; natural-looking
    rock and soil need large shapes carrying medium ones carrying fine
    detail. Weights are per texture: bedrock leans on the fine octaves for
    its blotching, grass and dirt on the broad ones.
    """
    acc = [[0.0] * N for _ in range(N)]
    for i, (cells, w) in enumerate(octaves):
        f = value_noise(seed + i * 13, cells)
        for y in range(N):
            for x in range(N):
                acc[y][x] += f[y][x] * w
    lo = min(map(min, acc))
    hi = max(map(max, acc))
    rng = (hi - lo) or 1.0
    for y in range(N):
        for x in range(N):
            v = (acc[y][x] - lo) / rng
            v = (v - 0.5) * contrast + 0.5
            acc[y][x] = min(1.0, max(0.0, v))
    return acc


def ramp(field, tones):
    return [[tones[min(len(tones) - 1, int(v * len(tones)))] for v in row]
            for row in field]


def hexrgb(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


def fallback_bedrock():
    # Weighted toward the fine octaves and pushed hard on contrast: bedrock
    # reads as tight high-contrast blotching, not broad cloudy shading.
    tones = [hexrgb(c) for c in
             ('#3a3a3a', '#565656', '#727272', '#909090', '#adadad')]
    return ramp(fractal(17, ((2, 0.30), (4, 0.28), (8, 0.26), (16, 0.16)),
                        contrast=1.9), tones)


def fallback_grass_top():
    # Broad octaves dominate: grass is mostly even, with gentle patchiness.
    tones = [hexrgb(c) for c in
             ('#5d9a3f', '#6aa94a', '#77b755', '#84c560', '#91d16b')]
    return ramp(fractal(3, ((2, 0.45), (4, 0.30), (8, 0.18), (16, 0.07)),
                        contrast=1.15), tones)


def fallback_grass_side():
    dirt = [hexrgb(c) for c in
            ('#5c4028', '#6b4b30', '#795538', '#876040', '#956b48')]
    grass = [hexrgb(c) for c in
             ('#4a7d33', '#558c3a', '#609a42', '#6ba84a', '#76b552')]
    f = fractal(7, ((2, 0.40), (4, 0.30), (8, 0.20), (16, 0.10)),
                contrast=1.25)
    rnd = random.Random(99)
    depth = [3 + rnd.randrange(3) for _ in range(N)]     # ragged overhang
    rows = []
    for y in range(N):
        row = []
        for x in range(N):
            pal = grass if y < depth[x] else dirt
            row.append(pal[min(len(pal) - 1, int(f[y][x] * len(pal)))])
        rows.append(row)
    return rows


def shade(rgb, k):
    return '#%02x%02x%02x' % tuple(
        min(255, max(0, int(c * k + 0.5))) for c in rgb)


def render(top_tex, side_tex, shading):
    top_k, right_k, left_k = shading
    px = {}
    for sy in range(SZ):
        for sx in range(SZ):
            cx, cy = sx + 0.5, sy + 0.5
            d = (cx - SZ / 2) / 2.0
            u, v = (cy + d) / 2.0, (cy - d) / 2.0          # top face
            if 0 <= u < N and 0 <= v < N:
                px[(sx, sy)] = shade(top_tex[int(v)][int(u)], top_k)
                continue
            u_l, w_l = cx / 2.0, (cy - SZ / 4 - cx / 4.0) / 2.0
            if cx < SZ / 2 and 0 <= u_l < N and 0 <= w_l < N:
                px[(sx, sy)] = shade(side_tex[int(w_l)][int(u_l)], left_k)
                continue
            u_r = (cx - SZ / 2) / 2.0
            w_r = (cy - SZ / 2 + u_r) / 2.0
            if 0 <= u_r < N and 0 <= w_r < N:
                px[(sx, sy)] = shade(side_tex[int(w_r)][int(u_r)], right_k)
    return px


def to_svg(px, title):
    rects = []
    for x in range(SZ):
        ys = sorted(y for (xx, y) in px if xx == x)
        if not ys:
            continue
        start, col, prev = ys[0], px[(x, ys[0])], ys[0]
        for y in ys[1:] + [None]:
            c = px[(x, y)] if y is not None else None
            if y != prev + 1 or c != col:
                rects.append((x, start, prev - start + 1, col))
                if y is None:
                    break
                start, col = y, c
            prev = y
    by = {}
    for x, y, h, c in rects:
        by.setdefault(c, []).append((x, y, h))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
           'width="64" height="64" shape-rendering="crispEdges" role="img">',
           '  <title>%s</title>' % title]
    for c in sorted(by, key=lambda k: -len(by[k])):
        d = ''.join('M%d %dh1v%dh-1z' % r for r in by[c])
        out.append('  <path fill="%s" d="%s"/>' % (c, d))
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    used = []

    top = load_png('grass_block_top.png')
    if top is None:
        top, src = fallback_grass_top(), 'generated'
    else:
        src = 'textures/grass_block_top.png'
        if is_greyscale(top):
            top = tint(top, GRASS_TINT)
            src += ' (greyscale, tinted)'
    used.append('grass top:   ' + src)

    side = load_png('grass_block_side.png')
    used.append('grass side:  ' +
                ('textures/grass_block_side.png' if side else 'generated'))
    side = side or fallback_grass_side()

    bed = load_png('bedrock.png')
    used.append('bedrock:     ' +
                ('textures/bedrock.png' if bed else 'generated'))
    bed = bed or fallback_bedrock()

    for name, svg in (
        ('block-grass.svg',
         to_svg(render(top, side, GRASS_SHADE), 'Grass block')),
        ('block-bedrock.svg',
         to_svg(render(bed, bed, BEDROCK_SHADE), 'Bedrock block')),
    ):
        with open(os.path.join(OUT, name), 'w') as fh:
            fh.write(svg)

    print('\n'.join(used))
    print('wrote images/block-grass.svg and images/block-bedrock.svg')


if __name__ == '__main__':
    main()
