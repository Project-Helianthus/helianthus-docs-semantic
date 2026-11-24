// Package remote keeps a remote bridge identity as a local record.
// NodeRef is the pair (Bridge, ID). Provenance is the driver's Origin and its
// evidence. The merged module exports no remote factory, authenticator or pager.
package remote

import (
	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
)

// Local is one remote node under local ownership: the original bridge pair
// and a copy of its provenance.
type Local struct {
	Ref        driver.NodeRef
	Provenance driver.Origin
}

// Preserve copies a validated bridge pair and its provenance.
// Discovery is not an argument: NodeRef has no discovery field.
func Preserve(ref driver.NodeRef, provenance driver.Origin) (Local, error) {
	if err := ref.Validate(); err != nil {
		return Local{}, err
	}
	if err := provenance.Validate(); err != nil {
		return Local{}, err
	}
	evidence := make([]v1.EvidenceRef, len(provenance.Evidence))
	copy(evidence, provenance.Evidence)
	return Local{
		Ref:        driver.NodeRef{Bridge: ref.Bridge, ID: ref.ID},
		Provenance: driver.Origin{Kind: provenance.Kind, Evidence: evidence},
	}, nil
}
