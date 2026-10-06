from adversarial_research import build_bull_bear
from contradiction_engine import challenge
from thesis_fragility import classify_thesis

def run_company_v6(memory):
    bundle=build_bull_bear(memory); challenged=challenge(bundle,memory); classification=classify_thesis(memory,challenged); return {"company":memory.get("company"),"bull_bear":bundle,"challenge":challenged,"classification":classification}
def run_v6(memories,finalist_names=None,progress=None):
    allowed={str(x).casefold() for x in finalist_names} if finalist_names else None; selected=[m for m in memories if allowed is None or str(m.get("company","")).casefold() in allowed]; results=[]
    for i,m in enumerate(selected,1):
        results.append(run_company_v6(m))
        if progress:progress(i,len(selected),m.get("company"))
    return results
def summary_rows(results):
    return [{"company":r.get("company"),**r.get("classification",{})} for r in results]
def report_markdown(results):
    return "# V6 Bull/Bear Adversarial Research\n\n"+"\n".join(f"- {r.get('company')}: {r.get('classification',{}).get('thesis_status')}" for r in results)
