from pathlib import Path
import json
import pandas as pd
import streamlit as st

from importer import read_uploaded_file
from analyzer import analyze, methodology_markdown
from strategy import generate_master_strategies, strategy_markdown
from candidates import read_result_file, build_candidate_universe
from screener_auto_financials import enrich_candidate_universe
from financials import build_company_histories, merge_candidate_context
from financial_scoring import rank_financial_universe
from research_documents import ingest_uploaded_document, document_catalog
from research_agent import extract_research_evidence, build_company_research_memory
from v6_pipeline import run_v6, summary_rows as v6_summary_rows

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; REPORTS=ROOT/'reports'; DATA.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
st.set_page_config(page_title='Personal AI Stock Researcher V6.1',layout='wide')
st.title('Personal AI Stock Researcher — V6.1')
st.caption('Methodology → strategies → candidates → autonomous financial enrichment → evidence research → Bull/Bear challenge')

for k,v in {'screens':[],'analysis':None,'strategies':[],'candidate_rows':[],'candidates':[],'financial_ranked':[],'documents':[],'evidence':[],'memories':[],'v6':[]}.items(): st.session_state.setdefault(k,v)

with st.sidebar:
    st.header('Runtime')
    cdp=st.text_input('Chrome CDP URL','http://127.0.0.1:9222')
    st.info('Long-term target: fully autonomous market-data + screening gateway. CSV/XLSX remains a fallback/debug path.')

T1,T2,T3,T4,T5=st.tabs(['1 · Methodology','2 · Strategies/Candidates','3 · Financial Intelligence','4 · Research Memory','5 · Bull/Bear'])

with T1:
    st.subheader('Import trusted historical screens')
    up=st.file_uploader('Screener screens XLSX/CSV',type=['xlsx','xls','csv'],key='screens_file')
    if st.button('Analyze methodology') and up:
        screens=read_uploaded_file(up); a=analyze(screens); st.session_state.screens=screens; st.session_state.analysis=a; st.session_state.strategies=generate_master_strategies(screens,a); st.success(f'Analyzed {len(screens)} screens.')
    if st.session_state.analysis:
        a=st.session_state.analysis; c1,c2,c3=st.columns(3); c1.metric('Screens',len(st.session_state.screens)); c2.metric('Conditions',len(a['conditions'])); c3.metric('Unique parameters',len(a['parameter_frequency']))
        st.markdown(methodology_markdown(st.session_state.screens,a)[:12000])

with T2:
    if st.session_state.strategies:
        st.subheader('Master strategies')
        for s in st.session_state.strategies:
            with st.expander(f"{s['id']} · {s['name']} · methodology support {s['evidence_confidence']}/100"):
                st.code(s['hard_query']); st.write(s['purpose'])
    st.subheader('Import strategy result sets')
    sid=st.text_input('Strategy ID for this result file','S1')
    rf=st.file_uploader('Result XLSX/CSV',type=['xlsx','xls','csv'],key='result_file')
    if st.button('Add result file') and rf:
        st.session_state.candidate_rows.extend(read_result_file(rf,strategy_id=sid)); st.success('Result rows added; snapshot ratios preserved.')
    if st.button('Build candidate universe') and st.session_state.candidate_rows:
        strategies=st.session_state.strategies or [{'id':'S1','name':'Imported Strategy','evidence_confidence':50}]; st.session_state.candidates=build_candidate_universe(st.session_state.candidate_rows,strategies)
    if st.session_state.candidates:
        st.metric('Unique candidates',len(st.session_state.candidates)); st.dataframe(pd.DataFrame([{k:v for k,v in x.items() if k!='snapshot'} for x in st.session_state.candidates]),use_container_width=True)

with T3:
    st.subheader('Autonomous V3 financial enrichment')
    st.write('The app first keeps ratios already present in the strategy-result export, then optionally enriches each candidate with multi-period Screener company financials using your logged-in Chrome session.')
    use_screener=st.checkbox('Enrich from logged-in Screener company pages',value=True)
    limit=st.number_input('Max companies (0 = all)',min_value=0,value=0,step=10)
    if st.button('Run V3 automatically',type='primary'):
        if not st.session_state.candidates: st.error('Build a candidate universe first.')
        else:
            bar=st.progress(0); msg=st.empty()
            def prog(i,n,c,status): bar.progress(i/max(n,1)); msg.write(f'{i}/{n} {c} — {status}')
            rows,resolved,errors=enrich_candidate_universe(st.session_state.candidates,cdp_url=cdp,use_screener=use_screener,max_companies=int(limit),progress=prog)
            companies=build_company_histories(rows); companies=merge_candidate_context(companies,st.session_state.candidates); ranked=rank_financial_universe(companies,target_keep=min(100,len(companies))); st.session_state.financial_ranked=ranked
            st.success(f'Built financial intelligence for {len(ranked)} companies; {len(errors)} enrichment issues were retained as data gaps.')
    if st.session_state.financial_ranked:
        df=pd.DataFrame(st.session_state.financial_ranked); cols=[c for c in ['financial_rank','company','v3_priority_score','financial_score','data_confidence','funnel_decision','warnings'] if c in df.columns]; st.dataframe(df[cols],use_container_width=True)

with T4:
    st.subheader('Source-linked company research memory')
    company=st.selectbox('Company',['']+[x.get('company') for x in st.session_state.financial_ranked if x.get('company')])
    files=st.file_uploader('Optional research documents (manual fallback)',type=['pdf','txt','md','html','htm'],accept_multiple_files=True,key='docs')
    if st.button('Ingest documents') and files:
        for f in files:
            st.session_state.documents.append(ingest_uploaded_document(f,company_override=company))
        st.success(f'Documents in memory: {len(st.session_state.documents)}')
    if st.button('Build evidence/research memory') and st.session_state.documents:
        ev,errors=extract_research_evidence(st.session_state.documents,use_llm=False); st.session_state.evidence=ev; st.session_state.memories=build_company_research_memory(st.session_state.documents,ev,st.session_state.financial_ranked); st.success(f'{len(ev)} evidence items across {len(st.session_state.memories)} companies.')
    if st.session_state.memories:
        st.dataframe(pd.DataFrame([{k:v for k,v in m.items() if k not in {'evidence','risks','catalysts','management_claim_evidence','financial_context'}} for m in st.session_state.memories]),use_container_width=True)

with T5:
    st.subheader('V6 independent Bull/Bear challenge')
    st.warning('Research-state analysis only — not a buy/sell recommendation or expected-return probability.')
    if st.button('Run adversarial research'):
        if not st.session_state.memories: st.error('Build company research memory first.')
        else: st.session_state.v6=run_v6(st.session_state.memories); st.success(f'Analyzed {len(st.session_state.v6)} companies.')
    if st.session_state.v6: st.dataframe(pd.DataFrame(v6_summary_rows(st.session_state.v6)),use_container_width=True)

st.divider(); st.caption('See README.md and docs/ for architecture, setup, autonomy, current status and roadmap.')
