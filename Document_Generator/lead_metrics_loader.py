import os
import re
import pandas as pd
from typing import Dict, Any
from datetime import datetime


class LeadMetricsLoader:
    """
    Loads and processes individual dealer lead reports, calculating Q2, Q3, and YTD totals.
    The dealer code is extracted from the filename (e.g., 'Elko Chrysler Dodge Jeep Ram - 26837.csv').
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.dealer_code = self._extract_dealer_code_from_filename()
        self.lead_df = self._load_data()

    # -------------------
    # INTERNAL UTILITIES
    # -------------------

    def _extract_dealer_code_from_filename(self) -> str:
        """Extract the dealer code (e.g., 26837) from filenames like 'Dealer Name - 26837.csv'."""
        filename = os.path.basename(self.file_path)
        match = re.search(r' - (\d+)\.csv$', filename)
        if match:
            return match.group(1)
        else:
            raise ValueError(
                f"❌ Could not find Dealer Code in filename '{filename}'. Expected format: 'Dealer Name - CODE.csv'"
            )

    def _load_data(self) -> pd.DataFrame:
        """Load and clean the CSV data, filtering to the correct dealer."""
        if not os.path.exists(self.file_path):
            print(f"❌ File not found: {self.file_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(self.file_path)
            if df.empty:
                print(f"⚠️ File {self.file_path} is empty.")
                return pd.DataFrame()

            # Normalize and clean
            df.columns = [c.strip() for c in df.columns]
            if 'Created At' not in df.columns or 'Dealer Code' not in df.columns:
                print(f"⚠️ Missing required columns in {self.file_path}. Columns found: {df.columns.tolist()}")
                return pd.DataFrame()

            df['Created At'] = pd.to_datetime(df['Created At'], errors='coerce')
            df.dropna(subset=['Created At'], inplace=True)
            df['Dealer Code'] = df['Dealer Code'].astype(str).str.strip()

            # Filter rows matching the dealer from the filename
            dealer_rows = df[df['Dealer Code'] == self.dealer_code]
            if dealer_rows.empty:
                print(f"⚠️ Dealer code {self.dealer_code} not found in {os.path.basename(self.file_path)}.")
            return dealer_rows

        except Exception as e:
            print(f"❌ Error reading {self.file_path}: {e}")
            return pd.DataFrame()

    # -------------------
    # CALCULATIONS
    # -------------------

    def _calculate_quarterly_periods(self, run_date: datetime) -> Dict[str, pd.Timestamp]:
        """Define Q2, Q3, and YTD periods relative to the given run date."""
        current_year = run_date.year
        return {
            'Q2': (pd.Timestamp(f"{current_year}-04-01"), pd.Timestamp(f"{current_year}-06-30")),
            'Q3': (pd.Timestamp(f"{current_year}-07-01"), pd.Timestamp(f"{current_year}-09-30")),
            'YTD': (pd.Timestamp(f"{current_year}-01-01"), pd.Timestamp(f"{current_year}-09-30")),
        }

    def _count_leads(self, start_date, end_date) -> int:
        """Count leads between two dates."""
        try:
            return self.lead_df[
                (self.lead_df['Created At'] >= start_date) &
                (self.lead_df['Created At'] <= end_date)
            ].shape[0]
        except Exception:
            return 0

    # -------------------
    # PUBLIC API
    # -------------------

    def get_dealer_lead_metrics(self) -> Dict[str, Any]:
        """Calculate and return Q2, Q3, and YTD lead counts."""
        if self.lead_df.empty:
            return {
                "Dealer Code": self.dealer_code,
                "Q2 Leads": 0,
                "Q3 Leads": 0,
                "YTD Leads": 0,
            }

        run_date = datetime(2025, 10, 1)
        periods = self._calculate_quarterly_periods(run_date)

        q2 = self._count_leads(*periods['Q2'])
        q3 = self._count_leads(*periods['Q3'])
        ytd = self._count_leads(*periods['YTD'])

        return {
            "Dealer Code": self.dealer_code,
            "Q2 Leads": q2,
            "Q3 Leads": q3,
            "YTD Leads": ytd,
        }


# Quick local test helper
if __name__ == "__main__":
    sample_path = "lead_reports/Elko Chrysler Dodge Jeep Ram - 26837.csv"
    if os.path.exists(sample_path):
        loader = LeadMetricsLoader(sample_path)
        print(loader.get_dealer_lead_metrics())
    else:
        print("⚠️ Sample file not found for quick test.")
