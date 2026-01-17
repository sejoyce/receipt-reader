from PIL import Image, ImageOps, ImageFilter
import pytesseract
import pandas as pd
import os

from rapidfuzz import process, fuzz

import re
import sqlite3

def split_line(line: str):
    """
    Split an OCR line into product string and cleaned price.
    Assumes the price is the last number in the line.
    Returns (product, price) where price is a float or None.
    """

    # Try to grab the last numeric-looking token
    match = re.search(r"(\d+[.,]?\d*)\s*$", line)
    if not match:
        return line.strip(), None

    raw_price = match.group(1)
    product = line[:match.start()].strip()

    # Normalize and fix decimals
    raw_price = raw_price.replace(",", ".")  # handle commas as decimals
    try:
        price = float(raw_price)
    except ValueError:
        price = None

    if price is not None:
        # If OCR dropped the decimal, fix based on assumption (< 100)
        if "." not in raw_price and price > 100:
            price = price / 100.0

    return product, f"{price:0.2f}"

def clean_price(raw_price: str) -> float | None:
    """
    Clean up OCR price string.
    Ensures decimals are placed correctly if missing.
    Assumes all valid prices are < 100.
    """
    # Extract digits and possible decimal
    match = re.search(r"\d+(\.\d{1,2})?", raw_price)
    if not match:
        return None
    
    price_str = match.group(0)

    # Convert to float
    try:
        price = float(price_str)
    except ValueError:
        return None

    # If no decimal found and price > 100, fix it
    if "." not in price_str and price > 100:
        # Assume last two digits are cents
        price = price / 100.0

    return price


def fuzzy_correct_text(ocr_text, expected_words, wholerow = True, threshold=85):
    """
    Correct OCR text by fuzzy matching tokens to expected words.
    
    Parameters:
        ocr_text (str): Raw OCR output
        expected_words (list[str]): Known vocabulary
        threshold (int): Minimum similarity score (0-100) for replacement
    
    Returns:
        str: Corrected OCR text
    """
    lines = ocr_text.splitlines()
    lines = [line.strip() for line in lines if line.strip()]

    corrected_tokens = []

    for line in lines:
        product, price = split_line(line)
        #print(product, "PRICE", price)
        newline = ""

        if wholerow:
            match, score, _ = process.extractOne(product, expected_words, scorer=fuzz.partial_ratio)
            if score >=threshold:
                newline += match
                print(product, match, score)

            else:
                newline = product
            
        else:
            for token in product.split():
                # Find best match from expected words
                match, score, _ = process.extractOne(token, expected_words, scorer=fuzz.partial_ratio)
                if score >= threshold:
                    newline += match
                else:
                    newline += token
                newline += ' '
            
        if price: newline += price
        corrected_tokens.append(newline)

    return "\n".join(corrected_tokens)

def get_expected_words():
    df = pd.read_csv(r"ingredients.csv")
    ingredients = list(df.iloc[:,0])
    ingredients = [x.upper() for x in ingredients]

    return df, ingredients

class receipt:
    def __init__(self, fname):
        self.fname = fname
        self.init_read()
        self.edit_text()

    def init_read(self):
        # Load image
        img = Image.open(self.fname)

        # --- Preprocessing steps ---
        # 1. Convert to grayscale
        img = img.convert("L")

        # 2. Increase contrast (stretch pixel values)
        img = ImageOps.autocontrast(img)

        # 3. Optional: resize (helps OCR on small text)
        scale = 2  # 2x enlargement
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)

        # 4. Optional: binarize (threshold to pure black/white)
        threshold = 160
        img = img.point(lambda p: 255 if p > threshold else 0)

        # 5. Optional: denoise slightly
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # --- Run OCR ---
        text = pytesseract.image_to_string(img, config="--psm 6")

        if any(expected_items):
            text = fuzzy_correct_text(text, expected_items, threshold = 75)

        text = text.splitlines()
        self.text = text[:]

    def edit_text(self):
        editor = TextEditor(self.text, self.fname)
        editor.edit_text_gui()
        text = editor.text
        date = editor.date
        store = editor.store

        self.date = date
        self.store = store
        self.text = text

        print(self.store, self.date)

    def scan_for_date(self):
        ...

    def scan_for_store(self):
        ...

    def save_items(self):
        #save item list to fuzzy matching for future ease
        items, fname = read_itemlist()

        new_items = []
        for item in self.text:
            spl = item.split()
            item_name = ' '.join(spl[:-1])
            new_items.append(item_name)

        items.extend(new_items)

        unique_items = set(items)
        write_items = [item + '\n' for item in unique_items]

        with open(fname, 'w') as f:
            f.writelines(write_items)


    def write_to_db(self):
        #write data to database using sql
        ...

def read_itemlist(fname = 'ingredients2.txt'):
    if os.path.exists(fname):
        with open(fname, 'r') as f:
            items = f.read().splitlines()
    else:
        items = []
    return items, fname
    ...

if __name__ == '__main__':

    expected_items, _ = read_itemlist()

    receipt_dir = 'receipts'
    receipts = os.listdir(receipt_dir)
    receipts = [os.path.join(receipt_dir, r) for r in receipts]

    db_name = 'test.db'
    print(receipts[0])
    foo = receipt(receipts[0])