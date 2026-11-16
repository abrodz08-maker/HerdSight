import unittest
from pathlib import Path
from datetime import date
import ast
import numpy as np
import pandas as pd

APP = Path(__file__).resolve().parents[1] / 'app.py'
TREE = ast.parse(APP.read_text(encoding='utf-8'))
KEEP = {'FACTORS','OPTIONAL','REQUIRED','VALID_VACC'}
BODY = [node for node in TREE.body if (isinstance(node, ast.FunctionDef) and node.name in {'score_row','prepare','scenario'}) or (isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id in KEEP for t in node.targets))]
NS = {'np':np,'pd':pd,'date':date}
exec(compile(ast.Module(body=BODY,type_ignores=[]),str(APP),'exec'),NS)

class HerdSightTests(unittest.TestCase):
    def test_complete_low_score(self):
        row={'Arrival_Weight_lb':800,'Age_Months':14,'Transport_Hours':2,'Vaccination_Status':'Full','Commingled_0_1':0,'Number_of_Source_Herds':1,'Preconditioned_0_1':1,'Previous_Illness_0_1':0,'Daily_Temperature_Fluctuation_F':10,'Dust_Index_0_to_1':.2,'Stocking_Density_sqft_per_head':220}
        out=NS['score_row'](pd.Series(row))
        self.assertEqual(out['Risk_Lower'],12)
        self.assertEqual(out['Risk_Upper'],12)
        self.assertEqual(out['Completeness'],100)
    def test_missing_does_not_look_low(self):
        row=pd.Series({'Animal_ID':'A','Feedlot_ID':'Y'})
        out=NS['score_row'](row)
        self.assertEqual(out['Priority'],'Data review')
        self.assertGreater(out['Risk_Upper'],out['Risk_Lower'])
        self.assertEqual(out['Completeness'],0)
    def test_invalid_vaccine_flagged(self):
        out=NS['score_row'](pd.Series({'Vaccination_Status':'??'}))
        self.assertIn('Vaccination_Status',out['Missing_Inputs'])
    def test_baseline_consumes_resources(self):
        v=NS['scenario'](100,20,20,0,0,110,90,5,1600,90,0,0,0,0,5,160,35,60,40,8,15)
        self.assertEqual(v['Daily_Checks'],40)
        self.assertEqual(v['Daily_Vet_Reviews'],8)
        self.assertEqual(v['Spaces'],15)
        self.assertEqual(v['Cases'],20)
        self.assertEqual(v['Total_Cost'],5600)
    def test_capacity_can_bind(self):
        v=NS['scenario'](100,80,20,10,5,110,90,5,1600,90,0,2,100,100,5,30,10,20,20,8,15)
        self.assertFalse(v['Feasible'])
    def test_original_dataset(self):
        p=APP.parent/'data'/'BRD_synthetic_10000_cattle.xlsx'
        d=NS['prepare'](pd.read_excel(p,sheet_name='Cattle_Records'))
        self.assertEqual(len(d),10000)
        self.assertEqual(d['Feedlot_ID'].nunique(),4)
    def test_missing_dataset(self):
        d=NS['prepare'](pd.read_csv(APP.parent/'data'/'missing_data_test.csv'))
        self.assertGreater((d.Priority=='Data review').sum(),0)
        self.assertTrue((d.Risk_Upper>=d.Risk_Lower).all())

if __name__=='__main__': unittest.main()
