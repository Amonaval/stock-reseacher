from __future__ import annotations
import json,os,requests

def configured(): return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))
def _post_json(messages):
    base=os.getenv("LLM_BASE_URL","").rstrip("/"); payload={"model":os.getenv("LLM_MODEL"),"messages":messages,"temperature":0.0,"response_format":{"type":"json_object"}}; r=requests.post(base+"/chat/completions",headers={"Authorization":f"Bearer {os.getenv('LLM_API_KEY')}","Content-Type":"application/json"},json=payload,timeout=240); r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])
def synthesize_company(memory):
    if not configured(): return {"ok":False,"error":"LLM not configured"}
    evidence=[{"evidence_id":x.get("evidence_id"),"document":x.get("document_title"),"document_type":x.get("document_type"),"date":x.get("document_date"),"page":x.get("page"),"kind":x.get("kind"),"theme":x.get("theme"),"claim":x.get("claim"),"excerpt":x.get("excerpt")} for x in memory.get("evidence",[])[:160]]
    system="""You are the synthesis layer of an evidence-driven equity research system. Use ONLY supplied financial context and evidence. Do not invent facts. Do not issue a buy/sell recommendation. Separate facts, management claims and inference. Every substantive synthesis point must cite one or more evidence_id values."""
    user=f"""Build a company research memo for {memory.get('company')}.\nFinancial context:\n{json.dumps(memory.get('financial_context',{}),ensure_ascii=False)}\nEvidence:\n{json.dumps(evidence,ensure_ascii=False)}\nReturn JSON with business_model, growth_drivers, management_and_capital_allocation, financial_quality_observations, catalysts, risks, governance_watchpoints, management_claims_to_verify, contradictions_or_uncertainties, missing_research, research_summary, research_confidence. Every point must include evidence_ids."""
    return {"ok":True,"memo":_post_json([{"role":"system","content":system},{"role":"user","content":user}])}
def memo_markdown(company,memo):
    lines=[f"# V4 Research Memo — {company}",""]; sections=[("Business model","business_model"),("Growth drivers","growth_drivers"),("Management & capital allocation","management_and_capital_allocation"),("Financial-quality observations","financial_quality_observations"),("Catalysts","catalysts"),("Risks","risks"),("Governance watchpoints","governance_watchpoints"),("Management claims to verify","management_claims_to_verify"),("Contradictions / uncertainties","contradictions_or_uncertainties")]
    for title,key in sections:
        lines += [f"## {title}",""]
        items=memo.get(key,[])
        if not items: lines.append("- No supported item extracted.")
        else:
            for item in items: lines += [f"- {item.get('point','')}  ",f"  Evidence: `{', '.join(item.get('evidence_ids',[]))}`"]
        lines.append("")
    lines += ["## Missing research",""]+[f"- {x}" for x in memo.get("missing_research",[])]+["","## Research summary","",memo.get("research_summary",""),"",f"**Research confidence:** {memo.get('research_confidence','')}","","_This memo is a research synthesis, not an investment recommendation._"]
    return "\n".join(lines)
