from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = Path('/home/ubuntu/AssaneAI_TiersIntegrated')
OUT = ROOT / 'docs' / 'assane_ai_interface_inventory.png'
items = [
    ('Conversation / réponse', ROOT / 'docs' / 'assane_ai_chat_preview.png'),
    ('Travail en cours', ROOT / 'docs' / 'assane_ai_working_preview.png'),
    ('Ordinateur / exécution', ROOT / 'docs' / 'previews' / 'assane_ai_execution_computer.png'),
    ('Interface mobile', ROOT / 'docs' / 'previews' / 'assane_ai_mobile_interface.png'),
    ('Icône proposée', ROOT / 'docs' / 'previews' / 'assane_ai_app_icon.png'),
    ('Interface principale', ROOT / 'docs' / 'assane_ai_clean_interface_preview.png'),
]
font = ImageFont.load_default()
card_w, card_h = 720, 520
header_h = 92
cols, rows = 2, 3
canvas = Image.new('RGB', (cols * card_w, header_h + rows * card_h), '#07120f')
draw = ImageDraw.Draw(canvas)
draw.text((28, 24), 'ASSANE AI — INVENTAIRE VISUEL DU PROJET', fill='#ffffff', font=font)
draw.text((28, 52), 'Captures et previews disponibles — les panneaux non exécutés sont indiqués comme références.', fill='#a7b6b0', font=font)
for i, (label, path) in enumerate(items):
    x = (i % cols) * card_w
    y = header_h + (i // cols) * card_h
    draw.rectangle((x + 10, y + 10, x + card_w - 10, y + card_h - 10), fill='#111d1a', outline='#18c874', width=2)
    draw.text((x + 26, y + 25), label, fill='#f5c542', font=font)
    if not path.exists():
        draw.text((x + 26, y + 55), f'Fichier absent : {path.name}', fill='#d94a4a', font=font)
        continue
    with Image.open(path) as source:
        source = source.convert('RGB')
        max_w, max_h = card_w - 52, card_h - 84
        thumb = ImageOps.contain(source, (max_w, max_h), method=Image.Resampling.LANCZOS)
        px = x + (card_w - thumb.width) // 2
        py = y + 62 + (max_h - thumb.height) // 2
        canvas.paste(thumb, (px, py))
canvas.save(OUT, optimize=True)
print(OUT)
