import re
from backend.receipt_reader import read_itemlist


class Receipt:
    def __init__(self, text: str):
        # Store raw lines
        self.text = [line.strip() for line in text.splitlines() if line.strip()]
        self.store = None
        self.date = None

        self.extract_metadata()

    @classmethod
    def from_text(cls, text: str):
        return cls(text)

    def extract_metadata(self):
        """
        Extract store name and date from receipt lines.
        """

        # Date detection
        date_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})"
        )

        for line in self.text:
            date_match = date_pattern.search(line)
            if date_match:
                self.date = date_match.group(0)
                break

        # Store name (naive: first line)
        if self.text:
            self.store = self.text[0]

    def extract_items(self):
        """
        Extract structured item + price pairs from OCR lines.
        """
        items = []
        total = None

        price_pattern = re.compile(r"-?\d+[.,]\d{2}")

        skip_words = [
            "SAVINGS",
            "YOU SAVED",
            "BALANCE DUE",
            "DISCOVER",
            "SUBTOTAL",
            "TAX",
        ]

        for line in self.text:
            clean_line = line.strip()

            # Skip empty lines
            if not clean_line:
                continue

            # Skip obvious non-item lines
            if any(word in clean_line.upper() for word in skip_words):
                continue

            # Find all price-like values
            prices = price_pattern.findall(clean_line)

            if prices:
                # Normalize commas to dots
                prices = [p.replace(",", ".") for p in prices]

                # Last price is usually the item price
                price = float(prices[-1])

                # Detect total
                if "BALANCE" in clean_line.upper():
                    total = price
                    continue

                # Remove price from name
                name = price_pattern.sub("", clean_line)
                name = re.sub(r"[\*\t]", "", name)
                name = name.strip()

                # Skip negative prices (discount lines)
                if price < 0:
                    continue

                # Skip very short names
                if len(name) < 3:
                    continue

                items.append({
                    "name": name,
                    "price": price
                })

        return {
            "items": items,
            "total": total
        }

    def save_items(self):
        """
        Update ingredient list for fuzzy correction.
        """
        items, fname = read_itemlist()

        new_items = []
        for item in self.text:
            spl = item.split()
            if len(spl) > 1:
                item_name = " ".join(spl[:-1])
                new_items.append(item_name)

        items.extend(new_items)

        unique_items = set(items)
        write_items = [item + "\n" for item in unique_items]

        with open(fname, "w") as f:
            f.writelines(write_items)