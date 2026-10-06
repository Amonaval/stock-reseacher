from __future__ import annotations
import json,os,requests
from datetime import datetime,timezone

def configured(): return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))
def _post_json(messages):
    base=os.getenv("LLM_BASE_URL","").rstrip("/"); payload={"model":os.getenv("LLM_MODEL"),"messages":messages,"temperature":0.0,"response_format":{"type":"json_object"}}; r=requests.post(base+"/chat/completions",headers={"Authorization":f"Bearer {os.getenv('LLM_API_KEY')}","Content-Type":"application/json"},json=payload,timeout=300); r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])
def _evidence(memory,limit=220): return [{"evidence_id":e.get("evidence_id"),"document":e.get("document_title"),"document_type":e.get("document_type"),"date":e.get("document_date"),"page":e.get("page"),"theme":e.get("theme"),"kind":e.get("kind"),"claim":e.get("claim"),"excerpt":e.get("excerpt"),"confidence":e.get("confidence")} for e in memory.get("evidence",[])[:limit]]
def deterministic_case(memory,side):
    side=side.upper(); evidence=memory.get("evidence",[]); preferred=[e for e in evidence if (e.get("theme") in {"growth","business_model","catalyst","cash_flow"} and e.get("kind") not in {"RISK","GOVERNANCE"})] if side=="BULL" else [e for e in evidence if e.get("theme") in {"risk","governance","cash_flow"} or e.get("kind") in {"RISK","GOVERNANCE"}]; points=[]
    for e in preferred[:12]:
        text=e.get("claim") or e.get("excerpt") or ""
        if text: points.append({"point":text[:500],"evidence_ids":[e.get("evidence_id")] if e.get("evidence_id") else [],"strength":"source_only"})
    return {"side":side,"summary":f"Deterministic {side.lower()} evidence collection; LLM synthesis not enabled.","points":points,"key_assumptions":[],"what_must_be_true":[],"invalidation_conditions":[],"missing_evidence":[],"confidence":"low" if len(points)<3 else "medium","mode":"deterministic"}
def build_case(memory,side):
    side=side.upper()
    if side not in {"BULL","BEAR"}: raise ValueError("side must be BULL or BEAR")
    if not configured(): return deterministic_case(memory,side)
    role="Build the strongest evidence-supported upside thesis, naming assumptions and invalidation conditions. Do not hide adverse evidence." if side=="BULL" else "Attack the thesis using supported business, cash-flow, governance, concentration, competition, execution and capital-allocation risks. Do not invent problems."
    system=f"You are one side of an adversarial equity-research system. {role} Use ONLY supplied context/evidence. Every point must cite evidence IDs. Do not issue an investment recommendation."; user=f"Company:{memory.get('company')}\nSide:{side}\nContext:{json.dumps(memory.get('financial_context',{}),ensure_ascii=False)}\nEvidence:{json.dumps(_evidence(memory),ensure_ascii=False)}\nReturn JSON with side,summary,points,key_assumptions,what_must_be_true,invalidation_conditions,missing_evidence,confidence."
    result=_post_json([{"role":"system","content":system},{"role":"user","content":user}]); result["mode"]="llm"; return result
def build_bull_bear(memory): return {"company":memory.get("company"),"generated_at":datetime.now(timezone.utc).isoformat(),"bull":build_case(memory,"BULL"),"bear":build_case(memory,"BEAR")}
