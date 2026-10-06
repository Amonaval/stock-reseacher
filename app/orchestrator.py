from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

REQUIRED_DOC_TYPES={"annual_report":1.00,"quarterly_result":0.95,"investor_presentation":0.65,"earnings_call":0.65,"exchange_filing":0.80,"credit_rating":0.55}
RESEARCH_GAP_TASKS={"annual_report":"Acquire a recent annual report and extract business, governance, capital-allocation and risk evidence.","quarterly_result":"Acquire recent quarterly/annual financial results and extract operating changes.","investor_presentation":"Find a recent investor presentation for management framing, segments, capacity and growth initiatives.","earnings_call":"Find a recent earnings-call transcript/record for management guidance and Q&A.","exchange_filing":"Collect recent material exchange filings and scan for events, governance and capital-allocation changes.","credit_rating":"Find a recent credit-rating rationale for debt, liquidity, working-capital and business-risk assessment."}

def _now(): return datetime.now(timezone.utc).isoformat()

def research_stage(memory):
    f=memory.get("financial_context",{})
    if f.get("v3_funnel_decision")=="ELIMINATE": return "STOPPED_V3"
    readiness=float(memory.get("research_readiness") or 0); quality=float(memory.get("evidence_quality") or 0)
    if readiness>=78 and quality>=65: return "READY_FOR_V5"
    if readiness>=48: return "ACTIVE_RESEARCH"
    return "SOURCE_ACQUISITION"

def generate_tasks(memory):
    company=memory.get("company"); present=set(memory.get("document_types",[])); tasks=[]
    for doc_type,weight in REQUIRED_DOC_TYPES.items():
        if doc_type not in present: tasks.append({"company":company,"task_type":"SOURCE_GAP","priority":round(70+weight*25,1),"target":doc_type,"instruction":RESEARCH_GAP_TASKS[doc_type],"reason":f"{doc_type} is missing from research memory.","status":"PENDING","created_at":_now()})
    f=memory.get("financial_context",{}); warnings=f.get("financial_warnings") or []
    for warning in warnings[:8]: tasks.append({"company":company,"task_type":"VERIFY_WARNING","priority":88,"target":"financial_warning","instruction":f"Find primary evidence that explains or contradicts this V3 warning: {warning}","reason":"Financial warning requires contextual research before deeper conviction work.","status":"PENDING","created_at":_now()})
    if memory.get("risk_items",0)==0 and memory.get("documents",0)>=2: tasks.append({"company":company,"task_type":"ADVERSARIAL_GAP","priority":82,"target":"risk","instruction":"Actively search for downside, governance, customer concentration, working-capital, litigation and execution-risk evidence.","reason":"Research memory has documents but no meaningful downside evidence.","status":"PENDING","created_at":_now()})
    if memory.get("management_claims",0)>0: tasks.append({"company":company,"task_type":"PROMISE_DELIVERY","priority":76,"target":"management_delivery","instruction":"Find later-dated evidence to verify whether earlier management guidance/promises were delivered, delayed or missed.","reason":f"{memory.get('management_claims')} unresolved management claims are present.","status":"PENDING","created_at":_now()})
    return sorted(tasks,key=lambda x:-x["priority"])

def build_orchestrator_state(memories,source_catalog=None):
    source_catalog=source_catalog or []; source_by_company=Counter(str(x.get("company","")).strip().casefold() for x in source_catalog); states=[]; all_tasks=[]
    for m in memories:
        tasks=generate_tasks(m); all_tasks.extend(tasks); f=m.get("financial_context",{})
        states.append({"company":m.get("company"),"stage":research_stage(m),"v3_rank":f.get("financial_rank"),"v3_score":f.get("v3_priority_score"),"research_readiness":m.get("research_readiness"),"evidence_quality":m.get("evidence_quality"),"documents":m.get("documents"),"discovered_sources":source_by_company[str(m.get("company","")).strip().casefold()],"open_tasks":len(tasks),"next_action":tasks[0]["instruction"] if tasks else "Ready for deeper research.","next_action_reason":tasks[0]["reason"] if tasks else "Minimum V4 evidence/readiness thresholds met."})
    return sorted(states,key=lambda x:(0 if x["stage"]=="SOURCE_ACQUISITION" else 1 if x["stage"]=="ACTIVE_RESEARCH" else 2,x.get("v3_rank") or 10**9)),all_tasks

def narrow_for_next_stage(states,max_companies=50):
    eligible=[x for x in states if x["stage"] in {"READY_FOR_V5","ACTIVE_RESEARCH"}]; eligible.sort(key=lambda x:(-(float(x.get("v3_score") or 0)*0.55+float(x.get("research_readiness") or 0)*0.45),x.get("v3_rank") or 10**9)); selected=eligible[:max_companies]; selected_names={x["company"] for x in selected}; decisions=[]
    for x in states:
        if x["company"] in selected_names: decision="ADVANCE_TO_V5_QUEUE"; reason="Highest combined V3 priority and V4 research readiness within current research budget."
        elif x["stage"]=="SOURCE_ACQUISITION": decision="NEEDS_MORE_SOURCES"; reason=x["next_action_reason"]
        elif x["stage"]=="STOPPED_V3": decision="STOPPED"; reason="V3 hard elimination."
        else: decision="HOLD_FOR_LATER_RESEARCH"; reason="Outside current V5 research budget; retained for future reevaluation."
        decisions.append({**x,"orchestrator_decision":decision,"decision_reason":reason})
    return decisions
