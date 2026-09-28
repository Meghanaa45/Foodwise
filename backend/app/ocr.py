"""
Receipt scanning: OCR raw text off a photo, then resolve each line to a
known ingredient. OCR gets you text; the actual product ("GV WHL MLK 1GAL")
still needs to be matched to an ingredient ("milk"), which is the part
handled here with fuzzy string matching against the ingredient table.
"""
import io
import re
from typing import List

from PIL import Image
from rapidfuzz import process, fuzz

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

QUANTITY_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[xX]?\s*")
NOISE_TOKENS = {"total", "subtotal", "tax", "cash", "change", "card", "balance", "visa", "debit", "credit"}

MATCH_THRESHOLD = 60


def extract_text(image_bytes: bytes) -> str:
    if not TESSERACT_AVAILABLE:
        raise RuntimeError(
            "pytesseract/tesseract-ocr is not installed on this server. "
            "Install the tesseract-ocr system package to enable receipt scanning."
        )
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "L":
        image = image.convert("L")
    return pytesseract.image_to_string(image)


def _clean_line(line: str) -> str:
    line = re.sub(r"[$]?\d+\.\d{2}\s*$", "", line)  # strip trailing price
    line = re.sub(r"[^a-zA-Z0-9\s\.]", " ", line)
    return line.strip()


def parse_receipt_lines(raw_text: str) -> List[str]:
    lines = []
    for raw_line in raw_text.splitlines():
        cleaned = _clean_line(raw_line)
        if len(cleaned) < 3:
            continue
        if any(token in cleaned.lower() for token in NOISE_TOKENS):
            continue
        if cleaned.replace(".", "").isdigit():
            continue
        lines.append(cleaned)
    return lines


def match_to_ingredients(lines: List[str], known_ingredient_names: List[str]):
    """
    Returns a list of dicts: raw_text, matched_ingredient_name, match_confidence,
    quantity, unit. quantity/unit are best-effort guesses (default to 1 unit)
    since receipts rarely spell these out explicitly.
    """
    results = []
    for line in lines:
        quantity = 1.0
        qty_match = QUANTITY_PATTERN.match(line)
        rest = line
        if qty_match:
            try:
                quantity = float(qty_match.group(1))
                rest = line[qty_match.end():]
            except ValueError:
                pass

        match = process.extractOne(rest.lower().strip(), known_ingredient_names, scorer=fuzz.WRatio)
        if match:
            matched_name, confidence, _ = match
        else:
            matched_name, confidence = None, 0.0

        results.append(
            {
                "raw_text": line,
                "matched_ingredient_name": matched_name if confidence >= MATCH_THRESHOLD else None,
                "match_confidence": round(confidence / 100.0, 2),
                "quantity": quantity,
                "unit": "unit",
            }
        )
    return results
