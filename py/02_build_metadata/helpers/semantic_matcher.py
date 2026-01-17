#!/usr/bin/env python3
"""
Compute semantic bridges (narrow) for variable harmonization.
This is extracted from the original create_two_level_bridge.py logic.
"""

import pandas as pd
import re

def clean_label(label):
    """Clean variable label for comparison."""
    if pd.isna(label):
        return ''

    cleaned = str(label).upper().strip()
    # Remove RC- prefix
    cleaned = re.sub(r'^RC-\s*', '', cleaned)
    # Remove common prefixes
    cleaned = re.sub(r'^(ADULT|YOUTH):\s*', '', cleaned)
    # Remove "EVER USED" when "LIFETIME" is present
    if 'LIFETIME' in cleaned or 'EVER' in cleaned:
        cleaned = re.sub(r'\s*-?\s*EVER\s*USED', '', cleaned)
    return cleaned.strip()

def extract_semantic_features(variable_name, variable_label):
    """Extract semantic features for matching.

    Returns dict with: substance, time_period, measure_type
    """
    text = f"{variable_name} {variable_label}".upper()

    # Substance
    substance = 'other'
    substance_patterns = [
        ('marijuana', r'\b(MARIJUANA|MRJ|MJ)\b'),
        ('cocaine', r'\b(COCAINE|COC|CRACK|CRK)\b'),
        ('heroin', r'\b(HEROIN|HER)\b'),
        ('hallucinogen', r'\b(HALLUCINOGEN|HAL|LSD|PCP)\b'),
        ('alcohol', r'\b(ALCOHOL|ALC)\b'),
        ('tobacco', r'\b(TOBACCO|CIG|SMOKE)\b'),
        ('stimulant', r'\b(STIMULANT|STIM|METH)\b'),
        ('sedative', r'\b(SEDATIVE|SED)\b'),
        ('tranquilizer', r'\b(TRANQUILIZER|TRQ)\b'),
        ('painkiller', r'\b(PAIN|ANALGESIC|ANL)\b'),
        ('inhalant', r'\b(INHALANT|INH)\b'),
    ]
    for sub, pattern in substance_patterns:
        if re.search(pattern, text):
            substance = sub
            break

    # Time period
    time_period = ''
    time_patterns = [
        ('lifetime', r'\b(LIFETIME|EVER)\b'),
        ('past_30_days', r'\b(PAST\s*(30|MONTH|MO))\b'),
        ('past_year', r'\b(PAST\s*(YEAR|12|YR))\b'),
    ]
    for period, pattern in time_patterns:
        if re.search(pattern, text):
            time_period = period
            break

    # Measure type
    measure = 'use'
    if re.search(r'\b(FLAG|INDICATOR)\b', text):
        measure = 'use_indicator'
    elif re.search(r'\b(AGE|FIRST)\b', text):
        measure = 'age_first_use'
    elif re.search(r'\b(ABUSE|DEPEND)\b', text):
        measure = 'abuse_dependence'

    return {
        'substance': substance,
        'time_period': time_period,
        'measure_type': measure
    }

def compute_semantic_bridges(df):
    """Compute narrow cross-year bridges.

    Args:
        df: DataFrame with columns: year, variable_name, variable_label, confirmed_group,
            optionally cross_year_confirmed

    Returns:
        DataFrame with additional columns: clean_label, substance, time_period,
        measure_type, cross_year_narrow
    """
    print("Computing semantic features...")

    # Clean labels
    df['clean_label'] = df['variable_label'].apply(clean_label)

    # Extract semantic features
    features = df.apply(
        lambda row: extract_semantic_features(row['variable_name'], row['variable_label']),
        axis=1
    )
    df['substance'] = features.apply(lambda x: x['substance'])
    df['time_period'] = features.apply(lambda x: x['time_period'])
    df['measure_type'] = features.apply(lambda x: x['measure_type'])

    print("Computing narrow bridges...")
    # Narrow bridge: exact match on variable_name AND semantic features
    df['narrow_key'] = (
        df['variable_name'] + '|' +
        df['clean_label'] + '|' +
        df['time_period'].fillna('') + '|' +
        df['substance']
    )

    def expand_keys_with_confirmed(key_col):
        if 'cross_year_confirmed' not in df.columns:
            return
        has_confirmed = df['cross_year_confirmed'].notna() & (df['cross_year_confirmed'] != '')
        if not has_confirmed.any():
            return
        key_to_confirmed = {}
        for confirmed_id, keys in (
            df.loc[has_confirmed].groupby('cross_year_confirmed')[key_col].unique().items()
        ):
            for key in keys:
                if key not in key_to_confirmed:
                    key_to_confirmed[key] = confirmed_id
        df[key_col] = df[key_col].map(lambda k: key_to_confirmed.get(k, k))

    # Expand narrow groups to include anything matching a confirmed group
    expand_keys_with_confirmed('narrow_key')

    # Group by narrow key and use first year + representative name for stable IDs
    narrow_group_info = (
        df[['narrow_key', 'year', 'variable_name']]
        .sort_values(['year', 'variable_name'])
        .groupby('narrow_key', sort=False)
        .first()
    )
    df['cross_year_narrow'] = df['narrow_key'].map(
        lambda k: f"{narrow_group_info.at[k, 'variable_name']}_narrow_{int(narrow_group_info.at[k, 'year'])}"
    )

    # Clean up temporary columns
    df = df.drop(columns=['narrow_key'])

    print(f"✓ Created {df['cross_year_narrow'].nunique()} narrow bridges")

    return df

if __name__ == "__main__":
    # Test
    test_data = {
        'year': [2002, 2003, 2002, 2003],
        'variable_name': ['MRJFLAG', 'MRJFLAG', 'COCFLAG', 'COCFLAG'],
        'variable_label': ['MARIJUANA - EVER USED', 'MARIJUANA - EVER USED',
                          'COCAINE - EVER USED', 'COCAINE - EVER USED'],
        'confirmed_group': ['MRJ_01', 'MRJ_01', 'COC_01', 'COC_01']
    }
    df = pd.DataFrame(test_data)
    result = compute_semantic_bridges(df)
    print(result[['variable_name', 'clean_label', 'substance', 'cross_year_narrow']])
