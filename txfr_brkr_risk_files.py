import pandas as pd
import numpy as np
import argparse



#####
# The code needs to get files based on the brkr or txfr assest selection.
# Do all the cleanings and joins
# Give the out put
#####



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default='.', help="path to your datafile working directory")
    parser.add_argument('--type', type=str, default='brkr', help='select between brkr or txfr assets')
    parser.add_argument('--year', type=int, default=2025, help='select the year')
    parser.add_argument('--out', type=str, default='output',help='select the output file')
    parser.add_argument('--line', type=int, default=1, help='selecting the asset line: 1-both T&D, 2- T only, 3-D only')

    ### File names
    parser.add_argument('--t_txfr', type=str, default='TXFR-T_REPLACEMENT LIST_01_12_26.xlsm', help='name of the transformer transmission file')
    parser.add_argument('--d_txfr', type=str, default='D_Transf_Risk_Ranking_Under_Const 2026.xlsx', help='name of the transformer distribution file')
    parser.add_argument('--t_brkr', type=str, default='T_BRKR 1-N Under Const (1 15 2026).xlsx', help='name of the circuit breaker transmission file')
    parser.add_argument('--d_brkr', type=str, default='D BRKR 1-N Under Const 2026.xlsx', help='name of the circuit breaker transmission file')

    ### Failure File

    parser.add_argument('--failure', type=str, default='2024 + Emergency Job Tracker_5_7_25.xlsm', help='name of the failure file')

    args = parser.parse_args()
    return args




def rename_columns(df, old_cols, new_cols):
    """
    Rename a series of columns using two aligned lists.
    """
    if len(old_cols) != len(new_cols):
        raise ValueError("old_cols and new_cols must have the same length")

    return df.rename(columns=dict(zip(old_cols, new_cols)))


def clean_fail(args):

    ### Read and cleaning fail data

    df = pd.read_excel(args.failure, sheet_name = "Emerg Tracker (TCR) 2024 +", index_col=None, na_values=['NA'], skiprows=3, engine='openpyxl')
    sel_cols = ['SAP Equipment Number(s), if available', 'Project Name for SAP (Failed Asset)\n(max. 40 char.)','Equipment Type\n(being replaced)',
            'Voltage (kV)', 'Location\n(Station Name)','Future\nYear\nImpact\n($000)', 
            'Estimated Spend in Current Year\n($000)','Date SAM first contacted',
            'Date Declared Emergency (Date decision to be placed in emergency)',
           'Failure Type', 'In-Serv./Catastrophic Equipment Category (CB, Xfmr, Unitsub, 3ph Reg, Battery)',
           'Outage Customer Minutes (CMIN) In-Service and Catastrophic Failures (XFMR, CB, XFMR Bushings, Minor)',
           'Age at Year of Failure', 'MVA/KVA (Transformer & Regs)', '3Ph or 1Ph? (Transformers and Regs)']

    df_fail = df[sel_cols]

    df_fail = rename_columns(df_fail, sel_cols, ["sap_id", "Project Name", "Equipment Type", "Voltage", "Substation Name", 
                                                "Future Spending", "Current Spending","Discover Date", "Date", "Failure Type",
                                                "Catastrophic Equipment", "CMIN", "Age", "MVA/KVA", "3Ph or 1Ph"])

    df_fail['Date'] = pd.to_datetime(df_fail['Discover Date'], errors='coerce')
    df_fail['Year'] = df_fail['Date'].dt.year
    df_fail['Month'] = df_fail['Date'].dt.month
    df_fail = df_fail[~df_fail["Year"].isna()]


    df_fail['Future Spending'] = pd.to_numeric(df_fail['Future Spending'], errors='coerce').fillna(0).astype(int)
    df_fail['Current Spending'] = pd.to_numeric(df_fail['Current Spending'], errors='coerce').fillna(0).astype(int)
    df_fail["Total Spending"] = df_fail["Future Spending"]+df_fail["Current Spending"]

    split_vals = df_fail['Voltage'].str.split('/', expand=True)
    split_vals = split_vals.apply(pd.to_numeric, errors='coerce')
    split_vals[1] = split_vals[1].fillna(split_vals[0])
    split_vals = split_vals.fillna(np.nan)

    # Assign to new columns
    df_fail['High Vol'] = split_vals[0]
    df_fail['Low Vol']  = split_vals[1]


    if args.type == 'txfr':
        df_txfr =df_fail[(df_fail["Equipment Type"]=="TXFR") & (df_fail['Date']>=f'01-01-{str(args.year)}') & (df_fail['Date']<f'01-01-{str(args.year+1)}')]
        t_count = df_txfr.shape[0]


        df_txfr = df_txfr[["sap_id", "Equipment Type", "Voltage", "Substation Name", 
                                                "Future Spending", "Current Spending", "Date", "Age", "Failure Type"]]


        df_txfr = rename_columns(df_txfr, ['sap_id'], ['Equipment'])

        clean_df = df_txfr

    elif args.type == 'brkr':
        df_cb = df_fail[(df_fail["Equipment Type"]=="BRKR") & (df_fail['Date']>=f'01-01-{str(args.year)}') & (df_fail['Date']<f'01-01-{str(args.year+1)}')]

        t_count = df_cb.shape[0]

        df_cb = df_cb[["sap_id", "Equipment Type", "Voltage", "Substation Name", 
                                                "Future Spending", "Current Spending", "Date", "Age", "Failure Type"]]


        df_cb = rename_columns(df_cb, ['sap_id'], ['Equipment'])

        clean_df = df_cb
        
    else:
        raise ValueError('The type of the asset is not correctly selected. Choose between txfr or brkr.')

    return clean_df, t_count

def asset_data(args):

    if args.type == 'txfr':

        ### transmission asset

        file_loc = r"TXFR-T_REPLACEMENT LIST_01_12_26.xlsm"
        df = pd.read_excel(file_loc, sheet_name = "Mar 2026 Repl Ranking by Phase", index_col=None, na_values=['NA'], skiprows=0)

        sel_cols = ['SAP Equipment ID', 'Sub Name', 'Highest Cumulative POF ',
                    'Reliability Risk Matrix (PoF,CoF)']

        df_t_txfr = df[sel_cols]

        df_t_txfr=rename_columns(df_t_txfr, ['SAP Equipment ID', 'Sub Name', 'Highest Cumulative POF '], 
                                        ['Equipment', 'Substation Name', 'POF'])

        df_t_txfr['line'] = 'T'
      
         ### distribution asset

        file_loc = r"D_Transf_Risk_Ranking_Under_Const 2026.xlsx"
        df = pd.read_excel(file_loc, sheet_name = "Distribution Transformers", index_col=None, na_values=['NA'], skiprows=0, engine='openpyxl')

        sel_cols = ['SAP Equipment I.D.', 'Substation Name', 'Highest POF ', 'Reliability Risk Matrix (PoF,CoF)']

        df_d_txfr = df[sel_cols]

        df_d_txfr=rename_columns(df_d_txfr, ['SAP Equipment I.D.', 'Highest POF '], 
                                ['Equipment', 'POF'])

        df_d_txfr['line'] = 'D'
        if args.line ==1:
            asset_files = pd.concat([df_d_txfr, df_t_txfr])
            asset_files = asset_files[~((asset_files['Equipment'].isin([41158251,
                                        41158253,
                                        41158254,
                                        44918680,
                                        45247388,
                                        45274594])) & 
                                        (asset_files['line']=='T'))]
        elif args.line ==2:
            asset_files = df_t_txfr
            asset_files = asset_files[~((asset_files['Equipment'].isin([41158251,
                                                    41158253,
                                                    41158254,
                                                    44918680,
                                                    45247388,
                                                    45274594])) & 
                                                    (asset_files['line']=='T'))]
        elif args.line == 3:
            asset_files = df_d_txfr
            asset_files = asset_files[~((asset_files['Equipment'].isin([41158251,
                                                    41158253,
                                                    41158254,
                                                    44918680,
                                                    45247388,
                                                    45274594])) & 
                                                    (asset_files['line']=='T'))]
        else:
            raise ValueError('The line of the asset is not correctly selected. Choose between 1,2,3 (T&D, T, D, respectively).')
        asset_files['type'] = 'TXFR'

    elif args.type == 'brkr':
        
        ### transmission asset
        file_loc = r"T_BRKR 1-N Under Const (1 15 2026).xlsx"
        df = pd.read_excel(file_loc, sheet_name = "Transmission Breakers", index_col=None, na_values=['NA'], skiprows=0)

        sel_cols = [' Equipment', 'Substation Name', 'Highest PoF'
                    'Reliability Risk Matrix (PoF,CoF)']

        df_t_brkr = df[sel_cols]


        df_t_brkr=rename_columns(df_t_brkr, [' Equipment', 'Highest PoF'], 
                                ['Equipment', 'POF'])

        df_t_brkr['line'] = 'T'
        ### distribution asset
        file_loc = r"D BRKR 1-N Under Const 2026.xlsx"
        df = pd.read_excel(file_loc, sheet_name = "Distribution Breakers", index_col=None, na_values=['NA'], skiprows=0, engine='openpyxl')

        sel_cols = ['Equipment', 'Substation Name', 'Highest Cummulative PoF',
                    'Reliability Risk Matrix (PoF,CoF)']

        df_d_brkr = df[sel_cols]

        df_d_brkr=rename_columns(df_d_brkr, ['Highest Cummulative PoF'], 
                        ['POF'])
        
        df_d_brkr['line'] = 'D'

        if args.line ==1:
            asset_files = pd.concat([df_d_brkr, df_t_brkr])
            asset_files = asset_files[~((asset_files['Equipment'].isin([40991421])) & (asset_files['line']=='T'))]
        elif args.line ==2:
            asset_files = df_t_brkr
            asset_files = asset_files[~((asset_files['Equipment'].isin([40991421])) & (asset_files['line']=='T'))]
        elif args.line == 3:
            asset_files = df_d_brkr
            asset_files = asset_files[~((asset_files['Equipment'].isin([40991421])) & (asset_files['line']=='T'))]
        else:
            raise ValueError('The line of the asset is not correctly selected. Choose between 1,2,3 (T&D, T, D, respectively).')

        asset_files['type'] = 'BRKR'
    else:
        raise ValueError('The type of the asset is not correctly selected. Choose between txfr or brkr.')

    return asset_files


def join_files(asset_files, clean_df):
    return pd.merge(asset_files,
                    clean_df[["Equipment", "Equipment Type","Date", "Age", "Failure Type"]], 
                    on="Equipment", 
                    how="left", indicator=True)
    


if __name__ == "__main__":
    args = get_args()
    faile_data,count = clean_fail(args)
    faile_data = faile_data.drop_duplicates(subset=['Equipment'], keep='last')
    asset_files = asset_data(args)
    asset_files = asset_files.drop_duplicates(subset=['Equipment'], keep='last')
    df = join_files(asset_files,faile_data)
    
    df.to_csv(f"{args.out}_{args.type}_{args.year}_{'T&D' if args.line == 1 else 'T' if args.line == 2 else 'D'}.csv", index=False)