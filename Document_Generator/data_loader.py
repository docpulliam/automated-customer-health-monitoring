# data_loader.py

import csv
from typing import Dict, Any, List


class DataLoader:
    """
    Loads the Master_Health_Check_Data.csv and maps the original column names to the
    internal keys used throughout the project.

    Input (original headers expected in the CSV):
      - Dealership Number        -> Dealer Code
      - Dealership Name          -> Dealer Name
      - ESHOP Price Match        -> Price Match Syndication
      - New SRP CTA Top          -> New SRP CTA Top
      - New SRP CTA              -> New SRP CTA
      - Tag                      -> Tag
      - Base URL                 -> Base URL (optional; created as "" if missing)

    Output (internal keys guaranteed for every row):
      - Dealer Code
      - Dealer Name
      - Price Match Syndication
      - New SRP CTA Top
      - New SRP CTA
      - Tag
      - Base URL
    """

    # Original headers we require IN the CSV (Base URL is optional)
    REQUIRED_ORIGINAL_COLUMNS = [
        "Dealership Number",
        "Dealership Name",
        "ESHOP Price Match",
        "New SRP CTA Top",
        "New SRP CTA",
        "Tag",
        # "Base URL" is optional; we’ll add an empty one if missing
    ]

    # Map ORIGINAL -> INTERNAL keys
    COLUMN_MAP = {
        "Dealership Number": "Dealer Code",
        "Dealership Name": "Dealer Name",
        "ESHOP Price Match": "Price Match Syndication",
        "New SRP CTA Top": "New SRP CTA Top",
        "New SRP CTA": "New SRP CTA",
        "Tag": "Tag",
        "Base URL": "Base URL",
    }

    # Internal keys we promise to downstream code
    INTERNAL_KEYS = [
        "Dealer Code",
        "Dealer Name",
        "Price Match Syndication",
        "New SRP CTA Top",
        "New SRP CTA",
        "Tag",
        "Base URL",
    ]

    def __init__(self, file_path: str):
        self.file_path = file_path

    @staticmethod
    def _clean(v: Any) -> Any:
        """Strip strings; return as-is for non-strings."""
        if isinstance(v, str):
            return v.strip()
        return v

    def load_data(self) -> List[Dict[str, str]]:
        """Read CSV, validate headers, map to internal keys, guarantee all internal keys."""
        rows: List[Dict[str, str]] = []

        try:
            # utf-8-sig handles BOM if the file came from Excel
            with open(self.file_path, mode="r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                # 1) Validate that the required ORIGINAL headers exist
                fieldnames = reader.fieldnames or []
                missing = [col for col in self.REQUIRED_ORIGINAL_COLUMNS if col not in fieldnames]
                if missing:
                    raise ValueError(
                        f"CSV is missing required columns: {missing}. "
                        f"Found columns: {fieldnames}"
                    )

                # Is Base URL present?
                has_base_url = "Base URL" in fieldnames

                # 2) Map each row to internal keys
                for raw in reader:
                    mapped: Dict[str, Any] = {}

                    # Map known columns
                    for original_key, internal_key in self.COLUMN_MAP.items():
                        if original_key in raw:
                            mapped[internal_key] = self._clean(raw.get(original_key, ""))
                        else:
                            # If the original column doesn't exist (e.g., Base URL), we’ll fill later
                            pass

                    # Ensure Base URL key exists (even if empty)
                    if not has_base_url:
                        mapped["Base URL"] = ""

                    # 3) Guarantee all internal keys exist
                    for key in self.INTERNAL_KEYS:
                        if key not in mapped:
                            mapped[key] = ""

                    rows.append(mapped)

            # Final sanity check — every row must include all internal keys
            for i, r in enumerate(rows, start=1):
                for k in self.INTERNAL_KEYS:
                    if k not in r:
                        raise KeyError(f"Row {i} missing internal key '{k}' after mapping.")

            return rows

        except FileNotFoundError:
            print(f"FATAL ERROR: The file '{self.file_path}' was not found.")
            return []
        except ValueError as e:
            print(f"FATAL ERROR: Data validation failed: {e}")
            return []
        except KeyError as e:
            print(f"FATAL ERROR: Data validation failed after mapping: {e}")
            return []
        except Exception as e:
            print(f"FATAL ERROR: Unexpected error loading data: {e}")
            return []
