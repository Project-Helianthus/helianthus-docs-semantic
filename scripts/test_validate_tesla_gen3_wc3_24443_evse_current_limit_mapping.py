#!/usr/bin/env python3
"""Focused mutations for the Tesla Gen3 WC3 EVSE mapping gate."""
import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tesla_mapping", ROOT / "scripts/validate_tesla_gen3_wc3_24443_evse_current_limit_mapping.py")
mapping = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mapping; spec.loader.exec_module(mapping)

def reject(name, path, value, expected):
    contract = copy.deepcopy(mapping.load()); mapping.mutate(contract, {"path": path, "value": value})
    try: mapping.validate_contract(contract)
    except ValueError as error:
        if str(error) != expected: raise AssertionError(f"{name}: {error}")
    else: raise AssertionError(f"{name} accepted")
    print(f"{name}: REJECTED")

def main():
    cases = [("pin", "pins.gateway_main", "0" * 40, "contract"), ("profile", "native_contract.profile", "wc3_24_44_4", "native_contract"), ("outbound", "native_contract.outbound_allowed", True, "native_contract"), ("identity_derivation", "identity.forbidden_derivations.0", "serial", "identity_contract"), ("identity_reuse", "identity.failure", "allow_reuse", "identity_contract"), ("lifecycle", "lifecycle.required.0", "timestamp", "lifecycle_contract"), ("persistent_target", "field_rules.0.target", "evse.limit.allocated_current", "field_rules"), ("provisional_disposition", "field_rules.1.disposition", "always", "field_rules"), ("unsupported", "unsupported.0", "power_allowed", "withheld_or_unsupported"), ("precedence", "projection.error_precedence.0", "x", "projection"), ("operations", "projection.operations", "available", "projection"), ("cutover", "consumer_cutover.forbidden.0", "allowed", "consumer_cutover")]
    for case in cases: reject(*case)
    contract = mapping.load(); baseline = contract["scenarios"][0]["input"]
    for name, path, value, expected in [("blank_identity", "identity.asset_id", "", "identity_invalid"), ("wrong_unit_profile", "profile", "other", "profile_or_version_invalid"), ("missing_receipt", "lifecycle.receipt_timestamp", "", "lifecycle_invalid"), ("operation_attempt", "operation", "evse.operation.set_allocated_current", "unsupported_fact_or_operation"), ("evidence", "evidence.provisional_ack", "bad", "evidence_binding_invalid")]:
        candidate = copy.deepcopy(baseline); mapping.mutate(candidate, {"path": path, "value": value})
        try: mapping.project(candidate, contract)
        except ValueError as error:
            if str(error) != expected: raise AssertionError(error)
        else: raise AssertionError(name + " accepted")
        print(name + ": REJECTED")
    print("baseline: PASS; 17 focused mutations rejected")

if __name__ == "__main__": main()
