"""Trace the supplied sheet pixels as safe, lossless-colour SVG paths.

Run with the project's Python after placing the original PNGs in docs/new/.
No font, emoji library, remote asset, raster embedding, quantization or redrawing is used.
The PNGs do not contain their original curves/alpha; the result preserves their pixel detail.
"""
import ast
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BACKGROUND = (23, 33, 43)


def manifest_keys():
    tree = ast.parse((ROOT / "community/stickers.py").read_text())
    return {
        node.targets[0].id: [ast.literal_eval(key) for key in node.value.keys]
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ("FACES", "GESTURES")
    }


def is_background(colour):
    # Remove the sheet's blue-grey matte, including enclosed holes between fingers.
    # Preserve neutral dark greys in the mechanical arm and brown facial features.
    return (max(abs(a - b) for a, b in zip(colour, BACKGROUND)) <= 16
            and abs(colour[1] - colour[0] - 10) <= 8
            and abs(colour[2] - colour[1] - 10) <= 8)


def sticker_pixels(cell):
    pixels = cell.load()
    retained = {(x, y): pixels[x, y]
                for y in range(2, cell.height - 2) for x in range(2, cell.width - 2)
                if not is_background(pixels[x, y])}
    # Flattened screenshot matte leaves isolated, dark compression specks. Keep
    # the actual connected drawing and all bright/coloured satellites (confetti,
    # hearts, halo, motion rays), rather than turning that matte noise into art.
    pending = set(retained)
    components = []
    while pending:
        seed = pending.pop()
        component, queue = {seed}, [seed]
        while queue:
            x, y = queue.pop()
            for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
                neighbour = (x + dx, y + dy)
                if neighbour in pending:
                    pending.remove(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        components.append(component)
    keep = set().union(*(component for component in components
                         if len(component) >= 4 or any(max(retained[p]) >= 100 for p in component)))
    return {point: retained[point] for point in keep}


def trace(cell):
    retained = sticker_pixels(cell)
    if not retained:
        raise ValueError("Empty sticker cell")
    left = min(x for x, _ in retained)
    right = max(x for x, _ in retained) + 1
    top = min(y for _, y in retained)
    bottom = max(y for _, y in retained) + 1
    colours = defaultdict(list)
    for y in range(top, bottom):
        x = left
        while x < right:
            colour = retained.get((x, y))
            if colour is None:
                x += 1
                continue
            end = x + 1
            while end < right and retained.get((end, y)) == colour:
                end += 1
            length = end - x
            colours[colour].append(f"M{x - left} {y - top}h{length}v1h-{length}Z")
            x = end
    scale = 88 / max(right - left, bottom - top)
    dx = (96 - (right - left) * scale) / 2
    dy = (96 - (bottom - top) * scale) / 2
    paths = "".join(f'<path fill="#{r:02X}{g:02X}{b:02X}" d="{"".join(runs)}"/>'
                    for (r, g, b), runs in sorted(colours.items()))
    return f'<g transform="translate({dx:.6f} {dy:.6f}) scale({scale:.6f})">{paths}</g>'


def main():
    keys = manifest_keys()
    destination = ROOT / "static/stickers"
    destination.mkdir(exist_ok=True)
    for group, filename in (("FACES", "img_2.png"), ("GESTURES", "img_3.png")):
        source = ROOT / "docs/new" / filename
        digest = sha256(source.read_bytes()).hexdigest()
        image = Image.open(source).convert("RGB")
        if len(keys[group]) != 48:
            raise ValueError("Each reference sheet has six rows of eight stickers")
        for index, key in enumerate(keys[group]):
            row, column = divmod(index, 8)
            cell = image.crop((round(column * image.width / 8), round(row * image.height / 6),
                               round((column + 1) * image.width / 8), round((row + 1) * image.height / 6)))
            provenance = f"docs/new/{filename}; row {row + 1}, column {column + 1}; SHA256 {digest}"
            svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" width="96" height="96">'
                   f'<!-- {provenance} -->{trace(cell)}</svg>\n')
            (destination / f"{key}.svg").write_text(svg)
        print(f"{filename}: 48 SVG stickers; SHA256 {digest}")


if __name__ == "__main__":
    main()
