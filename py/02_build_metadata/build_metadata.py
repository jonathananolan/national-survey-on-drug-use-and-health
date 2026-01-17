#!/usr/bin/env python3
"""
Build comprehensive variable_metadata.csv combining all metadata sources:
1. Stata file variable labels
2. DDI question text (where available)
3. Concordance mappings (official SAMHSA harmonization)
4. Inferred narrow concordance (semantic matching)
"""

import sys
from pathlib import Path
import pandas as pd

# Add extract subfolder to path to import extraction modules
sys.path.append(str(Path(__file__).parent / 'extract'))

from stata_metadata import extract_all_stata_metadata
from ddi_metadata import extract_all_ddi_metadata
from concordance_metadata import load_concordance_files

# Import the semantic matching logic from helper module
sys.path.append(str(Path(__file__).parent / 'helpers'))
from semantic_matcher import compute_semantic_bridges

def build_variable_metadata():
    """Build comprehensive variable metadata CSV."""

    print("="*70)
    print("BUILDING VARIABLE METADATA")
    print("="*70)

    years = list(range(1979, 2025))

    # Step 1: Extract Stata metadata (variable names and labels)
    print("\n[1/5] Extracting Stata metadata...")
    df_stata = extract_all_stata_metadata(years)

    if df_stata.empty:
        print("✗ No Stata metadata extracted. Exiting.")
        return

    print(f"✓ Extracted {len(df_stata)} variable-year combinations")

    # Step 2: Extract DDI question text
    print("\n[2/5] Extracting DDI question text...")
    ddi_data = extract_all_ddi_metadata(years)

    # Merge DDI into Stata metadata
    df_stata['question_text'] = ''
    for year in ddi_data:
        for idx, row in df_stata[df_stata['year'] == year].iterrows():
            var_name = row['variable_name']
            if var_name in ddi_data[year]:
                df_stata.at[idx, 'question_text'] = ddi_data[year][var_name]

    ddi_count = (df_stata['question_text'] != '').sum()
    print(f"✓ Added question text for {ddi_count} variables")

    # Step 3: Load concordance mappings
    print("\n[3/5] Loading SAMHSA concordance...")
    df_concordance = load_concordance_files()

    if not df_concordance.empty:
        # Merge concordance group into main dataframe
        df_stata = df_stata.merge(
            df_concordance[['year', 'variable_name', 'confirmed_group', 'concordance_file']],
            on=['year', 'variable_name'],
            how='left'
        )
        concordance_count = df_stata['confirmed_group'].notna().sum()
        print(f"✓ Matched {concordance_count} variables to confirmed groups")
    else:
        df_stata['confirmed_group'] = ''
        df_stata['concordance_file'] = ''

    # Add confirmed cross-year key based on official concordance
    has_concordance = df_stata['confirmed_group'].notna() & (df_stata['confirmed_group'] != '')
    df_stata['cross_year_confirmed'] = ''
    df_stata.loc[has_concordance, 'cross_year_confirmed'] = (
        df_stata.loc[has_concordance, 'variable_name'].astype(str) + '_' +
        df_stata.loc[has_concordance, 'concordance_file'].astype(str) + '_' +
        df_stata.loc[has_concordance, 'confirmed_group'].astype(str)
    )

    # Step 4: Compute semantic bridges (narrow)
    print("\n[4/5] Computing semantic bridges...")
    df_with_bridges = compute_semantic_bridges(df_stata)

    # Step 5: Save result
    print("\n[5/5] Saving variable_metadata.csv...")
    output_path = Path("metadata/variable_metadata.csv")
    output_path.parent.mkdir(exist_ok=True)

    df_with_bridges.to_csv(output_path, index=False)

    print(f"✓ Saved to {output_path}")
    print(f"\nFinal metadata:")
    print(f"  - Total records: {len(df_with_bridges):,}")
    print(f"  - Years: {df_with_bridges['year'].min()}-{df_with_bridges['year'].max()}")
    print(f"  - Unique variables: {df_with_bridges['variable_name'].nunique():,}")
    print(f"  - With question text: {(df_with_bridges['question_text'] != '').sum():,}")
    print(f"  - With confirmed: {df_with_bridges['confirmed_group'].notna().sum():,}")
    print(f"  - Narrow bridges: {df_with_bridges['cross_year_narrow'].nunique():,}")

    print("\n" + "="*70)
    print("METADATA BUILD COMPLETE")
    print("="*70)

if __name__ == "__main__":
    build_variable_metadata()
