from __future__ import annotations
import json,os,requests
from collections import defaultdict
from datetime import datetime,timezone

def configured(): return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))
def _post_json(messages):
    base=os.getenv("LLM_BASE_URL","").rstrip("/"); payload={"model":os.getenv("LLM_MODEL"),"messages":messages,"temperature":0.0,"response_format":{"type":"json_object"}}; r=requests.post(base+"/chat/completions",headers={"Authorization":f"Bearer {os.getenv('LLM_API_KEY')}","Content-Type":"application/json"},json=payload,timeout=240); r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])
def _evidence_for_company(memory): return [{"evidence_id":e.get("evidence_id"),"document":e.get("document_title"),"document_type":e.get("document_type"),"date":e.get("document_date"),"page":e.get("page"),"theme":e.get("theme"),"kind":e.get("kind"),"claim":e.get("claim"),"excerpt":e.get("excerpt")} for e in memory.get("evidence",[])[:180]]
def execute_task(task,memory):
    if not configured(): return {"task":task,"status":"BLOCKED_NO_LLM","answer":"","evidence_ids":[],"confidence":"low","unresolved":[task.get("instruction")]}
    evidence=_evidence_for_company(memory)
    if not evidence: return {"task":task,"status":"BLOCKED_NO_EVIDENCE","answer":"","evidence_ids":[],"confidence":"low","unresolved":[task.get("instruction")]}
    system="Answer only from supplied evidence. Do not recommend buying or selling. Every conclusion must cite evidence_id values."
    user=f"Company: {memory.get('company')}\nResearch task:{json.dumps(task,ensure_ascii=False)}\nFinancial context:{json.dumps(memory.get('financial_context',{}),ensure_ascii=False)}\nEvidence:{json.dumps(evidence,ensure_ascii=False)}\nReturn JSON with answer,evidence_ids,contradicting_evidence_ids,confidence,unresolved,suggested_followups."
    result=_post_json([{"role":"system","content":system},{"role":"user","content":user}]); return {"task":task,"status":"COMPLETED" if result.get("answer") else "INSUFFICIENT_EVIDENCE","answer":result.get("answer",""),"evidence_ids":result.get("evidence_ids",[]),"contradicting_evidence_ids":result.get("contradicting_evidence_ids",[]),"confidence":result.get("confidence","low"),"unresolved":result.get("unresolved",[]),"suggested_followups":result.get("suggested_followups",[]),"completed_at":datetime.now(timezone.utc).isoformat()}
def execute_priority_tasks(tasks,memories,max_tasks=100):
    memory_map={str(m.get("company","")).casefold():m for m in memories}; ordered=sorted(tasks,key=lambda t:-float(t.get("priority") or 0))[:int(max_tasks)]; results=[]
    for task in ordered:
        memory=memory_map.get(str(task.get("company","")).casefold())
        if not memory: results.append({"task":task,"status":"BLOCKED_NO_MEMORY","answer":"","evidence_ids":[],"confidence":"low","unresolved":[task.get("instruction")]}); continue
        if task.get("task_type")=="SOURCE_GAP": results.append({"task":task,"status":"ROUTE_TO_SOURCE_ACQUISITION","answer":"","evidence_ids":[],"confidence":"low","unresolved":[task.get("instruction")]}); continue
        results.append(execute_task(task,memory))
    return results
def task_execution_summary(results):
    statuses=defaultdict(int)
    for r in results: statuses[r.get("status")]+=1
    return {"total":len(results),"by_status":dict(statuses),"completed":sum(1 for r in results if r.get("status")=="COMPLETED"),"unresolved":sum(1 for r in results if r.get("unresolved"))}
