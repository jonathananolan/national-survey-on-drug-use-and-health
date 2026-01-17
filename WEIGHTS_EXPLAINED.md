# Survey Weights in NSDUH Analysis

## Why Use Weights?

Survey weights are essential for making NSDUH estimates:
1. **Representative of the US population** - not just the sample
2. **Comparable across years** - adjusts for sampling design changes
3. **Corrects for non-response** - accounts for people who didn't participate
4. **Adjusts for complex survey design** - stratification, clustering, etc.

## Weight Variables by Period

### 2002-2019: `ANALWT_C`
- **Final Person-Level Sample Weight**
- Harmonized across all years (comparability code = 1 in concordance file)
- Accounts for:
  - Sampling design
  - Non-response adjustment
  - Post-stratification to Census estimates
  - Mode effects (after 2015 questionnaire redesign)

### 2021+: `ANALWT2_C`
- **Final Person-Level Sample Weight 2**
- Adjusted for multimode data collection (web + in-person)
- Includes mode composition weights:
  - Target: 70% in-person, 30% web
  - Removes bias from varying mode proportions

### Pre-2002: `ANALWT` or `ANALWT2`
- **Analysis Weight** (varies by year)
- Generally comparable within pre-2002 period
- Different methodology than post-2002

## How Weights Are Used

### Without Weights (WRONG):
```python
pct = (df[drug_flag] == 1).sum() / len(df) * 100
```
This gives the percentage in the *sample*, not the US population.

### With Weights (CORRECT):
```python
weighted_ever_used = df[df[drug_flag] == 1]['analysis_weight'].sum()
weighted_total = df['analysis_weight'].sum()
pct = (weighted_ever_used / weighted_total) * 100
```
This gives the weighted percentage, representing the **US population aged 18-25**.

## Implementation in Our Code

### Database Builder ([build_database.py](build_database.py))
```python
def get_weight_var(available_cols, year):
    """Get the analysis weight variable for a given year"""
    if 'ANALWT_C' in available_cols:
        return 'ANALWT_C'  # 2002-2019
    elif 'ANALWT2_C' in available_cols:
        return 'ANALWT2_C'  # 2021+
    elif 'ANALWT' in available_cols:
        return 'ANALWT'  # Pre-2002
```

Adds `analysis_weight` column to database for all years.

### Plotting Script ([plot_from_database.py](plot_from_database.py))
```python
# Calculate WEIGHTED percentages
for flag in available_flags:
    df_valid = df_year[df_year[flag].notna()]
    weighted_ever_used = df_valid[df_valid[flag] == 1]['analysis_weight'].sum()
    weighted_total = df_valid['analysis_weight'].sum()
    pct = (weighted_ever_used / weighted_total) * 100
```

## Why This Matters for Comparability

The **2002-2019 comparability** is achieved through:

1. **Consistent weight methodology**: `ANALWT_C` uses same approach across all years
2. **Mode effect adjustments**: 2015+ weights account for questionnaire changes
3. **SAMHSA validation**: Concordance file confirms weights maintain comparability

Without weights, you would see:
- Biased estimates (not representative of US population)
- Spurious trends from sampling design changes
- Incomparable estimates across years

**With weights, the 2002-2019 period shows true population-level drug use trends for ages 18-25.**

## Sources

- SAMHSA PUF Comparability documentation (`ConcatPUFComparability_2019.xlsx`)
- NSDUH Codebooks (2002-2024)
- Variable harmonization file (`nsduh_harmonized.csv`)
