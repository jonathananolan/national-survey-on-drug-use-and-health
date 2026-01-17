#!/usr/bin/env python3
"""
Build SQLite database from NSDUH Stata files with normalized age variables
and comprehensive variable metadata
"""
import pandas as pd
import sys
import pyreadstat
import zipfile
import sqlite3
import glob
import os
from pathlib import Path
import numpy as np
from datetime import datetime

# Allow importing concordance loader from metadata pipeline
sys.path.append(str(Path(__file__).parent.parent / '02_build_metadata' / 'extract'))
from concordance_metadata import load_concordance_files

def find_dta_in_zip(zip_path):
    """Find the .dta file in a zip archive"""
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Try to find DS0001 file first
        dta_files = [f for f in z.namelist() if f.lower().endswith('.dta') and 'DS0001' in f.upper()]
        if dta_files:
            return sorted(dta_files, key=len, reverse=True)[0]
        # Otherwise just get any .dta file
        dta_files = [f for f in z.namelist() if f.lower().endswith('.dta')]
        if dta_files:
            return sorted(dta_files, key=len, reverse=True)[0]
    return None

def get_age_var(available_cols):
    """Get the age variable name from available columns"""
    # CATAGE is consistent across all years (1=12-17, 2=18-25, 3=26-34, 4=35+)
    if 'CATAGE' in available_cols:
        return 'CATAGE'
    return None

def decode_catage(catage_value):
    """Convert CATAGE coded value to age group label"""
    mapping = {
        1: '12-17',
        2: '18-25',
        3: '26-34',
        4: '35+'
    }
    return mapping.get(catage_value, None)

def get_weight_var(available_cols, year):
    """Get the analysis weight variable for a given year"""
    # Weight variables by period (for making estimates comparable across time):
    # - 2002-2019: ANALWT_C (harmonized across years per SAMHSA)
    # - 2021+: ANALWT2_C
    # - Pre-2002: ANALWT or ANALWT2

    if 'ANALWT_C' in available_cols:
        return 'ANALWT_C'  # 2002-2019
    elif 'ANALWT2_C' in available_cols:
        return 'ANALWT2_C'  # 2021+
    elif 'ANALWT' in available_cols:
        return 'ANALWT'  # Pre-2002
    elif 'ANALWT2' in available_cols:
        return 'ANALWT2'  # Some pre-2002 years

    return None

def process_year(zip_path, year):
    """Process a single year of data and return DataFrame"""
    print(f"\n{'='*60}")
    print(f"Processing {year}...")
    print(f"{'='*60}")

    # Find DTA file in zip
    dta_file = find_dta_in_zip(zip_path)
    if not dta_file:
        print(f"  ❌ No DTA file found")
        return None

    print(f"  Found DTA file: {dta_file}")

    # Extract and read the DTA file
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extract(dta_file, tmpdir)
            dta_path = os.path.join(tmpdir, dta_file)
            df, meta = pyreadstat.read_dta(dta_path)

        # Normalize all column names to uppercase
        df.columns = df.columns.str.upper()

        print(f"  Total records: {len(df):,}")

        # Get age variable
        age_var = get_age_var(df.columns)
        if age_var is None:
            print(f"  ❌ No age variable found in columns")
            return None

        print(f"  Age variable: {age_var}")

        # Check age statistics
        age_data = df[age_var].dropna()
        if len(age_data) == 0:
            print(f"  ❌ No valid age data")
            return None

        # Since CATAGE is categorical (1-4), show distribution
        print(f"\n  Age Category Distribution (CATAGE):")
        value_counts = age_data.value_counts().sort_index()
        total = len(age_data)

        for cat_value, count in value_counts.items():
            label = decode_catage(cat_value)
            pct = (count / total) * 100
            print(f"    {int(cat_value)}: {label:8} - {count:,} ({pct:.1f}%)")

        print(f"\n  Total valid: {total:,}")
        print(f"  Missing:     {len(df) - total:,}")

        # Sanity checks
        warnings = []
        unique_vals = sorted(age_data.unique())
        if min(unique_vals) < 1 or max(unique_vals) > 4:
            warnings.append(f"⚠️  CATAGE values outside expected range (1-4): {unique_vals}")
        if len(unique_vals) < 4:
            warnings.append(f"⚠️  Missing some age categories. Found: {unique_vals}")

        if warnings:
            print(f"\n  WARNINGS:")
            for w in warnings:
                print(f"    {w}")
        else:
            print(f"\n  ✓ Age categories look good")

        # Create normalized age category column
        df['age_category'] = df[age_var]
        df['age_group'] = df[age_var].apply(decode_catage)

        # Get weight variable
        weight_var = get_weight_var(df.columns, year)
        if weight_var:
            print(f"  Weight variable: {weight_var}")
            df['analysis_weight'] = df[weight_var]
        else:
            print(f"  ⚠️  No weight variable found - creating unit weights")
            df['analysis_weight'] = 1.0

        # Count drug flags present (all columns now uppercase)
        drug_flags = [
            'ALCFLAG', 'COCFLAG', 'HERFLAG', 'MJOFLAG', 'MRJFLAG', 'CIGFLAG',
            'HALFLAG', 'PSYFLAG2', 'SUMFLAG', 'INHFLAG', 'PCPFLAG', 'SMKFLAG',
            'LSDFLAG', 'SEDFLAG', 'STMFLAG', 'TRQFLAG', 'CGRFLAG', 'CRKFLAG',
            'ECSFLAG', 'CDUFLAG', 'PIPFLAG', 'TOBFLAG', 'IEMFLAG', 'MTHFLAG',
            'ANLFLAG', 'SNFFLAG', 'CHWFLAG', 'OXYFLAG', 'DAMTFXFLAG', 'KETMINFLAG'
        ]

        present_flags = [f for f in drug_flags if f in df.columns]
        print(f"\n  Drug flags present: {len(present_flags)}/{len(drug_flags)}")

        if len(present_flags) > 0:
            print(f"  Sample flags: {', '.join(present_flags[:5])}")
            if len(present_flags) > 5:
                print(f"               ... and {len(present_flags) - 5} more")

        # Derived ecstasy ever use with series break when the question adds "molly"
        ecstasy_sources = ['ECSTMOFLAG', 'ECSFLAG', 'ECSTASY']
        ecstasy_source = next((col for col in ecstasy_sources if col in df.columns), None)
        if ecstasy_source:
            df['ecstasy_ever'] = df[ecstasy_source]
            df['ecstasy_ever_source'] = ecstasy_source
        else:
            df['ecstasy_ever'] = pd.NA
            df['ecstasy_ever_source'] = pd.NA

        # Add year column and respondent_id (use index as unique ID within year)
        df['year'] = year
        df['respondent_id'] = df.index

        # Select columns to keep: year, respondent_id, age_category, age_group, analysis_weight, and all drug flags
        cols_to_keep = [
            'year',
            'respondent_id',
            'age_category',
            'age_group',
            'analysis_weight',
            'ecstasy_ever',
            'ecstasy_ever_source',
        ] + present_flags
        df_subset = df[cols_to_keep].copy()

        print(f"\n  ✓ Processed {len(df_subset):,} records with {len(cols_to_keep)} columns")

        return df_subset

def generate_html_report(summary_stats, db_path):
    """Generate HTML report summarizing the database build"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NSDUH Database Build Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px; }}
        .metric {{ display: inline-block; margin: 15px 20px 15px 0; padding: 15px 25px; background: #ecf0f1; border-radius: 5px; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NSDUH Database Build Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-label">Total Years</div>
            <div class="metric-value">{summary_stats['total_years']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Records</div>
            <div class="metric-value">{summary_stats['total_records']:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Columns</div>
            <div class="metric-value">{summary_stats['total_columns']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Database Size</div>
            <div class="metric-value">{summary_stats['db_size_mb']:.1f} MB</div>
        </div>

        <h2>Age Distribution (All Years)</h2>
        <table>
            <tr>
                <th>Age Group</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
    for age_group in ['12-17', '18-25', '26-34', '35+']:
        if age_group in summary_stats['age_distribution']:
            count = summary_stats['age_distribution'][age_group]
            pct = summary_stats['age_percentages'][age_group]
            html += f"""            <tr>
                <td>{age_group}</td>
                <td>{count:,}</td>
                <td>{pct:.1f}%</td>
            </tr>
"""

    html += """        </table>

        <h2>Records by Year</h2>
        <table>
            <tr>
                <th>Year</th>
                <th>Records</th>
                <th>% Under 25</th>
                <th>Avg Age Category</th>
            </tr>
"""
    for year_stat in summary_stats['year_stats']:
        html += f"""            <tr>
                <td>{year_stat['year']}</td>
                <td>{year_stat['count']:,}</td>
                <td>{year_stat['pct_under25']:.1f}%</td>
                <td>{year_stat['avg_age_cat']:.2f}</td>
            </tr>
"""

    html += f"""        </table>

        <h2>Database Tables</h2>
        <table>
            <tr>
                <th>Table</th>
                <th>Records</th>
                <th>Description</th>
            </tr>
            <tr>
                <td><strong>survey_data</strong></td>
                <td>{summary_stats['survey_data_records']:,}</td>
                <td>Individual-level survey responses with drug flags</td>
            </tr>
            <tr>
                <td><strong>variable_metadata</strong></td>
                <td>{summary_stats['metadata_records']:,}</td>
                <td>Comprehensive variable metadata across all years</td>
            </tr>
        </table>

        <div class="footer">
            <p>Database location: {db_path}</p>
            <p>Pipeline step: 03_build_database</p>
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    print("Building NSDUH SQLite Database")
    print("=" * 60)

    # Find all Stata zip files
    data_dir = Path('data')
    zip_files = sorted(glob.glob(str(data_dir / '*stata*.zip')))

    print(f"\nFound {len(zip_files)} Stata files")

    # Process each year
    all_data = []
    successful_years = []
    failed_years = []

    for zip_path in zip_files:
        # Extract year from filename
        basename = os.path.basename(zip_path)
        year = int(basename.split('-')[1])

        df = process_year(zip_path, year)
        if df is not None:
            all_data.append(df)
            successful_years.append(year)
        else:
            failed_years.append(year)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Successfully processed: {len(successful_years)} years")
    print(f"  Years: {successful_years}")
    print(f"Failed to process: {len(failed_years)} years")
    if failed_years:
        print(f"  Years: {failed_years}")

    if len(all_data) == 0:
        print("\n❌ No data to save!")
        return

    # Combine all years
    print(f"\nCombining data from all years...")
    combined_df = pd.concat(all_data, ignore_index=True)

    print(f"Total records: {len(combined_df):,}")
    print(f"Total columns: {len(combined_df.columns)}")
    print(f"\nAge category distribution across all years:")
    age_dist = combined_df['age_group'].value_counts()
    age_percentages = {}
    for group in ['12-17', '18-25', '26-34', '35+']:
        if group in age_dist.index:
            count = age_dist[group]
            pct = (count / len(combined_df)) * 100
            age_percentages[group] = pct
            print(f"  {group}: {count:,} ({pct:.1f}%)")

    # Show records by year
    print(f"\nRecords by year:")
    year_counts = combined_df.groupby('year').size()
    year_stats = []
    for year, count in year_counts.items():
        # Categories 1 and 2 are under 25 (12-17 and 18-25)
        year_data = combined_df[combined_df['year'] == year]
        pct_under25 = (year_data['age_category'] <= 2).sum() / count * 100
        avg_age_cat = year_data['age_category'].mean()
        year_stats.append({
            'year': year,
            'count': count,
            'pct_under25': pct_under25,
            'avg_age_cat': avg_age_cat
        })
        print(f"  {year}: {count:,} records ({pct_under25:.1f}% under 25, avg age cat: {avg_age_cat:.2f})")

    # Save to SQLite
    db_path = 'data/processed/nsduh_data.db'
    print(f"\nSaving to SQLite database: {db_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    combined_df.to_sql('survey_data', conn, if_exists='replace', index=False)

    # Also save to CSV for quick inspection
    csv_path = 'data/processed/nsduh_data.csv'
    print(f"Saving survey_data to CSV: {csv_path}")
    combined_df.to_csv(csv_path, index=False)

    # Create indexes for faster queries
    print("Creating indexes for survey_data...")
    cursor = conn.cursor()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON survey_data(year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_age_category ON survey_data(age_category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year_age ON survey_data(year, age_category)')
    conn.commit()

    # Load and add variable metadata table
    print("\nLoading variable metadata...")
    metadata_path = 'metadata/variable_metadata.csv'
    if Path(metadata_path).exists():
        df_metadata = pd.read_csv(metadata_path)
        print(f"  Found {len(df_metadata):,} metadata records")

        # Save to database
        df_metadata.to_sql('variable_metadata', conn, if_exists='replace', index=False)

        # Create indexes
        print("Creating indexes for variable_metadata...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_variable_name ON variable_metadata(variable_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meta_year ON variable_metadata(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_confirmed ON variable_metadata(confirmed_group)')
        # Broad bridge removed; no broad index to create
        conn.commit()

        metadata_records = len(df_metadata)
    else:
        print(f"  ⚠️  Metadata file not found: {metadata_path}")
        print(f"  Run 02_build_metadata/build_metadata.py first")
        metadata_records = 0

    # Concordance data is included in variable_metadata; no separate table required

    # Show database info
    cursor.execute("SELECT COUNT(*) FROM survey_data")
    row_count = cursor.fetchone()[0]

    cursor.execute("PRAGMA table_info(survey_data)")
    columns = cursor.fetchall()

    print(f"\n✓ Database created successfully!")
    print(f"  Path: {db_path}")
    print(f"  Tables: survey_data, variable_metadata")
    print(f"  Survey records: {row_count:,}")
    print(f"  Metadata records: {metadata_records:,}")
    print(f"  Survey columns: {len(columns)}")
    db_size_mb = os.path.getsize(db_path) / 1024 / 1024
    print(f"  File size: {db_size_mb:.1f} MB")

    conn.close()

    # Generate HTML report
    print("\nGenerating HTML report...")
    summary_stats = {
        'total_years': len(successful_years),
        'total_records': len(combined_df),
        'total_columns': len(combined_df.columns),
        'db_size_mb': db_size_mb,
        'age_distribution': age_dist.to_dict(),
        'age_percentages': age_percentages,
        'year_stats': year_stats,
        'survey_data_records': row_count,
        'metadata_records': metadata_records
    }

    html_content = generate_html_report(summary_stats, db_path)
    report_path = 'reports/03_database_build_report.html'
    os.makedirs('reports', exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(html_content)
    print(f"  Saved report to {report_path}")

    print(f"\n{'='*60}")
    print("DONE!")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
