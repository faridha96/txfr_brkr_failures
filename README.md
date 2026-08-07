# Data Generation and Dashboard Setup

## Data Generation Process

The data generation process starts by connecting the transformer (TXFR) and circuit breaker (BRKR) risk files with the Emergency Tracker failure data. This process is performed using the `txfr_brkr_risk_files.py` script.

The script allows you to customize multiple parameters, including:

- Processing year
- Asset type (transformer or circuit breaker)
- Input file names
- Output file names
- Asset line selection
- Working directory path

### Available Arguments

```python
def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--path',
        type=str,
        default='.',
        help='Path to the data working directory'
    )

    parser.add_argument(
        '--type',
        type=str,
        default='brkr',
        help='Select asset type: brkr or txfr'
    )

    parser.add_argument(
        '--year',
        type=int,
        default=2025,
        help='Select the target year'
    )

    parser.add_argument(
        '--out',
        type=str,
        default='output',
        help='Output file name'
    )

    parser.add_argument(
        '--line',
        type=int,
        default=1,
        help='Asset line: 1 = Both T&D, 2 = Transmission only, 3 = Distribution only'
    )

    # Asset files
    parser.add_argument(
        '--t_txfr',
        type=str,
        default='TXFR-T_REPLACEMENT LIST_01_12_26.xlsm',
        help='Transmission transformer file'
    )

    parser.add_argument(
        '--d_txfr',
        type=str,
        default='D_Transf_Risk_Ranking_Under_Const 2026.xlsx',
        help='Distribution transformer file'
    )

    parser.add_argument(
        '--t_brkr',
        type=str,
        default='T_BRKR 1-N Under Const (1 15 2026).xlsx',
        help='Transmission circuit breaker file'
    )

    parser.add_argument(
        '--d_brkr',
        type=str,
        default='D BRKR 1-N Under Const 2026.xlsx',
        help='Distribution circuit breaker file'
    )

    # Failure file
    parser.add_argument(
        '--failure',
        type=str,
        default='2024 + Emergency Job Tracker_5_7_25.xlsm',
        help='Emergency Tracker failure file'
    )

    return parser.parse_args()
```

## Example Data Generation

The following commands generate four output datasets corresponding to TXFR and BRKR assets for both 2025 and 2026:

```bash
python txfr_brkr_risk_files.py --type brkr --year 2025

python txfr_brkr_risk_files.py --type txfr --year 2025

python txfr_brkr_risk_files.py --type brkr --year 2026

python txfr_brkr_risk_files.py --type txfr --year 2026
```

These commands produce four separate datasets:

- BRKR 2025
- TXFR 2025
- BRKR 2026
- TXFR 2026

## Dashboard Data

After the datasets are generated, they can be uploaded to the dashboard.

The current file stored in the **Dashboard Data** folder is a combined version of the four generated datasets listed above.

## Required Dashboard Columns

To run the dashboard, ensure the dataset contains the following columns:

1. `Equipment`
2. `POF`
3. `Reliability Risk Matrix (PoF, CoF)`
4. `type`
5. `line`
6. `sap_id`
7. `Failure Type`
8. `Date`

These columns are currently required for proper dashboard functionality and visualization.