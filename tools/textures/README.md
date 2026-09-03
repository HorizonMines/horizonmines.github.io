# Block textures

Drop 16x16 PNGs in here and `../make-block-icons.py` will use them instead
of its generated stand-ins:

| file                    | used for                        |
| ----------------------- | ------------------------------- |
| `grass_block_top.png`   | top face of the Java icon       |
| `grass_block_side.png`  | the two side faces of that icon |
| `bedrock.png`           | all faces of the Bedrock icon   |

Then regenerate:

    python3 tools/make-block-icons.py

It prints which source each face came from, so you can confirm the files were
picked up rather than silently ignored.

Two things worth knowing:

- **The game's `grass_block_top.png` is greyscale.** It gets its colour from a
  per-biome tint at runtime, so dropped in as-is it would render a grey block.
  The script detects this and applies `GRASS_TINT`; adjust that constant if you
  want a different biome's green.
- **Any size other than 16x16 is nearest-neighbour resized**, which will look
  rough. Supply the native 16x16 texture where you can.

Nothing is committed here. Whether a particular texture may be redistributed on
a public site depends on where it came from, and that is a licensing decision
for whoever owns the site.
