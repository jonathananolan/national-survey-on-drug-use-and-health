#!/usr/bin/env python3
"""
Extract variable metadata from Stata .dta files.
Returns variable names, labels, and value labels for each year.
"""

import pandas as pd
from pathlib import Path
import zipfile
import tempfile
import shutil

def extract_stata_metadata(year):
    """Extract metadata from a Stata file for a given year.

    Args:
        year: Year to extract metadata for

    Returns:
        DataFrame with columns: year, variable_name, variable_label, value_labels
        Returns None if file not found or error occurs
    """
    # Find the Stata zip file for this year
    data_dir = Path("data")
    stata_files = list(data_dir.glob(f"*{year}*stata*.zip"))

    if not stata_files:
        print(f"⚠️  {year}: No Stata file found")
        return None

    stata_zip = stata_files[0]

    try:
        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(stata_zip, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            # Find the .dta file (some archives use .DTA)
            dta_files = list(Path(tmpdir).rglob("*.dta")) + list(Path(tmpdir).rglob("*.DTA"))
            if not dta_files:
                print(f"⚠️  {year}: No .dta file in archive")
                return None

            dta_file = dta_files[0]

            # Read Stata file metadata only (not full data)
            # This is much faster than loading all data
            with pd.io.stata.StataReader(str(dta_file)) as reader:
                # Get variable names (pandas StataReader doesn't expose varlist)
                variable_labels = reader.variable_labels()
                variable_names = list(variable_labels.keys())

                # Get value labels
                value_label_dict = reader.value_labels()

                # Build result
                results = []
                for var_name in variable_names:
                    var_label = variable_labels.get(var_name, '')

                    # Get value labels for this variable if they exist
                    value_labels_str = ''
                    if var_name in value_label_dict:
                        val_dict = value_label_dict[var_name]
                        # Format as "1=Label1; 2=Label2; ..."
                        value_labels_str = '; '.join([f"{k}={v}" for k, v in val_dict.items()])

                    results.append({
                        'year': year,
                        'variable_name': var_name,
                        'variable_label': var_label,
                        'value_labels': value_labels_str
                    })

                df = pd.DataFrame(results)
                print(f"✓ {year}: Extracted {len(df)} variables")
                return df

    except Exception as e:
        print(f"✗ {year}: Error - {str(e)}")
        return None

def extract_all_stata_metadata(years):
    """Extract metadata from all Stata files.

    Args:
        years: List of years to process

    Returns:
        DataFrame with all metadata combined
    """
    all_metadata = []

    for year in years:
        df = extract_stata_metadata(year)
        if df is not None:
            all_metadata.append(df)

    if all_metadata:
        return pd.concat(all_metadata, ignore_index=True)
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    # Test with a few years
    years = list(range(1979, 2025))
    df = extract_all_stata_metadata(years)
    print(f"\nTotal records: {len(df)}")
    print(f"\nSample:")
    print(df.head(10))
