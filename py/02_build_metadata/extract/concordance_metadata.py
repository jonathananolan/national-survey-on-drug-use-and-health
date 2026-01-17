#!/usr/bin/env python3
"""
Extract concordance information from existing concordance files.
These tell us which variables are officially harmonized by SAMHSA across years.
"""

import pandas as pd
from pathlib import Path
import re

def load_concordance_files():
    """Load all concordance Excel files and combine them.

    Returns:
        DataFrame with columns: year, variable_name, confirmed_group
    """
    concordance_dir = Path("metadata/concordance")

    if not concordance_dir.exists():
        print("⚠️  No concordance directory found")
        return pd.DataFrame()

    # Prefer the official SAMHSA concordance files when present
    preferred_files = [
        concordance_dir / "ConcatPUFComparability_2019.xlsx",
        concordance_dir / "PUFComparability_2024.xlsx",
    ]
    excel_files = [path for path in preferred_files if path.exists()]
    if not excel_files:
        # Fallback to any Excel files in the directory
        excel_files = list(concordance_dir.glob("*.xlsx")) + list(concordance_dir.glob("*.xls"))
        excel_files = [path for path in excel_files if not path.name.startswith("~$")]

    if not excel_files:
        print("⚠️  No concordance files found")
        return pd.DataFrame()

    all_concordance = []

    for excel_file in excel_files:
        try:
            # Read Excel file (detect header row containing VARIABLE)
            preview = pd.read_excel(excel_file, header=None, nrows=12)
            header_row = None
            for idx, row in preview.iterrows():
                normalized = row.astype(str).str.strip().str.upper()
                if (normalized == "VARIABLE").any():
                    header_row = idx
                    break
            if header_row is None:
                for idx, row in preview.iterrows():
                    normalized = row.astype(str).str.strip().str.upper()
                    if normalized.str.startswith("PUF").any():
                        header_row = idx
                        break
            if header_row is None:
                header_row = 0

            df = pd.read_excel(excel_file, header=header_row)

            # Concordance files typically have:
            # - One column per year
            # - Rows are concordance groups
            # - Cells contain variable names

            # Identify variable name column
            variable_col = None
            for col in df.columns:
                if str(col).strip().upper() == "VARIABLE":
                    variable_col = col
                    break
            if variable_col is None:
                print(f"⚠️  {excel_file.name}: VARIABLE column not found")
                continue

            # Melt to long format
            # First, find which columns are years (numeric or look like years)
            def find_year_cols(frame):
                cols = []
                lookup = {}
                for col in frame.columns:
                    col_str = str(col).strip()
                    # Match explicit year columns
                    if col_str.isdigit():
                        year = int(col_str)
                        if 1979 <= year <= 2024:
                            cols.append(col)
                            lookup[col] = year
                        continue

                    # Match PUF columns like "PUF02" or "PUF 21"
                    match = re.search(r"PUF\s*(\d{2})", col_str, flags=re.IGNORECASE)
                    if match:
                        year = 2000 + int(match.group(1))
                        if 1979 <= year <= 2024:
                            cols.append(col)
                            lookup[col] = year
                return cols, lookup

            year_cols, year_lookup = find_year_cols(df)
            if not year_cols:
                # Fallback: these files typically use header row 3
                fallback_header = 3
                if header_row != fallback_header:
                    df = pd.read_excel(excel_file, header=fallback_header)
                    year_cols, year_lookup = find_year_cols(df)

            if not year_cols:
                print(f"⚠️  {excel_file.name}: No year columns found")
                print(f"  header_row={header_row}, columns={list(df.columns)}")
                continue

            # Melt year columns (values are concordance codes)
            df_long = df.melt(
                id_vars=[variable_col],
                value_vars=year_cols,
                var_name='year',
                value_name='confirmed_group'
            )

            # Remove rows with no variable name or concordance group
            df_long = df_long[df_long[variable_col].notna()]
            df_long = df_long[df_long[variable_col] != '']
            df_long = df_long[df_long['confirmed_group'].notna()]
            df_long = df_long[df_long['confirmed_group'] != '']

            # Clean up
            df_long['year'] = df_long['year'].map(year_lookup).astype(int)
            df_long['variable_name'] = df_long[variable_col].astype(str).str.strip().str.upper()
            df_long['confirmed_group'] = df_long['confirmed_group'].astype(str).str.strip()

            # Keep only required columns
            df_long['concordance_file'] = excel_file.name
            df_long = df_long[['year', 'variable_name', 'confirmed_group', 'concordance_file']]

            all_concordance.append(df_long)
            print(f"✓ {excel_file.name}: {len(df_long)} concordance entries")

        except Exception as e:
            print(f"✗ {excel_file.name}: Error - {str(e)}")

    if all_concordance:
        combined = pd.concat(all_concordance, ignore_index=True)
        print(f"\n✓ Total concordance entries: {len(combined)}")
        return combined
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    df = load_concordance_files()
    if not df.empty:
        print(f"\nSample:")
        print(df.head(10))
        print(f"\nYears covered: {sorted(df['year'].unique())}")
        print(f"Variables: {df['variable_name'].nunique()}")
