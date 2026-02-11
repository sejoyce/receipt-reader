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