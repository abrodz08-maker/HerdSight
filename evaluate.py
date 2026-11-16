"""Evaluate only descriptive properties of synthetic outcome labels; no clinical claims."""
from pathlib import Path
import pandas as pd
p=Path(__file__).resolve().parents[1]/'data'/'BRD_synthetic_10000_cattle.xlsx'
d=pd.read_excel(p,sheet_name='Cattle_Records')
print('Rows:',len(d),'Feedlots:',d.Feedlot_ID.nunique())
print('Synthetic 45-day BRD incidence:',round(d.BRD_Within_45_Days_0_1.mean()*100,2),'%')
print('Missing core input counts:')
for col in ['Arrival_Weight_lb','Age_Months','Transport_Hours','Vaccination_Status','Commingled_0_1','Number_of_Source_Herds','Preconditioned_0_1','Previous_Illness_0_1','Daily_Temperature_Fluctuation_F','Dust_Index_0_to_1','Stocking_Density_sqft_per_head']:
 print(f'  {col}:',int(d[col].isna().sum()))
print('By feedlot:')
print(d.groupby('Feedlot_ID')['BRD_Within_45_Days_0_1'].agg(['size','mean']).to_string())
print('CAUTION: synthetic-label descriptive checks do not validate prediction in real cattle.')
