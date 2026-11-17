"""Generate the 3 sample receipt PNG images and expected.json.

Run from the project root:
    python scripts/generate_sample_receipts.py

Item prices in each receipt add up exactly to the receipt total.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "sample_receipts"

RECEIPTS = [
    {
        "receipt_id": "trader-joes-20261110",
        "file": "trader-joes-2026-11-10.png",
        "store_name": "Trader Joe's",
        "date": "2026-11-10",
        "transaction_time": "2026-11-10T14:32:00.000000Z",
        "total_amount": 42.18,
        "currency": "USD",
        "items": [
            {"name": "Organic Bananas", "price": 3.49, "quantity": 1},
            {"name": "Whole Milk", "price": 4.29, "quantity": 1},
            {"name": "Sourdough Bread", "price": 4.99, "quantity": 1},
            {"name": "Chicken Breast", "price": 12.49, "quantity": 1},
            {"name": "Avocados", "price": 5.99, "quantity": 1},
            {"name": "Coffee Beans", "price": 10.93, "quantity": 1},
        ],
    },
    {
        "receipt_id": "starbucks-20261112",
        "file": "starbucks-2026-11-12.png",
        "store_name": "Starbucks",
        "date": "2026-11-12",
        "transaction_time": "2026-11-12T09:15:00.000000Z",
        "total_amount": 6.45,
        "currency": "USD",
        "items": [
            {"name": "Grande Pike Place Coffee", "price": 3.45, "quantity": 1},
            {"name": "Blueberry Muffin", "price": 3.00, "quantity": 1},
        ],
    },
    {
        "receipt_id": "target-20261114",
        "file": "target-2026-11-14.png",
        "store_name": "Target",
        "date": "2026-11-14",
        "transaction_time": "2026-11-14T18:05:00.000000Z",
        "total_amount": 87.20,
        "currency": "USD",
        "items": [
            {"name": "Notebook", "price": 12.99, "quantity": 1},
            {"name": "Water Bottle", "price": 18.49, "quantity": 1},
            {"name": "T-Shirt", "price": 15.00, "quantity": 1},
            {"name": "Headphones", "price": 29.99, "quantity": 1},
            {"name": "Snacks", "price": 10.73, "quantity": 1},
        ],
    },
]


def _font(bold=False, size=28):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def draw_receipt(receipt):
    width = 640
    height = 408 + len(receipt["items"]) * 52
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = 30
    draw.text((width // 2, y), receipt["store_name"], fill="black", font=_font(True, 44), anchor="ma")
    y += 70
    draw.text((width // 2, y), "RECEIPT", fill="black", font=_font(False, 26), anchor="ma")
    y += 50
    draw.line([(40, y), (width - 40, y)], fill="black", width=2)
    y += 20
    draw.text((40, y), f"Date: {receipt['date']}", fill="black", font=_font(False, 28))
    y += 48
    draw.text((40, y), f"Receipt ID: {receipt['receipt_id']}", fill="black", font=_font(False, 24))
    y += 50
    draw.line([(40, y), (width - 40, y)], fill="black", width=2)
    y += 20
    for item in receipt["items"]:
        draw.text((40, y), item["name"], fill="black", font=_font(False, 28))
        draw.text((width - 40, y), f"${item['price']:.2f}", fill="black", font=_font(False, 28), anchor="ra")
        y += 52
    draw.line([(40, y), (width - 40, y)], fill="black", width=2)
    y += 20
    draw.text((40, y), "TOTAL", fill="black", font=_font(True, 34))
    draw.text((width - 40, y), f"${receipt['total_amount']:.2f} USD", fill="black", font=_font(True, 34), anchor="ra")
    y += 60
    draw.text((width // 2, y), "Thank you!", fill="black", font=_font(False, 26), anchor="ma")
    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for receipt in RECEIPTS:
        img = draw_receipt(receipt)
        img.save(OUT_DIR / receipt["file"])
        print(f"Wrote {receipt['file']} total {receipt['total_amount']:.2f}")
    expected = [
        {k: receipt[k] for k in ("receipt_id", "store_name", "transaction_time", "total_amount", "currency", "items", "file")}
        for receipt in RECEIPTS
    ]
    (OUT_DIR / "expected.json").write_text(json.dumps(expected, indent=2), encoding="utf-8")
    print("Wrote expected.json")


if __name__ == "__main__":
    main()
