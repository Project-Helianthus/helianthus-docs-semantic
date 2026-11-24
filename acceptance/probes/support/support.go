// Package support builds the small SemReg values the contract probes share.
// It mints nothing: resource ids here are probe literals, and digests name
// those literals only so EvidenceRef and CutRef can validate.
package support

import (
	"crypto/sha256"
	"encoding/hex"
	"time"

	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/graph"
)

// Digest is sha256 over label, in the module's digest form.
func Digest(label string) v1.Digest {
	sum := sha256.Sum256([]byte(label))
	return v1.Digest("sha256:" + hex.EncodeToString(sum[:]))
}

// Evidence is one public evidence reference for label.
func Evidence(label string) v1.EvidenceRef {
	return v1.EvidenceRef{
		Owner: "owner.probe", Kind: "evidence.probe", Digest: Digest(label),
		Contract: "probe.evidence/v1", Access: v1.EvidenceAccessPublic, Redaction: v1.RedactionNone,
	}
}

// Definition is a pack.test definition id at version 1.0.0.
func Definition(id string) v1.DefinitionRef {
	return v1.DefinitionRef{
		Pack:    v1.PackRef{ID: "pack.test", Version: "1.0.0"},
		ID:      v1.DefinitionID(id),
		Version: "1.0.0",
	}
}

// Node is a bridge and resource id pair.
func Node(bridge, id string) driver.NodeRef {
	return driver.NodeRef{Bridge: driver.BridgeID(bridge), ID: v1.ResourceID(id)}
}

// Origin is a validated-shape origin carrying one evidence reference.
func Origin(kind driver.OriginKind, label string) driver.Origin {
	return driver.Origin{Kind: kind, Evidence: []v1.EvidenceRef{Evidence(label)}}
}

// Cut is a semantic cut whose id validates. It carries no snapshot.
func Cut(label string) driver.SemanticCut {
	return driver.SemanticCut{Ref: graph.CutRef{CutID: Digest(label), Completeness: graph.CutComplete}}
}

// OperationRequest is one closed request for operation.set_sample.
// The boolean argument is a fresh value on every call.
func OperationRequest(timeout time.Duration) driver.OperationRequest {
	value := true
	return driver.OperationRequest{
		AssetID: "asset:probe", BindingID: "binding:probe", CapabilityInstanceID: "capability:probe",
		Operation:                          Definition("operation.set_sample"),
		Arguments:                          []v1.TypedField{{ID: "field.enabled", Value: v1.Value{Kind: v1.ValueBoolean, Boolean: &value}}},
		ExpectedSemanticRevision:           "1",
		ExpectedCapabilityRevision:         "1",
		ExpectedCapabilityInstanceRevision: "1",
		ExpectedDriverGeneration:           "1",
		ExpectedSourceEpochID:              "epoch:probe",
		Preconditions:                      nil,
		Timeout:                            timeout,
	}
}
