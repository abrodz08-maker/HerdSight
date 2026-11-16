"""HerdSight: educational BRD decision aid. All forward scenarios are assumptions, not clinical predictions."""
from pathlib import Path
from datetime import date
from io import BytesIO
import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).resolve().parent
DATA = BASE / 'BRD_synthetic_10000_cattle.xlsx'
FACTORS = {
    'Arrival_Weight_lb': (10, lambda x: 10 if x < 500 else 5 if x < 650 else 0),
    'Age_Months': (5, lambda x: 5 if x < 9 else 0),
    'Transport_Hours': (9, lambda x: 9 if x >= 10 else 5 if x >= 6 else 0),
    'Vaccination_Status': (9, lambda x: 9 if str(x).lower().strip() in ['none','no','unvaccinated','0'] else 4 if str(x).lower().strip() in ['partial','partially vaccinated'] else 0),
    'Commingled_0_1': (7, lambda x: 7 if float(x) == 1 else 0),
    'Number_of_Source_Herds': (4, lambda x: 4 if x >= 4 else 0),
    'Preconditioned_0_1': (5, lambda x: 5 if float(x) == 0 else 0),
    'Previous_Illness_0_1': (7, lambda x: 7 if float(x) == 1 else 0),
    'Daily_Temperature_Fluctuation_F': (5, lambda x: 5 if x >= 25 else 0),
    'Dust_Index_0_to_1': (5, lambda x: 5 if x >= .65 else 0),
    'Stocking_Density_sqft_per_head': (4, lambda x: 4 if x < 150 else 0),
}
OPTIONAL = {
    'Feed_Intake_Change_0_1': (5, lambda x: 5 if float(x) == 1 else 0),
    'Water_Access_0_1': (4, lambda x: 4 if float(x) == 0 else 0),
}
REQUIRED = ['Animal_ID','Feedlot_ID']
VALID_VACC = {'none','no','unvaccinated','0','partial','partially vaccinated','full','fully vaccinated','complete','yes','1'}


def score_row(row):
    """Return lower/upper scores; missing inputs cannot silently imply low risk."""
    low, upper, missing, drivers = 12.0, 12.0, [], []
    for key, (maximum, rule) in {**FACTORS, **{k:v for k,v in OPTIONAL.items() if k in row.index}}.items():
        value = row.get(key, np.nan)
        absent = pd.isna(value) or (isinstance(value, str) and not value.strip())
        if key == 'Vaccination_Status' and not absent:
            absent = str(value).strip().lower() not in VALID_VACC
        if not absent:
            try:
                points = rule(value)
            except (ValueError, TypeError):
                absent = True
        if absent:
            missing.append(key)
            upper += maximum
        else:
            low += points
            upper += points
            if points:
                drivers.append(f'{key}: +{points}')
    low, upper = min(85, low), min(85, upper)
    complete = (len(FACTORS) - sum(k in FACTORS for k in missing)) / len(FACTORS)
    status = 'Insufficient information' if complete < .6 else 'Review missing inputs' if complete < .9 else 'Core inputs complete'
    return pd.Series({'Risk_Lower':low,'Risk_Upper':upper,'Completeness':round(complete*100,1),
                      'Assessment':status,'Missing_Inputs':', '.join(missing), 'Risk_Drivers':', '.join(drivers),
                      'Priority':'Data review' if status == 'Insufficient information' else 'High' if upper >= 35 else 'Moderate' if upper >= 20 else 'Low'})


def prepare(df):
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    for col in REQUIRED:
        if col not in df:
            raise ValueError(f'Missing required column: {col}. Download the template or add this column.')
    df['Animal_ID'] = df['Animal_ID'].astype('string')
    df['Feedlot_ID'] = df['Feedlot_ID'].astype('string')
    if df['Animal_ID'].isna().any() or df['Feedlot_ID'].isna().any():
        raise ValueError('Animal_ID and Feedlot_ID cannot be blank.')
    for col in [k for k in FACTORS if k != 'Vaccination_Status'] + list(OPTIONAL):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'Days_Since_Arrival' in df:
        df['Days_Since_Arrival'] = pd.to_numeric(df['Days_Since_Arrival'], errors='coerce')
    elif 'Arrival_Date' in df:
        dates = pd.to_datetime(df['Arrival_Date'], errors='coerce')
        # Arrival date is historical; elapsed days are relative to analysis date, not simulated 45-day outcome timing.
        df['Days_Since_Arrival'] = (pd.Timestamp(date.today()) - dates).dt.days
    else:
        df['Days_Since_Arrival'] = np.nan
    df['Within_45_Days_Today'] = df['Days_Since_Arrival'].between(0,45)
    scores = df.apply(score_row,axis=1)
    return pd.concat([df,scores],axis=1)


def scenario(n, high, baseline, reduction, additional_per_head, cost_treat, cost_perf, mortality_rate, death_cost,
             treat_fraction, prophylactic_fraction, checks_per_head, review_fraction, space_fraction,
             days, monitor_capacity, vet_capacity, space_capacity, existing_checks, existing_vet, existing_space):
    cases = n * baseline / 100 * (1-reduction/100)
    deaths = cases * mortality_rate/100
    clinical_courses = cases * treat_fraction/100
    preventive_courses = n * prophylactic_fraction/100
    courses = clinical_courses + preventive_courses
    daily_checks = existing_checks + high * checks_per_head / days
    daily_vet = existing_vet + high * review_fraction/100 / days
    spaces = existing_space + high * space_fraction/100
    feasible = daily_checks <= monitor_capacity and daily_vet <= vet_capacity and spaces <= space_capacity
    health_cost = cases*(cost_treat+cost_perf)+deaths*death_cost
    program_cost = n*additional_per_head
    return dict(Cases=cases, Deaths=deaths, Clinical_Courses=clinical_courses, Preventive_Courses=preventive_courses,
                Antimicrobial_Courses=courses, Health_Cost=health_cost, Program_Cost=program_cost,
                Total_Cost=health_cost+program_cost, Daily_Checks=daily_checks, Daily_Vet_Reviews=daily_vet,
                Spaces=spaces, Feasible=feasible)


def csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

st.set_page_config(page_title='HerdSight | Decision Intelligence',page_icon='🐄',layout='wide')
st.markdown('''<style>
.stApp{background:#f5f8f7}.block-container{max-width:1450px;padding-top:1.8rem}
[data-testid="stSidebar"]{background:white}h1,h2,h3{color:#17384a}
[data-testid="stMetric"]{background:white;padding:16px;border:1px solid #dfe9e4;border-radius:14px}
.hero{background:linear-gradient(110deg,#fff,#e2f4e9);padding:32px;border-radius:18px;border:1px solid #d6e9dd;margin:14px 0 24px}
.brand{font-size:34px;font-weight:850;letter-spacing:-1px;color:#17384a}.brand span{color:#148466}
.note{font-size:13px;color:#54706c}.stTabs [data-baseweb="tab-list"]{gap:8px}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="brand">HERD<span>SIGHT</span></div><div class="note">LIVESTOCK HEALTH INTELLIGENCE · RESEARCH PROTOTYPE</div>',unsafe_allow_html=True)

with st.sidebar:
    st.header('HerdSight Workspace')
    upload = st.file_uploader('Upload CSV or XLSX',type=['csv','xlsx'])
    if upload:
        try:
            raw = pd.read_csv(upload) if upload.name.lower().endswith('.csv') else pd.read_excel(upload)
        except Exception as e:
            st.error(f'Could not read file: {e}');st.stop()
    elif DATA.exists():
        raw = pd.read_excel(DATA,sheet_name='Cattle_Records')
        st.caption('Using synthetic 10,000-cattle demonstration data.')
    else:
        st.error('Demo file not found; upload a CSV or XLSX.');st.stop()
    try:
        df = prepare(raw)
    except Exception as e:
        st.error(str(e));st.stop()
    if df.empty:
        st.error('Dataset is empty.');st.stop()
    yards = sorted(df['Feedlot_ID'].dropna().unique().tolist())
    selected = st.multiselect('Feedlots',yards,default=yards)
    cohort = df[df['Feedlot_ID'].isin(selected)].copy()
    st.caption(f'{len(cohort):,} selected animals')
    st.divider()
    st.subheader('45-day decision cohort')
    cohort_mode = st.radio('Analysis population', ['All selected arrivals (45-day outcome per arrival)','Currently within days 0–45'],index=0)
    if cohort_mode.startswith('Currently'):
        cohort = cohort[cohort['Within_45_Days_Today']].copy()
        if cohort.empty:
            st.warning('No animals currently in days 0–45. Historic synthetic arrivals may be outside this window.')
    st.caption('All selected arrivals: each animal has its own 45-day post-arrival outcome window. Currently within: requires elapsed arrival days.')
    st.divider()
    st.subheader('Scenario assumptions')
    baseline = st.number_input('Assumed 45-day BRD incidence (%)',0.,100.,20.,1.)
    treat_cost = st.number_input('Treatment expense per case ($)',0.,10000.,110.,10.)
    perf_cost = st.number_input('Lost performance per case ($)',0.,10000.,90.,10.)
    death_rate = st.slider('Fatality among BRD cases (%)',0.,30.,5.,1.)
    death_cost = st.number_input('Loss per death ($)',0.,10000.,1600.,100.)
    treat_fraction = st.slider('BRD cases treated with antimicrobial (%)',0.,100.,90.,5.)
    st.divider()
    st.subheader('Binding capacity')
    staff = st.number_input('Monitoring staff',1,200,4)
    checks_staff = st.number_input('Checks per staff per day',1,500,40)
    monitor_capacity = staff*checks_staff
    vet_capacity = st.number_input('Vet reviews per day',0,500,35)
    space_capacity = st.number_input('Observation spaces',0,1000,60)
    days = st.number_input('Planning days',1,45,5)
    existing_checks = st.number_input('Current daily monitoring checks',0,10000,40)
    existing_vet = st.number_input('Current daily vet reviews',0,1000,8)
    existing_space = st.number_input('Currently occupied observation spaces',0,1000,15)

n = len(cohort)
high = cohort[cohort['Priority'].eq('High')]
review = cohort[cohort['Priority'].eq('Data review')]
# Data-review animals are never silently placed in the low-risk queue.
priority = cohort.assign(_order=cohort['Priority'].map({'Data review':0,'High':1,'Moderate':2,'Low':3})).sort_values(['_order','Risk_Upper'],ascending=[True,False]).drop(columns='_order')

tabs = st.tabs(['Overview','Cattle Records','Risk & Missing Data','Management & Constraints','Strategy Comparison','Economics & Antimicrobials','Decision Summary','Evidence & Evaluation','Team'])
with tabs[0]:
    st.markdown('<div class="hero"><div style="font-size:12px;font-weight:800;color:#148466">POST-ARRIVAL HEALTH DECISIONS</div><h1>Your herd. Your priorities.</h1><p>Prioritize review, compare feasible management options, and make health–cost–antimicrobial trade-offs visible.</p></div>',unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    a.metric('Selected cattle',f'{n:,}');b.metric('High-priority',f'{len(high):,}');c.metric('Needs data review',f'{len(review):,}');d.metric('Mean upper score',f'{cohort.Risk_Upper.mean():.1f}' if n else '—')
    st.info('Risk scores are illustrative rankings, not calibrated BRD probabilities. Data-review animals are placed first in the review queue.')
    if n:
        left,right=st.columns(2)
        with left:
            counts=cohort['Priority'].value_counts().reset_index();counts.columns=['Priority','Cattle']
            st.plotly_chart(px.pie(counts,names='Priority',values='Cattle',hole=.55,title='Priority distribution'),use_container_width=True)
        with right:
            yard=cohort.groupby('Feedlot_ID',as_index=False).agg(Mean_Upper=('Risk_Upper','mean'),Cattle=('Animal_ID','size'))
            st.plotly_chart(px.bar(yard,x='Feedlot_ID',y='Mean_Upper',hover_data=['Cattle'],title='Average upper risk score by feedlot'),use_container_width=True)
        st.subheader('First animals for review')
        st.dataframe(priority[['Animal_ID','Feedlot_ID','Risk_Lower','Risk_Upper','Completeness','Priority']].head(20),hide_index=True,use_container_width=True)

with tabs[1]:
    st.header('Cattle Records')
    search=st.text_input('Find Animal ID')
    view=cohort[cohort['Animal_ID'].str.contains(search,case=False,na=False,regex=False)] if search else cohort
    cols=[c for c in ['Animal_ID','Feedlot_ID','Arrival_Date','Days_Since_Arrival','Arrival_Weight_lb','Vaccination_Status','Transport_Hours','Risk_Lower','Risk_Upper','Completeness','Priority'] if c in view]
    st.dataframe(view[cols],use_container_width=True,hide_index=True,height=440)
    st.download_button('Download selected records',csv_bytes(view),'HerdSight_records.csv','text/csv')
    template=pd.DataFrame(columns=['Animal_ID','Feedlot_ID','Arrival_Date']+list(FACTORS)+list(OPTIONAL))
    st.download_button('Download upload template',csv_bytes(template),'HerdSight_upload_template.csv','text/csv')
    st.caption('Animal_ID and Feedlot_ID are required; other inputs may be missing and will be flagged. No private cattle data are needed for the demonstration.')

with tabs[2]:
    st.header('Risk and Missing-Data Review')
    st.write('Unknown risk factors contribute to the upper bound, not a falsely reassuring low score. The interval is a rule-based sensitivity bound, **not** a statistical confidence interval.')
    if n:
        chosen=st.selectbox('Animal',cohort['Animal_ID'].astype(str).tolist())
        animal=cohort.loc[cohort['Animal_ID'].astype(str).eq(chosen)].iloc[0]
        a,b,c=st.columns(3)
        a.metric('Score interval',f'{animal.Risk_Lower:.0f}–{animal.Risk_Upper:.0f}');b.metric('Core data present',f'{animal.Completeness:.0f}%');c.metric('Queue',animal.Priority)
        st.write('**Known contributing factors:**',animal.Risk_Drivers or 'None detected')
        st.write('**Missing or invalid fields:**',animal.Missing_Inputs or 'None')
        if animal.Assessment=='Insufficient information':st.error('Insufficient information: collect missing inputs; do not interpret this score as low risk.')
        elif animal.Assessment=='Review missing inputs':st.warning('Review missing inputs before relying on this priority.')
        else:st.success('Core input fields present. Model validity is still unproven.')
        if pd.isna(animal.Days_Since_Arrival):st.warning('Cannot determine current day since arrival.')
        else:st.caption(f'Days since arrival: {animal.Days_Since_Arrival:.0f}. Currently in 0–45 day window: {bool(animal.Within_45_Days_Today)}')
        st.download_button('Download review queue',csv_bytes(priority[['Animal_ID','Feedlot_ID','Priority','Risk_Lower','Risk_Upper','Completeness','Missing_Inputs']]),'HerdSight_review_queue.csv','text/csv')

with tabs[3]:
    st.header('Management and Capacity')
    st.write('Baseline operations already consume monitoring, veterinary and observation resources. Enter those baseline commitments in the sidebar.')
    a,b,c=st.columns(3)
    a.metric('Daily monitoring capacity',monitor_capacity);b.metric('Daily vet capacity',vet_capacity);c.metric('Observation spaces',space_capacity)
    st.write(f'Baseline utilization: **{existing_checks}** monitoring checks/day, **{existing_vet}** vet reviews/day, **{existing_space}** observation spaces.')
    if existing_checks>monitor_capacity or existing_vet>vet_capacity or existing_space>space_capacity:st.error('Current operations already exceed at least one entered capacity. Reassess staffing and clinical access immediately.')
    st.subheader('Prioritized review queue')
    st.dataframe(priority[['Animal_ID','Feedlot_ID','Priority','Risk_Upper','Missing_Inputs']].head(100),hide_index=True,use_container_width=True)
    st.warning('The queue is for planning only. Signs of illness or urgent welfare concerns override any score, ranking or capacity assumption. Veterinary review determines care and medication.')

with tabs[4]:
    st.header('Compare Management Strategies')
    st.caption('Change assumed intervention effects and resources. Values are hypotheses, not measured treatment efficacy.')
    specs=[('Current operations',0.,0.,0.,0.,0.,0.),('Targeted monitoring',10.,5.,1.,25.,10.,0.),('Enhanced husbandry',18.,12.,2.,40.,20.,0.)]
    results=[]
    with st.expander('Edit each strategy assumption',expanded=True):
        for name,red,cost,checks,vet,spaces,preventive in specs:
            st.markdown(f'**{name}**')
            if name=='Current operations':
                st.caption('Reference case: existing monitoring, vet workload, occupied spaces and assumed disease incidence. No incremental program cost.')
            else:
                c1,c2,c3=st.columns(3)
                red=c1.slider(f'Assumed case reduction (%) · {name}',0.,50.,red,1.,key=f'red{name}')
                cost=c2.number_input(f'Extra $/head · {name}',0.,1000.,cost,1.,key=f'cost{name}')
                checks=c3.number_input(f'Extra checks/high-priority animal · {name}',0.,20.,checks,1.,key=f'checks{name}')
                c4,c5,c6=st.columns(3)
                vet=c4.slider(f'Extra vet reviews (% high-priority) · {name}',0.,100.,vet,5.,key=f'vet{name}')
                spaces=c5.slider(f'Extra observation spaces (% high-priority) · {name}',0.,100.,spaces,5.,key=f'space{name}')
                preventive=c6.slider(f'Additional preventive antimicrobial courses (% all cattle) · {name}',0.,100.,preventive,5.,key=f'prevent{name}')
            vals=scenario(n,len(high)+len(review),baseline,red,cost,treat_cost,perf_cost,death_rate,death_cost,treat_fraction,preventive,checks,vet,spaces,days,monitor_capacity,vet_capacity,space_capacity,existing_checks,existing_vet,existing_space)
            results.append({'Strategy':name,**vals,'Reduction_Assumption_pct':red,'Incremental_Cost_per_Head':cost})
    comp=pd.DataFrame(results)
    baseline_cost=comp.iloc[0]['Total_Cost'];baseline_courses=comp.iloc[0]['Antimicrobial_Courses']
    comp['Savings_vs_Current']=baseline_cost-comp['Total_Cost']
    comp['Course_Change_vs_Current']=comp['Antimicrobial_Courses']-baseline_courses
    st.session_state['comparison']=comp
    st.subheader('Health, costs, antimicrobial use and feasibility')
    st.dataframe(comp[['Strategy','Cases','Deaths','Antimicrobial_Courses','Course_Change_vs_Current','Total_Cost','Savings_vs_Current','Daily_Checks','Daily_Vet_Reviews','Spaces','Feasible']].round(1),hide_index=True,use_container_width=True)
    c1,c2=st.columns(2)
    with c1:st.plotly_chart(px.bar(comp,x='Strategy',y='Total_Cost',title='Projected total cost (assumptions)'),use_container_width=True)
    with c2:st.plotly_chart(px.bar(comp,x='Strategy',y='Cases',title='Projected 45-day BRD cases (assumptions)'),use_container_width=True)
    if (~comp['Feasible']).any():st.warning('One or more strategies exceed entered resource capacity. Compare the three demand columns against available capacity.')
    st.info('No automatic “cheapest = best” recommendation. Managers must weigh animal welfare, clinical access, cost and antimicrobial stewardship; treatment is never withheld to meet targets.')
    st.download_button('Download comparison',csv_bytes(comp),'HerdSight_strategy_comparison.csv','text/csv')

# Compute same default strategy values on tabs other than comparison (Streamlit executes all tab bodies).
with tabs[5]:
    st.header('Economics and Antimicrobial Stewardship')
    st.write('Disease costs include treatment expense, lost performance, and a separate mortality loss. All values are user-adjustable assumptions.')
    st.dataframe(comp[['Strategy','Health_Cost','Program_Cost','Total_Cost','Deaths','Clinical_Courses','Preventive_Courses','Antimicrobial_Courses']].round(1),hide_index=True,use_container_width=True)
    st.plotly_chart(px.bar(comp,x='Strategy',y=['Clinical_Courses','Preventive_Courses'],barmode='stack',title='Estimated antimicrobial courses by purpose'),use_container_width=True)
    st.warning('Courses are not doses, days of therapy, appropriateness, or proof of improved stewardship. Preventive antimicrobial exposure is an assumption, not a recommendation. A veterinarian must determine whether any antimicrobial is indicated.')

with tabs[6]:
    st.header('Downloadable Decision Summary')
    choice=st.selectbox('Strategy for decision summary',comp['Strategy'].tolist())
    item=comp.loc[comp.Strategy.eq(choice)].iloc[0]
    note=st.text_area('Manager rationale / veterinary review notes','Review incomplete records and prioritize clinically symptomatic animals regardless of queue rank.')
    summary={
        'prototype':'HerdSight','analysis_date':str(date.today()),'feedlots':selected,'cohort_definition':cohort_mode,
        'cattle':n,'high_priority':len(high),'needs_data_review':len(review),'strategy':choice,
        'baseline_45_day_incidence_assumption_pct':baseline,'treatment_cost_per_case':treat_cost,
        'performance_loss_per_case':perf_cost,'case_fatality_assumption_pct':death_rate,'loss_per_death':death_cost,
        'treatment_fraction_assumption_pct':treat_fraction,'monitoring_capacity_per_day':monitor_capacity,
        'vet_capacity_per_day':vet_capacity,'observation_capacity':space_capacity,
        'baseline_checks_per_day':existing_checks,'baseline_vet_reviews_per_day':existing_vet,
        'baseline_spaces_occupied':existing_space,'planning_days':days,
        'scenario':{k:(bool(v) if isinstance(v,(np.bool_,bool)) else float(v) if isinstance(v,(np.integer,np.floating,int,float)) else str(v)) for k,v in item.to_dict().items()},
        'manager_notes':note,'warning':'All projections are hypothetical. No clinical validation. Medication requires veterinary oversight.'
    }
    st.json(summary,expanded=False)
    if not item.Feasible:st.error('Selected plan exceeds at least one operational capacity. Do not treat it as feasible.')
    if len(review):st.warning(f'{len(review)} animals require missing-data review. They are not classified as low risk.')
    st.download_button('Download decision summary (JSON)',json.dumps(summary,indent=2).encode(),'HerdSight_decision_summary.json','application/json')
    lines=[f'HERDSIGHT MANAGEMENT DECISION SUMMARY — {date.today()}',f'Feedlots: {", ".join(selected)}',f'Cohort: {cohort_mode}',f'Animals: {n}; high priority: {len(high)}; data review: {len(review)}',f'Selected strategy: {choice}',f'Feasible under entered capacities: {bool(item.Feasible)}',f'45-day BRD cases (assumed): {item.Cases:.1f}',f'Deaths (assumed): {item.Deaths:.1f}',f'Antimicrobial courses (assumed): {item.Antimicrobial_Courses:.1f}',f'Total costs (assumed): ${item.Total_Cost:,.0f}',f'Net savings vs current: ${item.Savings_vs_Current:,.0f}',f'Daily monitoring demand: {item.Daily_Checks:.1f}/{monitor_capacity}',f'Daily vet demand: {item.Daily_Vet_Reviews:.1f}/{vet_capacity}',f'Observation spaces: {item.Spaces:.1f}/{space_capacity}',f'Manager notes: {note}','ASSUMPTIONS, NOT CLINICAL PREDICTIONS. Veterinary oversight required.']
    st.download_button('Download printable summary (TXT)','\n'.join(lines).encode(),'HerdSight_decision_summary.txt','text/plain')
    st.caption('For a complete end-to-end demonstration, see DEMONSTRATION_CASE.md in the GitHub repository.')with tabs[7]:
    st.header('Evidence, Evaluation & Limitations')
    st.write('**Decision unit:** individual cattle for review; feedlot-level comparisons for resource allocation. **User:** feedlot manager working with a veterinarian. **Timing:** at arrival and during days 0–45 as data become available.')
    st.write('**Data:** synthetic, not observations. Existing outcome fields are simulated 45-day labels; never use these post-outcome labels as arrival-time risk inputs. Synthetic generation provenance of the supplied original workbook is not independently reproducible from the files available.')
    st.write('**Model:** additive expert-inspired rules; lower/upper bounds represent missing-factor sensitivity. They are not calibrated disease probabilities, confidence intervals or clinical evidence.')
    if 'BRD_Within_45_Days_0_1' in cohort and n:
        observed=pd.to_numeric(cohort['BRD_Within_45_Days_0_1'],errors='coerce')
        valid=observed.notna()
        if valid.any():
            st.metric('Simulated 45-day BRD incidence in selected data',f'{observed[valid].mean()*100:.1f}%')
            st.caption('Descriptive check of synthetic labels, not external validation. Scenario baseline incidence remains an independently adjustable assumption.')
            temp=cohort.loc[valid,['Priority']].copy();temp['Simulated_BRD']=observed[valid].values
            st.dataframe(temp.groupby('Priority',as_index=False).agg(Count=('Simulated_BRD','size'),Synthetic_Incidence=('Simulated_BRD','mean')),hide_index=True,use_container_width=True)
    st.subheader('Decision limitations')
    st.markdown('- Intervention effects are hypothetical; not estimated from randomized or observational causal evidence.\n- Capacity checks are aggregated and do not schedule actual pen moves or urgent clinical cases.\n- The selected 45-day outcome cohort is defined per arrival, not by the current calendar date.\n- Missing-input upper bounds are heuristic worst-case increments, not statistical uncertainty.\n- Antimicrobial use is measured as assumed courses only, not appropriateness or resistance.\n- The original dataset generation script was not provided; a separate reproducible sample generator is included.\n- Model inputs do not include outcome columns, avoiding target leakage.')
    st.subheader('References and responsible use')
st.markdown('Merck Veterinary Manual, *Overview of Bovine Respiratory Disease Complex*; Merck Animal Health, *BRD FAQs* and *Advancing your BRD outcomes*. Full links and disclosure in SOURCES_AND_DISCLOSURE.md in the GitHub repository.')    st.warning('Research prototype only. No diagnosis, drug selection, dosage or treatment denial. Clinical decisions require a veterinarian.')

with tabs[8]:
    st.header('The HerdSight Team')
    st.write('**Kyler Ko · Abraham Rodriguez · Nishant Buchi**')
    st.write('AISFS × Merck Animal Health Interdisciplinary Hackathon 2026')
    st.caption('Independent student research prototype; not an official Merck Animal Health product.')

st.divider()
st.caption('HerdSight · Synthetic-data research prototype · Illustrative outcomes and costs · Veterinary oversight required')
