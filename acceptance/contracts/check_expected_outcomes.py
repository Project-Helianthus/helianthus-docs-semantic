#!/usr/bin/env python3
"""Compare each contract vector's canonical outcome with an independent expectation.

The expectation map below is written from the rules of api/v1/driver-contract.md
and not read from the vector files. A vector file is accepted only when its
identifiers are exactly the required set and every canonical `expected` member is
equal to the expectation. Explanatory text is kept outside the compared outcome.
Behaviour rules that have an executable form (retry normalization, path-node
allocation, composition evidence, the kernel Quality promotion wording) are
recomputed here as well.
"""
from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_family_catalog_v1 as family  # noqa: E402
import validate_kernel_v1 as kernel  # noqa: E402

LEGACY_DOMAIN = "helianthus.semgraph.resource/v1"
PATH_DOMAIN = "helianthus.semgraph.path-node/v1"
P1 = "resource:00000000000000000000000000000001"
P2 = "resource:00000000000000000000000000000002"
IDA = {"scheme": "scheme.ieee.eui48", "issuer": "", "token": "0A1B2C3D4E5F"}
IDB = {"scheme": "scheme.ieee.eui48", "issuer": "", "token": "0A1B2C3D4E60"}
BASE_KEY = {"installation": "inst-a", "driver_kind": "driver-x", "instance_key": "i1", "node_kind": "resource.bridge"}


def policy(budget=0, initial="0s", maximum="0s", jitter=0, enabled=False, p_initial="0s", p_maximum="0s"):
    return {"Budget": budget, "InitialDelay": initial, "MaxDelay": maximum, "JitterRatio": jitter,
            "Persistent": {"Enabled": enabled, "InitialDelay": p_initial, "MaxDelay": p_maximum}}


def retry(normalized):
    return {"outcome": "normalized retry policy", "normalized": normalized}


def compose(outcome, composition, verified, module, version, accepted):
    return {"outcome": outcome, "composition": composition, "composition_verified": verified,
            "module": module, "version": version, "accepted": accepted}


def early(outcome, handled, code, err, parsed):
    return {"outcome": outcome, "handled": handled, "exitCode": code, "err": err, "configuration_parsed": parsed}


def typed(outcome, accepted, **more):
    return dict({"outcome": outcome, "accepted": accepted}, **more)


EXPECTED = {
    "composition.json": {
        "K-RETRY-ZERO": retry(policy(0, "1s", "1s", 0.2)),
        "K-RETRY-BUDGET-NEGATIVE": retry(policy(0, "2s", "4s", 0.1)),
        "K-RETRY-INITIAL-NONPOSITIVE": retry(policy(2, "1s", "1s", 0.1)),
        "K-RETRY-MAX-BELOW-INITIAL": retry(policy(2, "5s", "5s", 0.1)),
        "K-RETRY-JITTER-ZERO": retry(policy(1, "1s", "8s", 0.2)),
        "K-RETRY-JITTER-NEGATIVE": retry(policy(1, "1s", "8s", 0)),
        "K-RETRY-JITTER-ABOVE": retry(policy(1, "1s", "8s", 0.5)),
        "K-RETRY-JITTER-KEPT": retry(policy(1, "1s", "8s", 0.5)),
        "K-RETRY-PERSISTENT-ENABLED": retry(policy(1, "1s", "8s", 0.3, True, "1s", "1s")),
        "K-RETRY-PERSISTENT-MAX-BELOW": retry(policy(1, "1s", "8s", 0.3, True, "3s", "3s")),
        "K-RETRY-PERSISTENT-DISABLED": retry(policy(1, "1s", "8s", 0.3, False, "-1s", "0s")),
        "K-CONFIG-HANDOFF": {
            "outcome": "per-instance secret reference handoff",
            "instances": [{"Instance": "i-a", "Enabled": True, "SecretRef": "ref-a"},
                          {"Instance": "i-b", "Enabled": True, "SecretRef": ""}],
            "host_resolves_secret": False, "neighbour_reference_shared": False, "operands_decoded_by": "factory"},
        "K-EARLY-HANDLED-EXIT": early("handled exit before flags", True, 3, None, False),
        "K-EARLY-HANDLED-ERROR": early("handled error before flags", True, 1, "present", False),
        "K-EARLY-NOT-HANDLED": early("not handled continues", False, 0, None, True),
        "K-EARLY-NONPARTICIPATING": {
            "outcome": "nonparticipating factory is not called", "factory_implements_interface": False,
            "called": False, "error": None},
        "K-COMPOSE-CLAIMED": compose("claimed composition with module and version", "composed", True,
                                     "synthetic.module", "1.0.0", True),
        "K-COMPOSE-MISSING-MODULE": compose("missing module rejected", "composed", True, None, "1.0.0", False),
        "K-COMPOSE-MISSING-VERSION": compose("missing version rejected", "composed", True,
                                             "synthetic.module", None, False),
        "K-COMPOSE-NOT-COMPOSED": compose("not_composed carries neither", "not_composed", False, None, None, True),
        "K-COMPOSE-NOT-COMPOSED-CARRIES": compose("not_composed carrying module rejected", "not_composed", False,
                                                  "synthetic.module", None, False),
        "K-VERIFICATION-HARDWARE": {
            "outcome": "tested_on_hardware needs a hardware test record", "verification": "tested_on_hardware",
            "evidence_kinds": ["specification"], "accepted": False},
        "K-CALENDAR-GUARD": {
            "outcome": "immutable acquisition with same-calendar guard",
            "reference": "one observed time and civil year, month and day",
            "check_same_calendar": "ok", "check_other_calendar_or_civil_day": "error"},
        "K-LINK-NODE-SLOT": {
            "outcome": "link node slot selects the reserved key", "slot": "uplink",
            "key": "configured parent plus slot anchor in installation, driver and instance scope",
            "transport_ownership_changed": False, "exclusive_claim_matching_changed": False,
            "empty_slot": "normal configured-link key construction"},
    },
    "identity.json": {
        "I-TWO-LIFECYCLES": {
            "outcome": "equal sorted node ids, link keys, endpoints, types, aliases and source links",
            "varied": ["factory order", "discovery order", "clocks", "generations"],
            "compared": "canonical graph results after reopening durable state",
            "excluded": ["cut digests", "timestamps", "leases"]},
        "I-THREE-INSTANCES": {
            "outcome": "three same-kind instances keep three disjoint node sets under their instance keys",
            "instances": 3, "shared_nodes": 0},
        "I-SHARED-EBUS": {
            "outcome": "two direct links and a shared bus keep one shared bus node",
            "shared_bus_nodes": 1, "direct_links": 2},
        "I-CHANGED-SERIAL": {
            "outcome": "a changed serial is a new unbound claim", "new_claim": "unbound", "old_reference": "kept",
            "history": "kept", "replacement_inferred": False, "rebind": "only a person"},
        "I-ABSENT-TARGET": {
            "outcome": "the same To is kept while the target is absent and on its return", "to": "unchanged",
            "complete_cut": "dangling", "partial_cut": "outside-cut",
            "on_return": "same key resolves with every retained claim and basis", "phantom_resource": False},
        "I-TWO-PUBLISHERS": {
            "outcome": "two publishers keep separate bases", "claims": 2,
            "after_first_withdrawn": {"remaining_claims": 1, "basis": "second publisher's"},
            "after_target_return": {"remaining_claims": 1, "basis": "second publisher's"}},
        "I-ALLOC-LEGACY-SLOT": {
            "outcome": "legacy slot id preserved", "domain": LEGACY_DOMAIN,
            "fields": ["resource.zone", "slot", P1, "zone-1"], "id": "resource:a0b7d12925ca145e10e3670e018086ce"},
        "I-ALLOC-LEGACY-KEY": {
            "outcome": "legacy native key id preserved", "domain": LEGACY_DOMAIN, "kind": "resource.equipment",
            "identity": IDA, "id": "resource:eb2e2bec29873eff6599e98733aaa17e"},
        "I-ALLOC-PATH-SLOT": {
            "outcome": "path-node slot id", "domain": PATH_DOMAIN,
            "key": dict(BASE_KEY, anchor={"tag": "slot", "parent": "", "slot": "primary"}),
            "id": "resource:70dc2ac7d92d82c2e1f254a5c532541d"},
        "I-ALLOC-PATH-KEY": {
            "outcome": "path-node key id", "domain": PATH_DOMAIN,
            "key": dict(BASE_KEY, anchor={"tag": "key", "identity": IDA}),
            "id": "resource:ee5fba45d9c4a6dfd8dad3236f362e93"},
        "I-ALLOC-INJECTIVE": {
            "outcome": "field boundaries cannot shift",
            "first": {"fields": ["a", "bc", "i1", "resource.bridge", "slot", "", "primary"],
                      "id": "resource:cba8c8d09199dde66a1cb714962a26ed"},
            "second": {"fields": ["ab", "c", "i1", "resource.bridge", "slot", "", "primary"],
                       "id": "resource:247e6998a2c167a928e81ca4c1b6facb"},
            "equal": False},
        "I-ALLOC-VARY": {
            "outcome": "every key field changes the id", "domain": PATH_DOMAIN,
            "base": dict(BASE_KEY, anchor={"tag": "slot", "parent": P1, "slot": "primary"},
                         id="resource:c26c0b683e132c9f0c564d4ad4513cf2"),
            "variants": [
                {"field": "installation", "value": "inst-b", "id": "resource:97c451ded54fdd490ebab2c1b4749cf2"},
                {"field": "driver_kind", "value": "driver-y", "id": "resource:1b53bf34dc9352a6afccea5c05ce34b0"},
                {"field": "instance_key", "value": "i2", "id": "resource:78bf3f7cd8944dce824e9655373a7970"},
                {"field": "node_kind", "value": "resource.link", "id": "resource:cd978b53e338794ad8dee422d892d828"},
                {"field": "parent", "value": "resource:00000000000000000000000000000002", "id": "resource:eca0387b619acfda72959460a3c38e41"},
                {"field": "slot", "value": "secondary", "id": "resource:169a3c1f6fbf49027d2ab9db12a2dfa0"},
                {"field": "anchor_tag", "value": "key with identity token 0A1B2C3D4E5F", "id": "resource:ee5fba45d9c4a6dfd8dad3236f362e93"},
                {"field": "digest", "value": "key with identity token 0A1B2C3D4E60", "id": "resource:0ad6658796b5672a89c7b900b716b268"},
            ],
            "all_distinct": True},
        "I-ALLOC-DOMAIN": {
            "outcome": "the two domains never collide", "fields": ["resource.bridge", "slot", "", "primary"],
            "legacy_id": "resource:0da424d548559cf247de0e155e51a59a",
            "path_node_id": "resource:2d3eb89ad2eb726c88d1ee4482c4ffb9", "equal": False},
    },
    "sources.json": {
        "S-THREE-PATHS": {
            "outcome": "one element with three paths, each a source link with priority, path, resolution and availability",
            "paths": 3, "data_from": "highest current source", "averaged": False},
        "S-TIE": {
            "outcome": "the most recent receipt wins a tie, and indistinguishable receipts use source-key order",
            "replay_refreshes_receipt": False, "unrelated_device_clocks_compared": False},
        "S-PRIORITY-TIE-ZERO": {
            "outcome": "typed priority-tie finding below the winner", "priority_tie": 0,
            "sources": ["lower-a", "lower-b"], "sample_values": None, "steps": None,
            "incomparable_marker": None, "winner": "unchanged"},
        "S-WITHIN-STEP": {
            "outcome": "a difference within the larger step is no finding", "difference": "0.4 K",
            "steps": ["0.5 K", "0.1 K"], "finding": None},
        "S-OVER-STEP": {
            "outcome": "a difference over the larger step is a finding and does not change the winner",
            "difference": "0.8 K", "steps": ["0.5 K", "0.1 K"],
            "finding": "disagreement with sources, values and steps", "winner": "unchanged"},
        "S-MISSING-WINNER": {
            "outcome": "the element shows unknown with no substitution by a lower source",
            "winner_state": "unknown", "lower_source_used": False},
        "S-STOPPED": {
            "outcome": "a stopped generation keeps the source and its last value visible as stale; the mirror is not authoritative",
            "state": "stale", "highest_source": "unchanged", "mirror_authoritative": False},
        "S-WITHDRAWAL": {
            "outcome": "withdrawal of the declaration removes the source from current contention",
            "contention": "removed", "sample_withdrawn_in_same_commit": True},
        "S-OWNER": {
            "outcome": "the command is routed to the setting owner only: no broadcast and not to the latest reader",
            "routed_to": "setting owner", "broadcast": False, "latest_reader": False,
            "no_owner_route": "nothing sent"},
        "S-INCOMPARABLE": {
            "outcome": "a pre-change mirror sample against a fresh sample is incomparable, not disagreement",
            "finding": "incomparable", "disagreement": False},
        "S-SLOTS": {
            "outcome": "two slots of one definition on one subject are two elements, each with its own source, candidate and route from one publisher commit",
            "elements": 2, "contend": False, "commits": 1},
    },
    "joins.json": {
        "J-ORDER": {"outcome": "opposite publication orders give the same join", "orders": "opposite",
                    "joins_equal": True},
        "J-NO-PROOF": {"outcome": "no proof leaves the join unapplied", "joined": False, "reason": "no proof",
                       "status": "unapplied"},
        "J-MATCH": {"outcome": "a matching proof joins and the certified survivor is the representative",
                    "joined": True, "representative": "certified survivor", "member_references_resolvable": True},
        "J-AMBIGUOUS": {"outcome": "ambiguous proof is unapplied with a finding", "joined": False,
                        "finding": "ambiguous"},
        "J-REPLAY": {"outcome": "a replay of the same certification changes nothing", "state_changed": False},
        "J-MFR-SERIAL": {
            "outcome": "a complete, equal, unambiguous manufacturer and serial pair resolves as one resource",
            "members": 2, "resources": 1, "scheme_id_used": False,
            "admitted_by": "session publisher with ownership stamp"},
        "J-MFR-SERIAL-MISSING": {"outcome": "a missing component infers no identity", "resources": 2,
                                 "reason": "kept"},
        "J-MFR-SERIAL-AMBIGUOUS": {"outcome": "an ambiguous serial infers no identity", "resources": 2,
                                   "reason": "kept"},
        "J-BINDING-LINK": {
            "outcome": "the configured binding association changes neither identity membership nor routes",
            "binding_resolves_to": "operator-selected resource", "unrelated_links": "survive",
            "certification": False,
            "withdrawals_with_pending": {"withdrawn_association": "disappears",
                                         "other_qualified_association": "pending until its eligible carry"},
            "redeclared_withdrawn_binding": {"link": "stays withdrawn", "proposed": False,
                                             "carried_by": "next eligible successor binding"}},
    },
    "consumers.json": {
        "C-NO-TRANSPORT": {
            "outcome": "a no transport publisher with a virtual node, typed links and an operator-declared observation keeping its Origin evidence",
            "transport": None, "virtual_node": "durable key", "typed_link_to_foreign_node": True,
            "foreign_to_foreign_link": "retained in the runtime overlay, resolved with no fabricated resource, kernel validation not relaxed",
            "origin_evidence": "kept", "start_output_receives": ["SemanticInput", "ScopedOperations"]},
        "C-DERIVED": {"outcome": "a derived value carries its lineage and is never presented as measured",
                      "origin": "derived", "lineage": "kept", "presented_as_measured": False},
        "C-CYCLE": {"outcome": "a formula cycle is rejected", "accepted": False, "reason": "cycle"},
        "C-REMOTE": {"outcome": "a remote read keeps (BridgeID, ID) and provenance under local publisher ownership",
                     "identity": "(BridgeID, ID)", "discovery_is_authority": False},
        "C-DONOR": {"outcome": "a consumer does not mutate a donor snapshot", "donor_snapshot_changed": False},
        "C-COLLIDE": {"outcome": "the same local id on two bridges does not collide", "bridges": 2,
                      "collision": False},
        "C-LOOP": {"outcome": "reflected origins and loops are rejected", "accepted": False},
        "C-ROUNDTRIP": {"outcome": "a serialized GraphQL round trip preserves the record", "preserved": True},
        "C-RESUME-ABA": {
            "outcome": "A to B to A returns both transitions, distinct from endpoint coalescing",
            "transitions": 2, "coalesced_to_endpoint": False, "order": "commit order"},
        "C-CROSS-ASSET": {
            "outcome": "a virtual total of two assets resolves each foreign input at its exact revision",
            "inputs": 2, "resolved_at": "exact revision", "local_candidate_lookup": False},
        "C-REMOTE-CUT": {"outcome": "every page belongs to one cut", "mixed_revision_view": False,
                         "advance_between_pages": "fails"},
        "C-REMOTE-RESYNC": {"outcome": "an expired or unavailable resume position is an explicit resync",
                            "resync": "explicit", "silent_mixed_cut": False},
        "C-LENS-SUM": {
            "outcome": "a phase-only sum on the same captured cut returns the exact typed value with the observed aggregate",
            "cut": "same", "sum": "typed value"},
        "C-LENS-PARTIAL": {
            "outcome": "a partial cut keeps its lens members and paging with a separate sum absence",
            "lens_result": "members and paging kept", "early_reason_return": False,
            "sum": "absence reason", "cut": "same"},
        "C-LENS-OUTSIDE": {"outcome": "an outside-scope request is refused", "accepted": False,
                           "scope_widened": False, "revision_switched": False},
        "C-INVOKE-CALLBOUND": {
            "outcome": "a call-bound invocation has no absolute deadline and cannot be serialized or replayed",
            "absolute_deadline": None, "serializable": False, "replayable": False,
            "timeout_dropped_opts_in": False},
        "C-INVOKE-FINITE": {"outcome": "ordinary invocation keeps the finite request and caller deadline rules",
                            "deadline": "finite"},
        "C-COMPOUND-PARTIAL": {
            "outcome": "a compound result reports partial with ordered steps", "partial": True, "steps": "ordered",
            "non_attempted_step": {"delivery": None, "acknowledgement": None, "readback": None},
            "native_coordinates_exposed": False},
        "C-EXECUTOR-REGISTER": {
            "outcome": "registration alone cannot authorize a send and an old unregister cannot remove its successor",
            "send_before_route_committed": False, "foreign_duplicate_or_retired": "refused",
            "stale_unregister_removes_successor": False},
        "C-NATIVE-RESUME": {
            "outcome": "unavailable history resyncs and an unavailable pinned cut returns revision_conflict",
            "history_unavailable": "resync", "pinned_cut_unavailable": "revision_conflict"},
    },
    "namespaces.json": {
        "N-CUT": {
            "outcome": "the same keys, membership, schema, value, ordering, errors, scope, redaction, action effects and terminal outcome of an accepted invocation through GraphQL and MCP",
            "surfaces": ["GraphQL", "MCP"], "same_cut_and_principal": True},
        "N-OWNER": {"outcome": "a conflicting owner of a namespace is rejected", "accepted": False},
    },
    "limits.json": {
        "L-QUERY": {"outcome": "the queried limit wins over the specification's", "applies": "queried limit",
                    "origin": "device query at first population"},
        "L-SPEC": {"outcome": "with no query the specification's limit applies", "applies": "specification's limit",
                   "origin": "specification clause"},
    },
    "structure.json": {
        "G-POS-SUBJ-CLASS-1": typed("a fact on a class-level dimension about an inverter accepted", True),
        "G-NEG-SUBJ-CLASS-1": typed("a resource of an undeclared class rejected with a reason", False,
                                    reason="undeclared class"),
        "G-POS-QUAL-1": typed("a declared qualifier accepted", True),
        "G-NEG-QUAL-1": typed("an undeclared qualifier rejected with a reason", False,
                              reason="undeclared qualifier"),
        "G-POS-PARAM-OMIT-1": typed("an intent with only its arguments accepted: optional omitted", True),
        "G-NEG-PARAM-REPEAT-1": typed("a repeated parameter rejected with a reason", False,
                                      reason="repeated parameter"),
        "G-NEG-PARAM-UNDECLARED-1": typed("an undeclared field rejected with a reason", False,
                                          reason="undeclared field"),
        "G-NEG-EVENT-PACK-1": typed("a foreign-pack payload fails the contract", False),
        "G-NEG-EVENT-RELATION-1": typed("a foreign-pack relation fails the contract", False),
        "G-POS-RELEASE-1": typed("the declared boolean false alone accepted under the release case: false alone",
                                 True),
        "G-NEG-RELEASE-MIXED-1": typed("a request carrying release and set arguments rejected: mixed case", False),
        "K-POS-026": typed(
            "A PV release accepts boolean false under the existing argument field ID and has no predicate.",
            True),
        "K-POS-027": typed(
            "An acknowledged EVSE release is unverified and reads nothing back.",
            True, execution_outcome='acknowledged_unverified'),
        "K-NEG-066": typed(
            "A release does not accept true.",
            False, error_id='invalid_value'),
        "K-NEG-067": typed(
            "Numeric zero is not boolean false.",
            False, error_id='invalid_value'),
        "K-NEG-068": typed(
            "A release cannot mix the numeric set and boolean release arguments.",
            False, error_id='invalid_value'),
        "K-NEG-069": typed(
            "A release cannot carry a fact predicate.",
            False, error_id='invalid_value'),
        "K-NEG-070": typed(
            "A numeric set intent requires its complete fact predicate.",
            False, error_id='invalid_value'),
        "K-NEG-071": typed(
            "A release record cannot carry readback even if the relation is inconclusive.",
            False, error_id='invalid_outcome'),
        "K-NEG-072": typed(
            "A release cannot report applied.",
            False, error_id='invalid_outcome'),
        "K-NEG-073": typed(
            "A release cannot report conflict.",
            False, error_id='invalid_outcome'),
        "K-NEG-074": typed(
            "A release cannot report no effect.",
            False, error_id='invalid_outcome'),
    },
}

STEMS = {
    "I-TWO-LIFECYCLES": "equal sorted", "I-THREE-INSTANCES": "three same-kind", "I-SHARED-EBUS": "two direct",
    "I-CHANGED-SERIAL": "unbound", "I-ABSENT-TARGET": "same To", "I-TWO-PUBLISHERS": "separate bases",
    "S-THREE-PATHS": "three paths", "S-TIE": "source-key order", "S-WITHIN-STEP": "within the larger step",
    "S-OVER-STEP": "does not change the winner", "S-MISSING-WINNER": "no substitution", "S-STOPPED": "stale",
    "S-WITHDRAWAL": "contention", "S-OWNER": "no broadcast", "S-INCOMPARABLE": "incomparable",
    "S-SLOTS": "two slots",
    "J-ORDER": "opposite", "J-NO-PROOF": "unapplied", "J-MATCH": "certified survivor", "J-AMBIGUOUS": "ambiguous",
    "J-REPLAY": "replay", "J-MFR-SERIAL": "one resource",
    "J-BINDING-LINK": "neither identity membership nor routes",
    "C-NO-TRANSPORT": "no transport", "C-DERIVED": "lineage", "C-CYCLE": "cycle", "C-REMOTE": "BridgeID",
    "C-DONOR": "donor snapshot", "C-COLLIDE": "does not collide", "C-LOOP": "reflected",
    "C-ROUNDTRIP": "round trip", "C-RESUME-ABA": "both transitions", "C-CROSS-ASSET": "exact revision",
    "C-REMOTE-CUT": "one cut", "C-REMOTE-RESYNC": "explicit resync",
    "N-CUT": "redaction", "N-OWNER": "conflicting owner",
    "L-QUERY": "queried limit", "L-SPEC": "specification's limit",
    "G-POS-SUBJ-CLASS-1": "inverter accepted", "G-NEG-SUBJ-CLASS-1": "undeclared class",
    "G-POS-QUAL-1": "declared qualifier", "G-NEG-QUAL-1": "undeclared qualifier",
    "G-POS-PARAM-OMIT-1": "optional omitted", "G-NEG-PARAM-REPEAT-1": "repeated parameter",
    "G-NEG-PARAM-UNDECLARED-1": "undeclared field", "G-NEG-EVENT-PACK-1": "foreign-pack payload",
    "G-NEG-EVENT-RELATION-1": "foreign-pack relation", "G-POS-RELEASE-1": "false alone",
    "G-NEG-RELEASE-MIXED-1": "mixed case",
}
EXTRA_STEMS = {"N-CUT": ["action effects", "outcome"]}


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate member: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def compare(name, vectors, expected):
    """Return the differences between one vector file and its expectation."""
    errors = []
    if not isinstance(vectors, list):
        return [f"{name}: not an array"]
    seen = {}
    for vector in vectors:
        if not isinstance(vector, dict) or not isinstance(vector.get("id"), str):
            errors.append(f"{name}: vector without an id")
            continue
        if vector["id"] in seen:
            errors.append(f"{name}: duplicate id {vector['id']}")
        seen[vector["id"]] = vector
        if not isinstance(vector.get("explanation"), str):
            errors.append(f"{name}: {vector['id']}: explanation missing")
    errors += [f"{name}: missing id {i}" for i in sorted(set(expected) - set(seen))]
    errors += [f"{name}: unexpected id {i}" for i in sorted(set(seen) - set(expected))]
    for ident in sorted(set(expected) & set(seen)):
        if seen[ident].get("expected") != expected[ident]:
            errors.append(f"{name}: {ident}: expected outcome differs")
    return errors


def secs(text):
    return float(text[:-1])


def normalize_retry(raw):
    out = copy.deepcopy(raw)
    out["Budget"] = max(raw["Budget"], 0)
    initial = secs(raw["InitialDelay"])
    initial = 1.0 if initial <= 0 else initial
    maximum = max(secs(raw["MaxDelay"]), initial)
    jitter = raw["JitterRatio"]
    jitter = 0.2 if jitter == 0 else 0 if jitter < 0 else min(jitter, 0.5)
    out.update(InitialDelay=f"{initial:g}s", MaxDelay=f"{maximum:g}s", JitterRatio=jitter)
    if raw["Persistent"]["Enabled"]:
        p_initial = secs(raw["Persistent"]["InitialDelay"])
        p_initial = 1.0 if p_initial <= 0 else p_initial
        p_maximum = max(secs(raw["Persistent"]["MaxDelay"]), p_initial)
        out["Persistent"].update(InitialDelay=f"{p_initial:g}s", MaxDelay=f"{p_maximum:g}s")
    return out


def digest_key(identity):
    text = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def legacy_id(fields):
    digest = hashlib.sha256(LEGACY_DOMAIN.encode("utf-8"))
    for field in fields:
        digest.update(b"\x00" + field.encode("utf-8"))
    return "resource:" + digest.hexdigest()[:32]


def path_id(fields):
    digest = hashlib.sha256(PATH_DOMAIN.encode("utf-8"))
    for field in fields:
        raw = field.encode("utf-8")
        digest.update(struct.pack(">I", len(raw)) + raw)
    return "resource:" + digest.hexdigest()[:32]


def key_fields(key):
    anchor = key["anchor"]
    head = [key["installation"], key["driver_kind"], key["instance_key"], key["node_kind"], anchor["tag"]]
    if anchor["tag"] == "slot":
        return head + [anchor["parent"], anchor["slot"]]
    return head + [digest_key(anchor["identity"])]


def vary(base, field, value):
    key = copy.deepcopy(base)
    anchor = key["anchor"]
    if field in ("installation", "driver_kind", "instance_key", "node_kind"):
        key[field] = value
    elif field == "parent":
        anchor["parent"] = P2
    elif field == "slot":
        anchor["slot"] = "secondary"
    elif field == "anchor_tag":
        key["anchor"] = {"tag": "key", "identity": IDA}
    else:
        key["anchor"] = {"tag": "key", "identity": IDB}
    return key


def allocation_errors(expected):
    """Recompute every allocation literal from the contract's encoding."""
    errors = []
    slot = expected["I-ALLOC-LEGACY-SLOT"]
    if legacy_id(slot["fields"]) != slot["id"]:
        errors.append("legacy slot id differs from the donor encoding")
    key = expected["I-ALLOC-LEGACY-KEY"]
    if legacy_id([key["kind"], "key", digest_key(key["identity"])]) != key["id"]:
        errors.append("legacy native key id differs from the donor encoding")
    for name in ("I-ALLOC-PATH-SLOT", "I-ALLOC-PATH-KEY"):
        if path_id(key_fields(expected[name]["key"])) != expected[name]["id"]:
            errors.append(f"{name} differs from the path-node encoding")
    pair = expected["I-ALLOC-INJECTIVE"]
    ids = [path_id(pair[side]["fields"]) for side in ("first", "second")]
    if ids != [pair["first"]["id"], pair["second"]["id"]] or ids[0] == ids[1]:
        errors.append("injective pair differs")
    vary_vector = expected["I-ALLOC-VARY"]
    base = {k: v for k, v in vary_vector["base"].items() if k != "id"}
    base_id = path_id(key_fields(base))
    changed = [path_id(key_fields(vary(base, v["field"], v["value"]))) for v in vary_vector["variants"]]
    if base_id != vary_vector["base"]["id"] or changed != [v["id"] for v in vary_vector["variants"]]:
        errors.append("variant ids differ from the path-node encoding")
    if len({base_id, *changed}) != 1 + len(changed):
        errors.append("a key field does not change the id")
    domain = expected["I-ALLOC-DOMAIN"]
    if domain["legacy_id"] != legacy_id(domain["fields"]) or domain["path_node_id"] != path_id(domain["fields"]):
        errors.append("domain vector differs")
    if domain["legacy_id"] == domain["path_node_id"]:
        errors.append("domains collide")
    return errors


def composition_errors(expected):
    """Recompute composition acceptance with the Family page's own row rules."""
    errors = []
    for name, vector in expected.items():
        if not name.startswith("K-COMPOSE-"):
            continue
        row = {"state": "candidate", "reason": "no_producer", "evidence": [], "verification": "not_tested_on_hardware",
               "composition": vector["composition"], "composition_verified": vector["composition_verified"],
               "module": vector["module"], "version": vector["version"]}
        if (family.check_row_state(row) == []) != vector["accepted"]:
            errors.append(f"{name}: acceptance differs from the Family row rules")
    hardware = expected["K-VERIFICATION-HARDWARE"]
    row = {"state": "candidate", "reason": "no_producer", "verification": hardware["verification"],
           "composition": "not_composed", "composition_verified": False,
           "evidence": [{"kind": kind} for kind in hardware["evidence_kinds"]]}
    if (family.check_row_state(row) == []) != hardware["accepted"]:
        errors.append("K-VERIFICATION-HARDWARE: acceptance differs from the Family row rules")
    return errors


def release_errors(structure):
    """Check the kernel vectors named by the structure table against its expectations."""
    vectors = {v["id"]: v for v in read_json(kernel.VECTORS)["vectors"]}
    operations = kernel.operation_metadata()
    errors = []
    for entry in structure:
        ident = entry["id"]
        if not ident.startswith(("K-POS-", "K-NEG-")):
            continue
        expected = entry["expected"]
        result = expected.get("error_id", expected.get("execution_outcome", "accept"))
        vector = vectors.get(ident)
        if vector is None:
            errors.append(f"{ident}: missing kernel release vector")
            continue
        expect = vector["expect"]
        if (expect["result"] != ("accept" if expected["accepted"] else "reject")
                or expect.get("error_id") != expected.get("error_id")
                or expect.get("outcome") != expected.get("execution_outcome")
                or kernel.release_vector_result(vector, operations) != result):
            errors.append(f"{ident}: kernel release result differs from {result}")
    return errors


def executable_errors(files):
    """Recompute the retry, allocation, composition and release outcomes."""
    errors = []
    expected = {k: v for table in EXPECTED.values() for k, v in table.items()}
    errors += allocation_errors(expected) + composition_errors(expected)
    if "structure.json" in files:
        errors += release_errors(files["structure.json"])
    for vector in files.get("composition.json", []):
        if vector.get("id", "").startswith("K-RETRY-"):
            if normalize_retry(vector.get("input", {})) != vector["expected"]["normalized"]:
                errors.append(f"{vector['id']}: normalization differs from the donor rules")
    return errors


QUALITY_HEADING = "### Type: Quality"
KERNEL_REQUIRED = [
    "none of them is by itself a veto on fact admission or on the promotion of an element",
    "validates as promoted when those value-presence requirements hold",
    "`unknown` may retain an observed opaque native symbol and stays native unknown, distinct from a known capability",
    "retains that actual candidate state rather than being suppressed or shown as good",
    "`unsupported`, `rejected` and `withdrawn` candidates have no value",
]
KERNEL_BANS = {
    "unsupported and rejected forbid promotion": "`unsupported` and `rejected` forbid a value and promotion.",
    "unknown cannot be promoted or satisfy a capability":
        "`unknown` may retain an observed opaque native symbol but cannot be promoted or satisfy a capability.",
    "promotion predicate": "`promotion=promoted` requires `qualification=qualified`, `validity` of `good` or"
                           " `suspect`, and `availability` of `available` or `degraded`.",
}


KERNEL_BAN_PARTS = ("forbid a value and promotion", "cannot be promoted or satisfy a capability",
                    "requires `qualification=qualified`")


def quality_section(text):
    start = text.index(QUALITY_HEADING)
    end = text.index("\n## ", start)
    return text[start:end]


def kernel_errors(text):
    """Check the kernel Quality section for both allowed outcomes and no old ban."""
    flat = " ".join(quality_section(text).split())
    errors = [f"kernel Quality statement missing: {rule}" for rule in KERNEL_REQUIRED if rule not in flat]
    errors += [f"kernel Quality ban restored: {name}" for name, ban in KERNEL_BANS.items() if ban in flat]
    errors += [f"kernel Quality ban restored: {part}" for part in KERNEL_BAN_PARTS if part in flat]
    return errors


def stem_errors():
    errors = []
    outcomes = {k: v["outcome"] for table in EXPECTED.values() for k, v in table.items()}
    for ident, stem in STEMS.items():
        if stem not in outcomes.get(ident, ""):
            errors.append(f"{ident}: stem missing from the expected outcome: {stem}")
    for ident, stems in EXTRA_STEMS.items():
        errors += [f"{ident}: stem missing: {s}" for s in stems if s not in outcomes[ident]]
    return errors


def run(directory, kernel_text, page_text):
    errors = stem_errors()
    files = {}
    for name, expected in EXPECTED.items():
        try:
            files[name] = read_json(directory / name)
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")
            continue
        errors += compare(name, files[name], expected)
    if not errors:
        errors += executable_errors(files)
    errors += kernel_errors(kernel_text)
    errors += [f"Family page: {e}" for e in family.check(page_text)]
    return errors


def load(directory):
    return {name: read_json(directory / name) for name in EXPECTED}


def release_mutation_failures():
    vectors = {v["id"]: v for v in read_json(kernel.VECTORS)["vectors"]}
    operations = kernel.operation_metadata()
    escaped = []

    def check_result(vector, expected, label):
        if kernel.release_vector_result(vector, operations) != expected:
            escaped.append(label)

    # Each component of both DefinitionRefs must participate in exact matching.
    for ident in ("K-POS-026", "K-POS-027"):
        for ref_name in ("kind", "rule"):
            for path, replacement in (
                (("pack", "id"), "helianthus.pack.other"),
                (("pack", "version"), "0.0.0"),
                (("id",), "other.definition"),
                (("version",), "0.0.0"),
            ):
                probe = copy.deepcopy(vectors[ident])
                intent = probe["input"] if ident == "K-POS-026" else probe["input"]["intent"]
                ref = intent["kind"] if ref_name == "kind" else intent["expected_effect"]["rule"]
                for segment in path[:-1]:
                    ref = ref[segment]
                ref[path[-1]] = replacement
                check_result(probe, "invalid_value", f"{ident}: {ref_name}.{'.'.join(path)}")

    for label, change in (
        ("wrong field ID", lambda i: i["arguments"][0].update(id="pv.limit.other")),
        ("no argument", lambda i: i["arguments"].clear()),
        ("extra parameter", lambda i: i["arguments"].append(
            {"id": "pv.parameter.other", "value": {"kind": "boolean", "boolean": False}})),
        ("missing rule", lambda i: i["expected_effect"].pop("rule")),
        ("null rule", lambda i: i["expected_effect"].update(rule=None)),
    ):
        probe = copy.deepcopy(vectors["K-POS-026"])
        change(probe["input"])
        check_result(probe, "invalid_value", label)

    set_probe = copy.deepcopy(vectors["K-NEG-070"])
    set_probe["input"]["expected_effect"] = vectors["K-NEG-069"]["input"]["expected_effect"]
    check_result(set_probe, "accept", "numeric set with complete predicate")
    for member in ("fact", "operator", "expected"):
        partial = copy.deepcopy(set_probe)
        partial["input"]["expected_effect"].pop(member)
        check_result(partial, "invalid_value", f"set without {member}")
        probe = copy.deepcopy(vectors["K-POS-026"])
        probe["input"]["expected_effect"][member] = None
        check_result(probe, "invalid_value", f"release with explicit null {member}")
    probe = copy.deepcopy(vectors["K-POS-026"])
    undeclared = next(item for item in operations if "release" not in item)
    probe["input"].update(kind=undeclared["ref"], expected_effect={"rule": undeclared["effect"]})
    probe["input"]["arguments"][0]["id"] = undeclared["argument"]["id"]
    check_result(probe, "invalid_value", "rule-only intent without a release declaration")
    probe = copy.deepcopy(vectors["K-POS-027"])
    probe["input"]["acknowledgement"] = "provisional"
    check_result(probe, "acknowledged_unverified", "provisional acknowledgement")
    probe["input"]["readback"] = None
    check_result(probe, "invalid_outcome", "explicit null readback")
    return escaped


def mutation_failures(files, kernel_text, page_text):
    """Return the mutations that did not make the check fail."""
    escaped = []

    def vectors_with(name, ident, change):
        mutated = copy.deepcopy(files)
        for vector in mutated[name]:
            if vector["id"] == ident:
                change(vector)
        return mutated

    def fails(mutated):
        errors = []
        for name, expected in EXPECTED.items():
            errors += compare(name, mutated[name], expected)
        return bool(errors)

    cases = {
        "S-THREE-PATHS not three paths": vectors_with(
            "sources.json", "S-THREE-PATHS", lambda v: v["expected"].update(outcome="not three paths")),
        "S-OWNER no-broadcast stem in a broadcast sentence": vectors_with(
            "sources.json", "S-OWNER", lambda v: v["expected"].update(
                outcome="the command is routed with no broadcast stem, then broadcast to every reader")),
        "altered value": vectors_with("joins.json", "J-MATCH", lambda v: v["expected"].update(joined=False)),
        "missing member": vectors_with("limits.json", "L-QUERY", lambda v: v["expected"].pop("origin")),
        "altered status": vectors_with("structure.json", "G-POS-QUAL-1", lambda v: v["expected"].update(accepted=False)),
        "altered identity": vectors_with(
            "identity.json", "I-ALLOC-PATH-SLOT", lambda v: v["expected"].update(id="resource:" + "0" * 32)),
    }
    cases["missing id"] = {**files, "limits.json": files["limits.json"][:1]}
    cases["duplicate id"] = {**files, "limits.json": files["limits.json"] + files["limits.json"][:1]}
    escaped += [name for name, mutated in cases.items() if not fails(mutated)]
    if not executable_errors({"composition.json": [dict(v, expected=dict(v["expected"], normalized=policy(9)))
                                                   if v["id"] == "K-RETRY-ZERO" else v
                                                   for v in files["composition.json"]]}):
        escaped.append("retry normalization mutation")
    for name, ban in KERNEL_BANS.items():
        mutated = kernel_text.replace(QUALITY_HEADING, QUALITY_HEADING + "\n\n" + ban + "\n", 1)
        if not kernel_errors(mutated) or family.check(page_text):
            escaped.append(f"kernel ban restored on the kernel alone: {name}")
    return escaped + release_mutation_failures()


def main():
    kernel_text = (ROOT / "api/v1/kernel.md").read_text(encoding="utf-8")
    page_text = (ROOT / "api/v1/family-catalog-v1.md").read_text(encoding="utf-8")
    errors = run(HERE, kernel_text, page_text)
    if not errors:
        errors += [f"mutation not detected: {m}" for m in mutation_failures(load(HERE), kernel_text, page_text)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("contract vectors ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
