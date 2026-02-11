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
        Extract structured items (name + price) from self.text.
        Handles:
          - Regular items: ITEM_NAME 5.69 *
          - Weighted produce: BANANAS 2.00 Tb @ 0.54/1b 1.08 *
        Returns a dict with items list and total (if found)
        """
        items = []
        total = None
        skip_next = False  # flag for multi-line weighted produce

        for i, line in enumerate(self.text):
            if skip_next:
                skip_next = False
                continue

            line = line.strip()
            if not line or line.lower() in ("savings", "you saved:"):
                continue

            # Check if next line looks like a weighted produce continuation
            if i + 1 < len(self.text):
                next_line = self.text[i + 1].strip()
                if re.search(r"[\d.,]+\s*(Tb|lb|/1b|@)", next_line):
                    # Merge current line with next line
                    line += " " + next_line
                    skip_next = True

            item = self._parse_item_line(line)
            if item:
                items.append(item)

            # Try to detect total if it looks like "BALANCE DUE 75.77" etc.
            if re.search(r"(total|balance|amount due)", line, re.IGNORECASE):
                numbers = re.findall(r"\d+[.,]?\d*", line)
                if numbers:
                    try:
                        total = float(numbers[-1].replace(",", "."))
                    except ValueError:
                        pass

        return {"items": items, "total": total}
    
    def _parse_item_line(self, line: str):
        """
        Parse a single line into {'name': ..., 'price': ...}.
        Strips out unit markers for weighted produce.
        """
        # Extract all numbers
        numbers = re.findall(r"\d+(?:[.,]\d+)?", line)
        if not numbers:
            return None

        # Last number is assumed to be the price
        raw_price = numbers[-1].replace(",", ".")
        try:
            price = float(raw_price)
        except ValueError:
            price = None

        # Remove numbers and units from name
        name = re.sub(r"(\d+[.,]?\d*\s*(?:Tb|lb|/1b|@)?)+", "", line)
        name = name.replace("*", "").strip()

        if not name:
            return None

        return {"name": name, "price": price}

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