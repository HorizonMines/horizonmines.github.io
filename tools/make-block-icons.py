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


def smooth_field(seed, passes=2):
    """Random field softened by neighbourhood averaging.

    Straight per-pixel noise gives speckle; averaging a few times pulls it
    into organic patches, which is what a real block texture looks like.
    Wraps at the edges, since block textures tile.
    """
    rnd = random.Random(seed)
    f = [[rnd.random() for _ in range(N)] for _ in range(N)]
    for _ in range(passes):
        g = [[0.0] * N for _ in range(N)]
        for y in range(N):
            for x in range(N):
                acc = [f[(y + dy) % N][(x + dx) % N]
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
                g[y][x] = sum(acc) / 9.0
        f = g
    lo, hi = min(map(min, f)), max(map(max, f))
    rng = (hi - lo) or 1.0
    return [[(v - lo) / rng for v in row] for row in f]


def ramp(field, tones, gamma=1.0):
    out = []
    for row in field:
        out.append([tones[min(len(tones) - 1, int((v ** gamma) * len(tones)))]
                    for v in row])
    return out


def hexrgb(s):
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


def fallback_bedrock():
    """Bedrock wants the opposite of smoothing.

    Averaging pulls grass and dirt into pleasant patches, but it turns
    bedrock straight back into smooth grey stone. What makes bedrock read
    is high-contrast blotching, so the tone distribution here is bimodal
    -- plenty of near-black and light grey, little middle -- and some
    pixels sample a 2x2 cell so the mottling clumps instead of speckling.
    """
    tones = [hexrgb(c) for c in
             ('#3d3d3d', '#585858', '#727272', '#8e8e8e', '#aaaaaa')]
    cuts = [34, 47, 60, 73]
    rnd = random.Random(17)
    fine = [[rnd.randrange(100) for _ in range(N)] for _ in range(N)]
    coarse = [[rnd.randrange(100) for _ in range(N)] for _ in range(N)]
    pickc = [[rnd.randrange(100) for _ in range(N)] for _ in range(N)]
    rows = []
    for y in range(N):
        row = []
        for x in range(N):
            v = coarse[y // 2][x // 2] if pickc[y][x] < 45 else fine[y][x]
            row.append(tones[sum(1 for c in cuts if v >= c)])
        rows.append(row)
    return rows


def fallback_grass_top():
    tones = [hexrgb(c) for c in
             ('#5d9a3f', '#6aa94a', '#77b755', '#84c560', '#91d16b')]
    return ramp(smooth_field(3, passes=2), tones)


def fallback_grass_side():
    dirt = [hexrgb(c) for c in
            ('#5c4028', '#6b4b30', '#795538', '#876040', '#956b48')]
    grass = [hexrgb(c) for c in
             ('#4a7d33', '#558c3a', '#609a42', '#6ba84a', '#76b552')]
    f = smooth_field(7, passes=2)
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
