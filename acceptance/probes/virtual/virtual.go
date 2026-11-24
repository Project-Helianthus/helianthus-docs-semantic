// Package virtual is a transport-free driver against the SemReg driver contract.
// Plan accepts no transport operand. The durable node key is the configured
// installation, driver, instance and slot. Resource ids on the typed link are
// probe literals: the merged module exports no path-node allocator.
package virtual

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"

	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"

	"github.com/Project-Helianthus/helianthus-docs-semantic/acceptance/probes/support"
)

const (
	// Kind is the driver kind this probe registers.
	Kind driver.DriverKind = "driver.virtual"
	// Installation is the configured installation of the durable node key.
	Installation = "installation.probe"
	// Slot is the configured anchor slot of that key.
	Slot = "slot.total"
	// LocalBridge is the bridge of the link's local endpoint.
	LocalBridge driver.BridgeID = "bridge.local"
	// ForeignBridge is the bridge of the link's other endpoint.
	ForeignBridge driver.BridgeID = "bridge.other"
)

// These ids are probe literals. They are not allocator output.
const (
	localResource   v1.ResourceID = "resource:probe-virtual"
	foreignResource v1.ResourceID = "resource:probe-foreign"
)

// Factory is the transport-free driver.
type Factory struct{}

type options struct {
	Installation string `json:"installation"`
	Slot         string `json:"slot"`
}

// Descriptor declares no family. An empty descriptor is valid.
func (Factory) Descriptor() driver.Descriptor { return driver.Descriptor{} }

// Plan decodes the two owned operands and returns one plan with no transport
// when the instance is enabled. A disabled instance returns no plan.
func (Factory) Plan(c driver.Config) ([]driver.InstancePlan, error) {
	if err := rejectTransport(c.Transport); err != nil {
		return nil, err
	}
	if !c.Enabled {
		return nil, nil
	}
	if err := decodeOptions(c.Options); err != nil {
		return nil, err
	}
	return []driver.InstancePlan{{Driver: Kind, Instance: driver.InstanceKey(c.Instance)}}, nil
}

func rejectTransport(raw json.RawMessage) error {
	if len(raw) == 0 || string(raw) == "null" {
		return nil
	}
	return errors.New("virtual driver accepts no transport operand")
}

func decodeOptions(raw json.RawMessage) error {
	if len(raw) == 0 {
		return errors.New("options are required")
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	var opt options
	if err := dec.Decode(&opt); err != nil {
		return err
	}
	if err := dec.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		return errors.New("options have trailing data")
	}
	if opt.Installation != Installation || opt.Slot != Slot {
		return errors.New("options do not name the configured installation and slot")
	}
	return nil
}

// Construct checks the plan and builds the durable key, declared origin and
// typed link this driver would publish. It opens no transport.
func (Factory) Construct(_ context.Context, plan driver.InstancePlan) (driver.Instance, error) {
	if err := plan.Validate(); err != nil {
		return nil, err
	}
	if len(plan.Transports) != 0 || plan.Driver != Kind {
		return nil, errors.New("virtual construct received a transport or another driver")
	}
	instance := &Instance{Plan: plan, Node: nodeKey(plan), Origin: support.Origin(driver.OriginDeclared, "declared-observation")}
	instance.Link = linkClaim()
	if err := instance.Node.Validate(); err != nil {
		return nil, err
	}
	if err := instance.Origin.Validate(); err != nil {
		return nil, err
	}
	if err := instance.Link.Validate(); err != nil {
		return nil, err
	}
	return instance, nil
}

func nodeKey(plan driver.InstancePlan) driver.NodeKey {
	return driver.NodeKey{
		Installation: Installation, Driver: plan.Driver, Instance: plan.Instance,
		Kind: "resource.virtual_node", Anchor: driver.AnchorKey{Slot: Slot},
	}
}

func linkClaim() driver.LinkClaim {
	return driver.LinkClaim{
		Key: driver.LinkKey{
			Type: support.Definition("relation.member"),
			From: driver.NodeRef{Bridge: LocalBridge, ID: localResource},
			To:   driver.NodeRef{Bridge: ForeignBridge, ID: foreignResource},
		},
		Basis: []v1.EvidenceRef{support.Evidence("link-basis")},
	}
}

// Instance is one transport-free virtual driver instance.
type Instance struct {
	Plan    driver.InstancePlan
	Node    driver.NodeKey
	Origin  driver.Origin
	Link    driver.LinkClaim
	started bool
}

// Start checks the formed records and requires the session's semantic input
// and publisher. It does not capture, publish or dial.
func (i *Instance) Start(_ context.Context, s driver.Session) error {
	if i.started {
		return errors.New("virtual instance already started")
	}
	if err := i.Plan.Validate(); err != nil {
		return err
	}
	if len(i.Plan.Transports) != 0 {
		return errors.New("virtual instance has a transport claim")
	}
	if err := i.Node.Validate(); err != nil {
		return err
	}
	if i.Origin.Kind != driver.OriginDeclared {
		return errors.New("virtual observation origin is not declared")
	}
	if err := i.Origin.Validate(); err != nil {
		return err
	}
	if err := i.Link.Validate(); err != nil {
		return err
	}
	if s == nil || s.SemanticInput() == nil || s.Publisher() == nil {
		return errors.New("virtual instance needs semantic input and a publisher")
	}
	i.started = true
	return nil
}

// Started reports whether Start succeeded.
func (i *Instance) Started() bool { return i.started }

// FenceWithdrawal is a no-op. This probe has no generation fence.
func (i *Instance) FenceWithdrawal() {}

// Stop reports a confirmed close. There is no transport to close.
func (i *Instance) Stop(context.Context) driver.CloseReport {
	i.started = false
	return driver.CloseReport{Confirmed: true}
}
