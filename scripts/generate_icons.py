import cairosvg
import shutil

icons = [
    ("icon-ios", 180),
    ("icon-android", 192),
    ("icon-desktop", 512),
    ("icon-ipad", 167),
]

for name, size in icons:
    cairosvg.svg2png(
        url=f"static/images/{name}.svg",
        write_to=f"static/images/{name}.png",
        output_width=size,
        output_height=size,
    )
    print(f"{name}.png cree")

shutil.copy("static/images/icon-ios.png", "static/images/icon-192.png")
shutil.copy("static/images/icon-desktop.png", "static/images/icon-512.png")

print("Toutes les icones creees")
