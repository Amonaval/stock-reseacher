from __future__ import annotations
import json,os,requests
from datetime import datetime,timezone

def configured(): return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))
def _post_json(messages):
    base=os.getenv("LLM_BASE_URL","").rstrip("/"); r=requests.post(base+"/chat/completions",headers={"Authorization":f"Bearer {os.getenv('LLM_API_KEY')}","Content-Type":"application/json"},json={"model":os.getenv("LLM_MODEL"),"messages":messages,"temperature":0,"response_format":{"type":"json_object"}},timeout=300); r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])
def _sv(v): return {"strong":1.0,"medium":.65,"weak":.35,"source_only":.45}.get(str(v).lower(),.4)
def deterministic_challenge(bundle):
    bull=bundle.get("bull",{}); bear=bundle.get("bear",{}); bp=bull.get("points",[]); rp=bear.get("points",[]); bs=sum(_sv(x.get("strength")) for x in bp); rs=sum(_sv(x.get("strength")) for x in rp); total=bs+rs; balance=50 if total==0 else round(bs/total*100,1); missing=list(dict.fromkeys((bull.get("missing_evidence") or [])+(bear.get("missing_evidence") or []))); return {"company":bundle.get("company"),"bull_strength":round(min(100,bs*10),1),"bear_strength":round(min(100,rs*10),1),"thesis_balance":balance,"contradictions":[],"surviving_bull_points":bp[:8],"surviving_bear_points":rp[:8],"fragility_flags":missing[:10],"unresolved_questions":missing[:12],"challenge_summary":"Deterministic comparison only; semantic contradiction analysis requires the configured LLM.","challenge_confidence":"low","mode":"deterministic","generated_at":datetime.now(timezone.utc).isoformat()}
def challenge(bundle,memory):
    if not configured(): return deterministic_challenge(bundle)
    system="Neutral chair of adversarial equity research. Identify which arguments survive, contradictions, fragile assumptions, and missing evidence. Reward source support, not eloquence. Do not issue an investment recommendation."; user=f"Company:{bundle.get('company')}\nBull:{json.dumps(bundle.get('bull',{}),ensure_ascii=False)}\nBear:{json.dumps(bundle.get('bear',{}),ensure_ascii=False)}\nContext:{json.dumps(memory.get('financial_context',{}),ensure_ascii=False)}\nReturn JSON with company,bull_strength,bear_strength,thesis_balance,contradictions,surviving_bull_points,surviving_bear_points,fragility_flags,unresolved_questions,challenge_summary,challenge_confidence."
    result=_post_json([{"role":"system","content":system},{"role":"user","content":user}]); result["mode"]="llm"; result["generated_at"]=datetime.now(timezone.utc).isoformat(); return result
