#!/usr/bin/env python3
"""Validate the kernel-compatible thermal/HVAC v1 catalog."""
from __future__ import annotations
import copy,json,re
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
VECTORS=ROOT/"api/v1/packs/thermal-hvac-acceptance-vectors.json"
DOCUMENT=ROOT/"api/v1/packs/thermal-hvac-v1.md"
PACK={"id":"helianthus.pack.thermal","version":"1.0.0"}
ID=re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
KINDS={"quantity","symbol","text","symbols","boolean","time"}
FIELDS={"thermal.measurement.air_temperature","thermal.measurement.water_temperature","thermal.measurement.humidity_relative","thermal.measurement.flow_rate","thermal.measurement.power","thermal.setpoint.temperature","thermal.setpoint.dhw_temperature","thermal.mode.system","thermal.mode.zone","thermal.demand.level","thermal.status.operation","thermal.status.fault","thermal.action.state"}
DIMS={"thermal.dimension.system","thermal.dimension.zone","thermal.dimension.circuit","thermal.dimension.dhw","thermal.dimension.ventilation"}
SERVICES={"thermal.service.system","thermal.service.zone","thermal.service.circuit","thermal.service.dhw","thermal.service.ventilation"}
CAPS={"thermal.capability.read.system","thermal.capability.read.zone","thermal.capability.read.circuit","thermal.capability.read.dhw","thermal.capability.read.ventilation","thermal.capability.set_temperature","thermal.capability.set_mode"}
OPS={"thermal.operation.set_temperature","thermal.operation.set_mode"}; EFFECTS={"thermal.effect.set_temperature","thermal.effect.set_mode"}
PORTAL={"thermal.portal.read.system","thermal.portal.read.zone","thermal.portal.read.circuit","thermal.portal.read.dhw","thermal.portal.read.ventilation","thermal.portal.operation.set_temperature","thermal.portal.operation.set_mode"}
DOMAINS={"thermal_hvac":("helianthus.pack.thermal","accepted"),"pv_inverter":("helianthus.pack.pv","follow_on"),"storage_bms":("helianthus.pack.storage","follow_on"),"evse":("helianthus.pack.evse","follow_on"),"infrastructure":("helianthus.pack.infrastructure","follow_on")}
LIFECYCLE={"source_epoch","driver_generation","semantic_revision","capability_qualification","activation","generation_fencing","partial_updates","stale_unknown_evidence","last_known_good_retention"}
LOSS={"native_enum","precision_range","multiple_zones_faces","schedules","vendor_extensions","unavailable_fields","conflicting_sources","unsupported_operations"}
PUBLICATION_POLICY={"admission":["exact_source_epoch","current_driver_generation","exact_semantic_revision","qualified_active_capability"],"stale_generation":"reject","partial_publication":"supplied_valid_only_preserve_permitted_last_known_good","withdrawal":"explicit_generation_fenced","evidence":"stale_unknown_never_promote_or_authorize","tombstone":"retained_non_actionable"}
OPERATION_STAGES=["admission","dispatch","acknowledgement","readback","terminal_outcome"]
OUTCOMES=["rejected","failed_no_contact","acknowledged_unverified","applied","no_effect","conflict","indeterminate"]
PINS={"semantic_kernel":"da5ab4415d3bec73f9572aec1c495a6cdcbcba47","ebus":"ef076cb03e6cd5612f5dcbe7839e00ab4ee666c9","gree_can":"665a5f22f78c349b5e3063bda158af250a3f44b6","eebus_ledger":"81cd647c834e88c88a3c82ef9fbc5a0194f6b0f1","eebus_m625_donor":"cedf238e34f879815ba773e9cd76b2b31c2822a3","matter_draft":"29b4768a513cf566011ab8cd60df1bc495204953"}
def pairs(ps):
 d={}
 for k,v in ps:
  if k in d: raise ValueError(f"duplicate JSON key: {k}")
  d[k]=v
 return d
def load_document(path):
 with path.open(encoding="utf-8") as f:return json.load(f,object_pairs_hook=pairs)
def exact(actual,expected,label):
 if actual!=expected:raise ValueError(f"{label} differs")
def refs(items,label):
 if not isinstance(items,list) or not items:raise ValueError(f"{label} must be non-empty")
 got=[]; order=[]
 for x in items:
  if not isinstance(x,dict) or not isinstance(x.get("id"),str) or not ID.fullmatch(x["id"]):raise ValueError(f"{label} invalid ID")
  if x.get("ref")!={"pack":PACK,"id":x["id"],"version":"1.0.0"}:raise ValueError(f"{label} missing exact DefinitionRef owner/version")
  got.append(x["id"]);order.append(x.get("order"))
 if len(got)!=len(set(got)):raise ValueError(f"duplicate definition ID in {label}")
 if not all(isinstance(x,int) and x>0 for x in order) or order!=sorted(order) or len(order)!=len(set(order)):raise ValueError(f"{label} noncanonical order")
 return set(got)
def decimal(x):
 if not isinstance(x,dict) or set(x)!={"coefficient","exponent10"} or not isinstance(x["coefficient"],str) or not re.fullmatch(r"0|-?[1-9][0-9]*",x["coefficient"]) or not isinstance(x["exponent10"],int) or not -18<=x["exponent10"]<=18 or (x["coefficient"]=="0" and x["exponent10"]!=0) or (x["coefficient"]!="0" and x["coefficient"].endswith("0")):raise ValueError("bounds must use canonical kernel Decimal")
 return int(x["coefficient"])*10**x["exponent10"]
def validate_defs(c):
 d=c.get("definitions",{}); fields=d.get("fields"); exact(refs(fields,"fields"),FIELDS,"field catalog")
 for x in fields:
  if x.get("kind") not in KINDS:raise ValueError("field has non-kernel ValueKind")
  if not isinstance(x.get("dimension"),str) or not ID.fullmatch(x["dimension"]):raise ValueError("field has invalid dimension ID")
  if not isinstance(x.get("optional"),bool):raise ValueError("field lacks optionality")
  if x["kind"]=="quantity":
   if not isinstance(x.get("unit"),str) or not ID.fullmatch(x["unit"]):raise ValueError("field has invalid unit ID")
   b=x.get("bounds",{});
   if decimal(b.get("minimum"))>=decimal(b.get("maximum")):raise ValueError("field unordered numeric bounds")
  elif "unit" in x or "bounds" in x:raise ValueError("non-quantity field has quantity-only data")
  if x["kind"] in {"symbol","symbols"}:
   ss=x.get("symbols",[])
   if not isinstance(ss,list) or not ss or ss!=sorted(ss) or any("unknown" in s or "withheld" in s for s in ss):raise ValueError("field has invalid semantic symbols")
   if x["id"]=="thermal.action.state" and set(ss)!={"thermal.action.state.cooling","thermal.action.state.dhw","thermal.action.state.heating","thermal.action.state.idle","thermal.action.state.ventilating"}:raise ValueError("field has invalid semantic symbols")
 exact(refs(d.get("fact_dimensions"),"fact dimensions"),DIMS,"fact-key dimension contracts")
 services=d.get("services");caps=d.get("capabilities");ops=d.get("operations");effects=d.get("effect_rules");portal=d.get("portal_contributions")
 s=refs(services,"services");q=refs(caps,"capabilities");o=refs(ops,"operations");e=refs(effects,"effect rules");p=refs(portal,"Portal contributions")
 exact(s,SERVICES,"service catalog");exact(q,CAPS,"capability catalog");exact(o,OPS,"operation catalog");exact(e,EFFECTS,"effect catalog");exact(p,PORTAL,"Portal catalog")
 for x in services:
  if x.get("fact_key_dimension") not in DIMS:raise ValueError("service missing dimension contract")
 for x in caps:
  if x.get("service") not in s or x.get("activation")!="qualified_current_binding":raise ValueError("capability dangling service or activation")
  if x["id"].startswith("thermal.capability.set_") and not isinstance(x.get("constraints"),list):raise ValueError("capability lacks exact argument constraint")
 for x in ops:
  if x.get("capability") not in q or not set(x.get("arguments",[]))<=FIELDS or x.get("effect_rule") not in e:raise ValueError("operation dangling reference")
  cap=next(item for item in caps if item["id"]==x["capability"])
  if cap.get("constraints")!=x.get("arguments") or x.get("argument_constraints")!=x.get("arguments"):raise ValueError("operation/capability constraint mismatch")
  if x.get("preconditions")!=["current_generation","qualified_active_capability","exact_route","authority_admitted"] or x.get("readback")!="current_generation_exact_effect" or x.get("retry")!="forbidden_after_indeterminate":raise ValueError("operation lacks admission/readback")
  if x.get("stages")!=OPERATION_STAGES or x.get("terminal_outcomes")!=OUTCOMES:raise ValueError("operation stages/outcomes are incomplete")
 for x in effects:
  if x.get("operation") not in o or x.get("fact") not in FIELDS or x.get("operator")!="equal":raise ValueError("effect dangling reference")
 for x in portal:
  if x.get("kind")=="read" and (x.get("service") not in s or not set(x.get("fields",[]))<=FIELDS):raise ValueError("Portal dangling reference")
  if x.get("kind")=="operation" and x.get("operation") not in o:raise ValueError("Portal dangling reference")
 read_fields={field for x in portal if x.get("kind")=="read" for field in x.get("fields",[])}
 exact(read_fields,FIELDS,"read descriptor field coverage")
def validate_catalog(c):
 if not isinstance(c,dict) or c.get("pack")!=PACK or c.get("kernel_contract")!="helianthus.semantic.kernel/v1":raise ValueError("catalog lacks exact PackRef")
 if {x.get("id"):(x.get("pack"),x.get("state")) for x in c.get("domain_catalog",[]) if isinstance(x,dict)}!=DOMAINS:raise ValueError("five-domain catalog")
 if {x.get("id"):x.get("revision") for x in c.get("inputs",[]) if isinstance(x,dict)}!=PINS:raise ValueError("pinned public inputs")
 if set(c.get("lifecycle_axes",[]))!=LIFECYCLE:raise ValueError("lifecycle axes")
 if c.get("publication_withdrawal_policy")!=PUBLICATION_POLICY:raise ValueError("publication/withdrawal policy")
 if set(c.get("loss_dispositions",[]))!=LOSS:raise ValueError("projection-loss coverage")
 m={x.get("native_owner"):x for x in c.get("candidate_mappings",[]) if isinstance(x,dict)}
 if any(m.get(k,{}).get("state")!="candidate" or m[k].get("qualification")!="native_owner_required" for k in ("helianthus-docs-ebus","helianthus-docs-canbus")):raise ValueError("native mapping boundary")
 if m.get("helianthus-docs-eebus",{}).get("state")!="unknown_pending_std_01":raise ValueError("eeBUS mapping")
 validate_defs(c)
def resolve(c,path):
 x=c;parts=path.split(".")
 for y in parts[:-1]:x=x[int(y)] if isinstance(x,list) else x[y]
 return x,int(parts[-1]) if isinstance(x,list) else parts[-1]
def mutate(c,m):
 p,k=resolve(c,m["path"])
 if m["op"]=="set":p[k]=m.get("value")
 elif m["op"]=="delete":del p[k]
 elif m["op"]=="append_copy":p[k].append(copy.deepcopy(p[k][m["index"]]))
 elif m["op"]=="remove_id":p[k][:]=[x for x in p[k] if (x.get("id") if isinstance(x,dict) else x)!=m["id"]]
 else:raise ValueError("unknown vector mutation")
def validate_document(d):
 if d.get("contract")!="helianthus.semantic.pack.thermal.acceptance/v1" or d.get("pack_contract")!="helianthus.pack.thermal/v1":raise ValueError("contract ID")
 validate_catalog(d.get("catalog"));vs=d.get("vectors",[])
 if not any(x.get("polarity")=="positive" for x in vs) or not any(x.get("polarity")=="negative" for x in vs):raise ValueError("positive and negative vectors")
 for v in vs:
  candidate=copy.deepcopy(d["catalog"])
  for m in v.get("input",{}).get("mutations",[]):mutate(candidate,m)
  if v.get("polarity")=="positive":validate_catalog(candidate)
  else:
   try:validate_catalog(candidate)
   except ValueError as e:
    if v.get("expect",{}).get("error") not in str(e):raise ValueError(f"{v.get('id')}: {e}")
   else:raise ValueError(f"{v.get('id')}: accepted")
def main():
 d=load_document(VECTORS);validate_document(d);text=DOCUMENT.read_text()
 for group in d["catalog"]["definitions"].values():
  for x in group:
   if x["id"] not in text:raise ValueError(f"document misses {x['id']}")
 print("thermal/HVAC pack v1: PASS")
if __name__=="__main__":main()
