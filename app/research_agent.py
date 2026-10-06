from __future__ import annotations
import json, os, re, requests
from collections import Counter, defaultdict

RESEARCH_THEMES={"business_model":["business model","revenue","segment","customer","product","service","market share","order book"],"management":["management","promoter","board","capital allocation","guidance","strategy","related party"],"growth":["capacity","expansion","capex","growth","new product","new plant","order inflow","demand"],"risk":["risk","litigation","competition","concentration","regulatory","raw material","forex","working capital","debt","contingent"],"cash_flow":["cash flow","working capital","receivable","inventory","free cash flow","operating cash"],"governance":["related party","pledge","auditor","resignation","fraud","investigation","qualified opinion","corporate governance"],"catalyst":["commissioning","launch","approval","order","capacity expansion","acquisition","new facility","commercial production"]}

def _norm(t): return re.sub(r"\s+"," ",str(t or "")).strip()
def _sentences(t): return [_norm(x) for x in re.split(r"(?<=[.!?])\s+|\n+",str(t or "")) if len(_norm(x))>=35]
def _theme(s):
    low=s.lower(); scores={k:sum(1 for w in words if w in low) for k,words in RESEARCH_THEMES.items()}; scores={k:v for k,v in scores.items() if v}; return max(scores,key=scores.get) if scores else None

def deterministic_extract(document,max_evidence_per_theme=8):
    out=[]; counts=Counter()
    for ci,ch in enumerate(document.get("chunks",[])):
        for s in _sentences(ch.get("text","")):
            theme=_theme(s)
            if not theme or counts[theme]>=max_evidence_per_theme: continue
            counts[theme]+=1; kind="risk" if theme in {"risk","governance"} else "catalyst" if theme=="catalyst" else "source_excerpt"
            out.append({"evidence_id":f"{document['document_id']}-{ci}-{counts[theme]}","company":document.get("company",""),"document_id":document.get("document_id"),"document_title":document.get("title") or document.get("filename"),"document_type":document.get("doc_type"),"document_date":document.get("document_date"),"page":ch.get("page"),"theme":theme,"kind":kind,"claim":"","excerpt":s[:900],"confidence":"source_excerpt","status":"unreviewed","source_kind":document.get("source_kind","uploaded")})
    return out

def llm_configured(): return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))
def _post(messages):
    base=os.getenv("LLM_BASE_URL","").rstrip("/"); r=requests.post(base+"/chat/completions",headers={"Authorization":f"Bearer {os.getenv('LLM_API_KEY')}","Content-Type":"application/json"},json={"model":os.getenv("LLM_MODEL"),"messages":messages,"temperature":0,"response_format":{"type":"json_object"}},timeout=240); r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])
def llm_extract_document(document):
    if not llm_configured(): return {"ok":False,"error":"LLM not configured","evidence":[]}
    source="\n\n".join(f"[PAGE {c.get('page') or 'NA'}]\n{c.get('text','')[:4500]}" for c in document.get("chunks",[])[:60]); data=_post([{"role":"system","content":"Evidence-bound equity research extractor. Never invent missing facts."},{"role":"user","content":f"Company:{document.get('company')}\nExtract supported evidence as JSON evidence[] with theme,kind,claim,page,excerpt,confidence.\nSOURCE:\n{source}"}]); out=[]
    for i,x in enumerate(data.get("evidence",[]),1): out.append({"evidence_id":f"{document['document_id']}-llm-{i}","company":document.get("company",""),"document_id":document.get("document_id"),"document_title":document.get("title") or document.get("filename"),"document_type":document.get("doc_type"),"document_date":document.get("document_date"),"page":x.get("page"),"theme":x.get("theme","other"),"kind":x.get("kind","FACT"),"claim":_norm(x.get("claim","")),"excerpt":_norm(x.get("excerpt",""))[:900],"confidence":x.get("confidence","medium"),"status":"machine_extracted","source_kind":document.get("source_kind","uploaded")})
    return {"ok":True,"evidence":out}
def extract_research_evidence(documents,use_llm=False):
    out=[]; errors=[]
    for d in documents:
        if use_llm and llm_configured():
            try:
                r=llm_extract_document(d)
                if r.get("ok"): out.extend(r.get("evidence",[])); continue
            except Exception as e: errors.append({"document_id":d.get("document_id"),"error":str(e)})
        out.extend(deterministic_extract(d))
    return out,errors

def _quality(items):
    if not items:return 0.0
    primary={"annual_report","quarterly_result","investor_presentation","exchange_filing","credit_rating","earnings_call"}; distinct=len({x.get("document_id") for x in items if x.get("document_id")}); p=sum(1 for x in items if x.get("document_type") in primary)/len(items); dated=sum(1 for x in items if x.get("document_date"))/len(items); paged=sum(1 for x in items if x.get("page"))/len(items); return round(min(100,min(1,distinct/6)*40+p*25+dated*15+paged*20),1)
def build_company_research_memory(documents,evidence,financial_ranked=None):
    fin={str(x.get("company","")).strip().casefold():x for x in (financial_ranked or []) if x.get("company")}; docs=defaultdict(list); ev=defaultdict(list)
    for d in documents: docs[str(d.get("company","")).strip().casefold()].append(d)
    for e in evidence: ev[str(e.get("company","")).strip().casefold()].append(e)
    out=[]
    for key in sorted(set(docs)|set(ev)|set(fin)):
        ds=docs[key]; items=ev[key]; f=fin.get(key,{}); company=(ds[0].get("company") if ds else None) or (items[0].get("company") if items else None) or f.get("company") or key; types={d.get("doc_type") for d in ds if d.get("doc_type")}; q=_quality(items); required={"annual_report","quarterly_result","investor_presentation","earnings_call","exchange_filing","credit_rating"}; coverage=round(len(types&required)/len(required)*100,1); themes=Counter(x.get("theme","other") for x in items); risks=[x for x in items if x.get("theme") in {"risk","governance"} or x.get("kind") in {"RISK","GOVERNANCE"}]; cats=[x for x in items if x.get("theme")=="catalyst" or x.get("kind")=="CATALYST"]; claims=[x for x in items if x.get("kind") in {"MANAGEMENT_CLAIM","OUTLOOK"}]; fc={"financial_rank":f.get("financial_rank"),"v3_priority_score":f.get("v3_priority_score"),"financial_score":f.get("financial_score"),"data_confidence":f.get("data_confidence"),"v3_funnel_decision":f.get("funnel_decision"),"strategy_count":f.get("strategy_count"),"strategies":f.get("strategies",[]),"financial_warnings":f.get("warnings",[])}; out.append({"company":company,"documents":len(ds),"document_types":sorted(types),"document_coverage":coverage,"evidence_items":len(items),"evidence_quality":q,"themes":dict(themes),"risk_items":len(risks),"catalyst_items":len(cats),"management_claims":len(claims),"research_readiness":round(.55*q+.45*coverage,1),"financial_context":fc,"evidence":items,"risks":risks,"catalysts":cats,"management_claim_evidence":claims})
    return sorted(out,key=lambda x:x.get("research_readiness",0),reverse=True)
def build_promise_delivery_ledger(memory): return [{"company":memory.get("company"),"promise":e.get("claim") or e.get("excerpt"),"promised_on":e.get("document_date"),"source_document":e.get("document_title"),"page":e.get("page"),"delivery_status":"UNRESOLVED","delivery_evidence":""} for e in memory.get("management_claim_evidence",[])]
def research_report(memories): return "# V4 Company Research Agent Report\n\n"+f"- Companies in research memory: **{len(memories)}**\n- Total source-linked evidence items: **{sum(m.get('evidence_items',0) for m in memories)}**\n"
