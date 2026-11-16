"""Reproducible NEW synthetic sample. Not the generator of the supplied 10k workbook."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--rows',type=int,default=120);p.add_argument('--seed',type=int,default=2026);p.add_argument('--output',default='data/reproducible_sample.csv');a=p.parse_args()
r=np.random.default_rng(a.seed);n=a.rows
feedlots=['TX_Panhandle_1','TX_Panhandle_2','Western_KS_1','Western_KS_2']
d=pd.DataFrame({'Animal_ID':[f'SAMPLE{i:05}' for i in range(n)],'Feedlot_ID':r.choice(feedlots,n),
'Arrival_Date':pd.Timestamp('2026-10-01')+pd.to_timedelta(r.integers(0,35,n),unit='D'),
'Age_Months':r.integers(7,19,n),'Arrival_Weight_lb':r.integers(400,900,n),
'Transport_Hours':r.uniform(1,15,n).round(1),'Vaccination_Status':r.choice(['Full','Partial','None'],n),
'Commingled_0_1':r.integers(0,2,n),'Number_of_Source_Herds':r.integers(1,7,n),
'Preconditioned_0_1':r.integers(0,2,n),'Previous_Illness_0_1':r.integers(0,2,n),
'Daily_Temperature_Fluctuation_F':r.uniform(5,35,n).round(1),'Dust_Index_0_to_1':r.uniform(0,1,n).round(2),
'Stocking_Density_sqft_per_head':r.integers(100,250,n),'Feed_Intake_Change_0_1':r.integers(0,2,n),
'Water_Access_0_1':r.choice([0,1],n,p=[.05,.95])})
# Intentionally create some missingness to exercise uncertainty logic.
for col in ['Vaccination_Status','Transport_Hours','Arrival_Weight_lb']:
    d.loc[r.random(n)<.12,col]=np.nan
path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);d.to_csv(path,index=False)
print(f'Generated {n} synthetic rows at {path} with seed {a.seed}.')
