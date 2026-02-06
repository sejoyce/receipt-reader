from PIL import Image, ImageOps, ImageFilter
import pytesseract
from rapidfuzz import process, fuzz
import re
import os

from backend.receipt_reader import read_itemlist, fuzzy_correct_text  # assuming your helper functions exist


class Receipt:
    def __init__(self, fname: str, expected_items: list[str] = None):
        """
        fname: path to receipt image
        expected_items: list of known product names for fuzzy correction
        """
        self.fname = fname
        self.expected_items = expected_items or []
        self.text = []
        self.date = None
        self.store = None

        self.init_read()
        self.extract_metadata()

    def init_read(self):
        """Load the image, preprocess, run OCR, and optionally apply fuzzy correction."""
        # Load image
        img = Image.open(self.fname)

        # --- Preprocessing ---
        img = img.convert("L")  # grayscale
        img = ImageOps.autocontrast(img)  # increase contrast

        # Resize to help OCR
        scale = 2
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)

        # Binarize
        threshold = 160
        img = img.point(lambda p: 255 if p > threshold else 0)

        # Denoise
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # OCR
        text = pytesseract.image_to_string(img, config="--psm 6")

        # Apply fuzzy correction if we have expected items
        if self.expected_items:
            text = fuzzy_correct_text(text, self.expected_items, threshold=75)

        # Keep only non-empty lines
        self.text = [line for line in text.splitlines() if line.strip()]

    def extract_metadata(self):
        """
        Automatically extract store name and date from the receipt lines.
        You can implement regex-based heuristics here.
        """
        # Example: naive date scan (YYYY-MM-DD or DD/MM/YYYY)
        date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})")
        for line in self.text:
            date_match = date_pattern.search(line)
            if date_match:
                self.date = date_match.group(0)
                break

        # Example: first line as store name (can be refined)
        if self.text:
            self.store = self.text[0]

    def save_items(self):
        """Update ingredient list for fuzzy correction."""
        items, fname = read_itemlist()

        new_items = []
        for item in self.text:
            spl = item.split()
            if len(spl) > 1:
                item_name = ' '.join(spl[:-1])
                new_items.append(item_name)

        items.extend(new_items)
        unique_items = set(items)
        write_items = [item + '\n' for item in unique_items]

        with open(fname, 'w') as f:
            f.writelines(write_items)