#!/usr/bin/env python3
"""
Plot drug trends from the SQLite database
"""
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from pathlib import Path
from datetime import datetime
import os
import math

# Drug flags to plot with nice labels
DRUG_FLAGS = {
    'ALCFLAG': 'Alcohol',
    'COCFLAG': 'Cocaine',
    'HERFLAG': 'Heroin',
    'hallucinogen': 'Hallucinogens',
    'any_illicit': 'Any illicit drug',
    'PCPFLAG': 'PCP',
    'LSDFLAG': 'LSD',
    'CRKFLAG': 'Crack cocaine',
    'ecstasy': 'Ecstasy',
    'TOBFLAG': 'Tobacco',
    'illicit_except_marijuana': 'Illicit drugs except marijuana',
    'methamphetamine': 'Methamphetamine',
    'stimulants': 'Stimulants',
    'marijuana': 'Marijuana',
    'psychotherapeutics': 'Any psychotherapeutics',
    'inhalants': 'Inhalants',
    'tranquilizers': 'Tranquilizers',
    'sedatives': 'Sedatives',
    'ketamine': 'Ketamine',
    'DAMTFXFLAG': 'DMT/AMT/Foxy',
    'GHBFLAG': 'GHB',
    'ICEFLAG': 'Ice',
    'IMFFLAG': 'Illegally made fentanyl',
    'PSILCYFLAG': 'Psilocybin',
    'KRATOMFLAG': 'Kratom',
}

def generate_html_report(summary_stats, output_files):
    """Generate HTML report summarizing the analysis"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NSDUH Trend Analysis Report</title>
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
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NSDUH Trend Analysis Report (Age 18-25)</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-label">Total Years</div>
            <div class="metric-value">{summary_stats['total_years']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Records (18-25)</div>
            <div class="metric-value">{summary_stats['total_records']:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Drug Flags Analyzed</div>
            <div class="metric-value">{summary_stats['drug_flags_count']}</div>
        </div>

        <h2>Drug Flags with Trend Data</h2>
        <table>
            <tr>
                <th>Flag</th>
                <th>Label</th>
                <th>Years Available</th>
            </tr>
"""
    for drug_info in summary_stats['drugs_with_data']:
        html += f"""            <tr>
                <td><code>{drug_info['flag']}</code></td>
                <td>{drug_info['label']}</td>
                <td>{drug_info['year_count']}</td>
            </tr>
"""

    html += """        </table>

        <h2>Visualizations</h2>
"""
    for output_file in output_files:
        if output_file.endswith('.png'):
            html += f"""        <h3>{os.path.basename(output_file)}</h3>
        <img src="../{output_file}" alt="{os.path.basename(output_file)}">
"""

    html += f"""
        <div class="footer">
            <p>Data source: NSDUH SQLite database</p>
            <p>Age group: 18-25 years (age_category = 2)</p>
            <p>Estimates are weighted using survey analysis weights</p>
            <p>Pipeline step: 04_analysis</p>
        </div>
    </div>
</body>
</html>
"""
    return html

def nice_ylim(max_value, headroom=0.02):
    """Set y-axis max with small proportional headroom."""
    if max_value <= 0:
        return 5.0
    return float(max_value * (1.0 + headroom))

def main():
    db_path = 'data/processed/nsduh_data.db'

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("Run 03_build_database/build_database.py first!")
        return

    print(f"Loading data from {db_path}...")
    conn = sqlite3.connect(db_path)

    # Try to load metadata from database, fallback to CSV if not available
    flag_descriptions = {}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='variable_metadata'")
        if cursor.fetchone():
            print("Loading metadata from database...")
            df_meta = pd.read_sql_query("SELECT * FROM variable_metadata", conn)

            # Get first appearance description for each flag
            for flag in DRUG_FLAGS.keys():
                flag_data = df_meta[df_meta['variable_name'] == flag]
                if len(flag_data) > 0:
                    # Get the first year's description
                    first_row = flag_data.sort_values('year').iloc[0]
                    flag_descriptions[flag] = first_row['variable_label']
        else:
            print("⚠️  No metadata table in database, trying CSV...")
            metadata_path = 'metadata/variable_metadata.csv'
            if Path(metadata_path).exists():
                df_meta = pd.read_csv(metadata_path)
                for flag in DRUG_FLAGS.keys():
                    flag_data = df_meta[df_meta['variable_name'] == flag]
                    if len(flag_data) > 0:
                        first_row = flag_data.sort_values('year').iloc[0]
                        flag_descriptions[flag] = first_row['variable_label']
    except Exception as e:
        print(f"⚠️  Could not load metadata: {e}")
        print("Continuing without metadata descriptions...")

    # Get all columns
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(survey_data)")
    all_columns = [col[1] for col in cursor.fetchall()]

    # Find which drug flags are in the database
    available_flags = [flag for flag in DRUG_FLAGS.keys() if flag in all_columns]

    print(f"Found {len(available_flags)} drug flags in database")

    # Detect series breaks for derived flags when source variable changes
    derived_sources = {
        'ecstasy': ['ECSTMOFLAG', 'ECSFLAG', 'ECSTASY'],
        'any_illicit': ['ILLFLAG', 'SUMFLAG'],
        'hallucinogen': ['HALLUCFLAG', 'HALFLAG'],
        'methamphetamine': ['METHAMFLAG', 'MTHFLAG'],
        'illicit_except_marijuana': ['ILLEMFLAG', 'IEMFLAG'],
        'stimulants': ['STMANYFLAG', 'STMFLAG'],
        'marijuana': ['MRJFLAG', 'MJOFLAG'],
        'psychotherapeutics': ['PSYANYFLAG2', 'PSYFLAG2'],
        'inhalants': ['INHALFLAG', 'INHFLAG'],
        'tranquilizers': ['TRQANYFLAG', 'TRQFLAG'],
        'sedatives': ['SEDANYFLAG', 'SEDFLAG'],
        'pain_relievers': ['PNRANYFLAG', 'ANLFLAG'],
        'ketamine': ['KETAFLGR', 'KETMINFLAG'],
    }
    break_years = {}
    for derived_flag, sources in derived_sources.items():
        source_col = f"{derived_flag}_source"
        if source_col not in all_columns:
            continue
        source_df = pd.read_sql_query(
            f"SELECT year, {source_col} FROM survey_data WHERE {source_col} IS NOT NULL",
            conn
        )
        primary_source = sources[0]
        primary_years = source_df[source_df[source_col] == primary_source]['year']
        if len(primary_years) == 0:
            continue
        first_primary_year = int(primary_years.min())
        earlier_sources = source_df[source_df['year'] < first_primary_year][source_col].unique()
        if len(earlier_sources) > 0:
            break_years[derived_flag] = first_primary_year

    # Query data for people aged 18-25 (age_category 2=18-25)
    query = f"""
    SELECT year, age_category, age_group, analysis_weight, {', '.join(available_flags)}
    FROM survey_data
    WHERE age_category = 2
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"Loaded {len(df):,} records for people aged 18-25")
    print(f"Age groups: {df['age_group'].value_counts().to_dict()}")

    # Calculate WEIGHTED percentages by year for each drug
    # Weights account for survey design and make estimates comparable across time
    results = []

    for year in sorted(df['year'].unique()):
        df_year = df[df['year'] == year]
        row = {'year': year}

        for flag in available_flags:
            # Use weighted calculations
            df_valid = df_year[df_year[flag].notna()]
            if len(df_valid) > 0:
                # Weighted count of ever used (flag == 1)
                weighted_ever_used = df_valid[df_valid[flag] == 1]['analysis_weight'].sum()
                # Weighted total
                weighted_total = df_valid['analysis_weight'].sum()

                if weighted_total > 0:
                    pct = (weighted_ever_used / weighted_total) * 100
                    row[flag] = pct
                else:
                    row[flag] = None
            else:
                row[flag] = None

        results.append(row)

    df_trends = pd.DataFrame(results)

    # Ensure output directories exist
    os.makedirs('plots', exist_ok=True)

    # Save to CSV
    # CSV output removed; plot images only

    # Split into core vs illicit plots
    core_flags = [
        flag for flag in [
            'ALCFLAG',
            'any_illicit',
            'TOBFLAG',
            'marijuana',
            'illicit_except_marijuana',
        ] if flag in available_flags
    ]
    illicit_candidates = [
        'COCFLAG',
        'CRKFLAG',
        'HERFLAG',
        'methamphetamine',
        'stimulants',
        'ecstasy',
        'hallucinogen',
        'LSDFLAG',
        'PCPFLAG',
        'ketamine',
        'GHBFLAG',
        'ICEFLAG',
        'IMFFLAG',
        'PSILCYFLAG',
        'KRATOMFLAG',
        'inhalants',
        'sedatives',
        'tranquilizers',
        'psychotherapeutics',
        'DAMTFXFLAG',
    ]
    illicit_flags = [flag for flag in illicit_candidates if flag in available_flags]

    # Count how many illicit drugs have data
    drugs_with_data = []
    for flag in illicit_flags:
        if flag in df_trends.columns:
            data = df_trends[['year', flag]].dropna()
            if len(data) > 0:
                label = DRUG_FLAGS.get(flag, flag)
                drugs_with_data.append((flag, label, len(data)))

    # Order facets by most recent available percent (descending)
    latest_year = df_trends['year'].max()
    latest_values = {}
    for flag, _, _ in drugs_with_data:
        series = df_trends[['year', flag]].dropna()
        if len(series) == 0:
            continue
        most_recent = series[series['year'] == latest_year]
        if most_recent.empty:
            most_recent = series.sort_values('year').tail(1)
        latest_values[flag] = float(most_recent[flag].iloc[0])

    drugs_with_data.sort(
        key=lambda item: latest_values.get(item[0], -1.0),
        reverse=True
    )

    print(f"Creating illicit plot with {len(drugs_with_data)} drugs...")

    # Create faceted plot with shared y-axis scales
    n_drugs = len(drugs_with_data)
    n_cols = 2
    n_rows = (n_drugs + n_cols - 1) // n_cols

    # Increase height to accommodate captions
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n_rows * 7.0), sharey=True)
    if n_drugs == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Define methodology periods with different colors (exclude 2020)
    # Note: 2002-2019 are comparable per SAMHSA PUF harmonization
    periods = [
        (1979, 1998, '#1f77b4', '1979-1998'),
        (1999, 2001, '#ff7f0e', '1999-2001'),
        (2002, 2019, '#2ca02c', '2002-2019'),  # Comparable period
        # Skip 2020
        (2021, 2024, '#9467bd', '2021+')
    ]

    # Use a shared y-limit across illicit drugs for comparability
    illicit_max = 0
    for flag, _, _ in drugs_with_data:
        series_max = df_trends[flag].max(skipna=True)
        if pd.notna(series_max):
            illicit_max = max(illicit_max, float(series_max))
    illicit_ylim = nice_ylim(illicit_max)

    for idx, (flag, label, _) in enumerate(drugs_with_data):
        ax = axes[idx]
        data = df_trends[['year', flag]].dropna()

        # Exclude 2020 data
        data = data[data['year'] != 2020]

        # Plot each methodology period separately with different colors (no connecting lines across breaks)
        for start_year, end_year, color, period_label in periods:
            period_data = data[(data['year'] >= start_year) & (data['year'] <= end_year)]
            if len(period_data) > 0:
                break_year = break_years.get(flag)
                if break_year:
                    left = period_data[period_data['year'] < break_year]
                    right = period_data[period_data['year'] >= break_year]
                    for segment in (left, right):
                        if len(segment) > 0:
                            ax.plot(segment['year'], segment[flag], marker='o', color=color,
                                   linewidth=2, markersize=4, label=period_label if idx == 0 else '')
                else:
                    ax.plot(period_data['year'], period_data[flag], marker='o', color=color,
                           linewidth=2, markersize=4, label=period_label if idx == 0 else '')

        # Add vertical lines for series breaks only (not within 2002-2019)
        ax.axvline(x=1998.5, color='gray', linestyle='--', alpha=0.3, linewidth=1)
        ax.axvline(x=2001.5, color='gray', linestyle='--', alpha=0.3, linewidth=1)
        ax.axvline(x=2019.5, color='gray', linestyle='--', alpha=0.3, linewidth=1)
        # Mark 2020 as excluded
        ax.axvspan(2019.5, 2020.5, alpha=0.2, color='gray')
        break_year = break_years.get(flag)
        if break_year:
            ax.axvline(x=break_year - 0.5, color='gray', linestyle='--', alpha=0.4, linewidth=1)

        # Create title and subtitle; Matplotlib has no per-axis subtitle, so annotate.
        ax.set_title(label, fontsize=10, fontweight='bold', pad=16)

        description = flag_descriptions.get(flag, '')
        if description:
            # Truncate long descriptions
            if len(description) > 60:
                description = description[:57] + '...'
            subtitle = f"{flag}: {description}"
            ax.annotate(
                subtitle,
                xy=(0.0, 1.02),
                xycoords='axes fraction',
                ha='left',
                va='bottom',
                fontsize=6.5,
                color='gray',
                clip_on=False,
            )

        ax.set_xlabel('Year', fontsize=8)
        ax.set_ylabel('Lifetime Use (%)', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(df_trends['year'].min() - 1, df_trends['year'].max() + 1)
        ax.set_ylim(0, illicit_ylim)
        ax.tick_params(labelsize=8)

    # Hide unused subplots
    for idx in range(len(drugs_with_data), len(axes)):
        axes[idx].axis('off')

    plt.suptitle(
        'Drug use by 18-25 year-olds, United States',
        fontsize=14,
        fontweight='bold',
        y=1.0,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig('plots/drug_trends_illicit_facets.png', dpi=200, bbox_inches='tight')
    print("Saved plot to plots/drug_trends_illicit_facets.png")

    # Core plot: alcohol, any illicit, tobacco
    fig, ax = plt.subplots(figsize=(12, 6))
    core_colors = {
        'ALCFLAG': '#1f77b4',
        'any_illicit': '#ff7f0e',
        'TOBFLAG': '#2ca02c',
    }
    plotted_labels = set()
    for flag in core_flags:
        data = df_trends[['year', flag]].dropna()
        data = data[data['year'] != 2020]
        for start_year, end_year, _, _ in periods:
            period_data = data[(data['year'] >= start_year) & (data['year'] <= end_year)]
            if len(period_data) > 0:
                break_year = break_years.get(flag)
                label = DRUG_FLAGS.get(flag, flag)
                label_to_use = label if label not in plotted_labels else None
                if break_year:
                    left = period_data[period_data['year'] < break_year]
                    right = period_data[period_data['year'] >= break_year]
                    for segment in (left, right):
                        if len(segment) > 0:
                            ax.plot(
                                segment['year'],
                                segment[flag],
                                marker='o',
                                color=core_colors.get(flag, '#333333'),
                                linewidth=2,
                                markersize=4,
                                label=label_to_use,
                            )
                            plotted_labels.add(label)
                            label_to_use = None
                else:
                    ax.plot(
                        period_data['year'],
                        period_data[flag],
                        marker='o',
                        color=core_colors.get(flag, '#333333'),
                        linewidth=2,
                        markersize=4,
                        label=label_to_use,
                    )
                    plotted_labels.add(label)

    ax.axvline(x=1998.5, color='gray', linestyle='--', alpha=0.4, linewidth=1.0)
    ax.axvline(x=2001.5, color='gray', linestyle='--', alpha=0.4, linewidth=1.0)
    ax.axvline(x=2019.5, color='gray', linestyle='--', alpha=0.4, linewidth=1.0)
    ax.axvspan(2019.5, 2020.5, alpha=0.2, color='gray')

    core_max = 0
    for flag in core_flags:
        series_max = df_trends[flag].max(skipna=True)
        if pd.notna(series_max):
            core_max = max(core_max, float(series_max))
    core_ylim = nice_ylim(core_max)

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Lifetime Use (%)', fontsize=11)
    ax.set_title(
        'Drug and alcohol use by 18-25 year-olds, United States',
        fontsize=13,
        fontweight='bold',
    )
    ax.grid(True, alpha=0.3)
    ax.set_xlim(df_trends['year'].min() - 1, df_trends['year'].max() + 1)
    ax.set_ylim(0, core_ylim)
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    plt.savefig('plots/drug_trends_core.png', dpi=200, bbox_inches='tight')
    print("Saved plot to plots/drug_trends_core.png")

    # Generate HTML report
    print("\nGenerating HTML report...")
    summary_stats = {
        'total_years': len(df['year'].unique()),
        'total_records': len(df),
        'drug_flags_count': len(drugs_with_data),
        'drugs_with_data': [
            {'flag': flag, 'label': label, 'year_count': year_count}
            for flag, label, year_count in drugs_with_data
        ]
    }

    output_files = [
        'plots/drug_trends_core.png',
        'plots/drug_trends_illicit_facets.png',
    ]

    html_content = generate_html_report(summary_stats, output_files)
    report_path = 'reports/04_analysis_report.html'
    os.makedirs('reports', exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(html_content)
    print(f"Saved report to {report_path}")

    print("\n✓ Done!")

if __name__ == '__main__':
    main()
