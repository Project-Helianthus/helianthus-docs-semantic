package main

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/Project-Helianthus/helianthus-ebusgateway/graphql"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/eebusoutput"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semanticoperations"
	eebusruntime "github.com/Project-Helianthus/helianthus-eebusreg"
	"github.com/Project-Helianthus/helianthus-eebusreg/eebusraw"
	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
)

// oracleEEBusRuntime records every remote read the production provider issues against the virtual runtime.
type oracleEEBusRuntime struct {
	*eebusInboundTestRuntime
	step  *string
	calls *[]any
}

func (r *oracleEEBusRuntime) FeaturesGet(ctx context.Context, auth eebusraw.ReadAuthorizationV1, request eebusraw.FeaturesGetRequestV1) (eebusraw.FeaturesGetDataV1, *eebusraw.ErrorV1) {
	data, failure := r.eebusInboundTestRuntime.FeaturesGet(ctx, auth, request)
	*r.calls = append(*r.calls, map[string]any{"step": *r.step, "operation": "FeaturesGet", "request": oracleJSON(request), "data": oracleJSON(data), "error": oracleJSON(failure)})
	return data, failure
}

func (r *oracleEEBusRuntime) FeaturesDataGet(ctx context.Context, auth eebusraw.ReadAuthorizationV1, request eebusraw.FeatureDataGetRequestV1) (eebusraw.FeatureDataGetDataV1, *eebusraw.ErrorV1) {
	data, failure := r.eebusInboundTestRuntime.FeaturesDataGet(ctx, auth, request)
	*r.calls = append(*r.calls, map[string]any{"step": *r.step, "operation": "FeaturesDataGet", "request": oracleJSON(request), "data": oracleJSON(data), "error": oracleJSON(failure)})
	return data, failure
}

func oracleEEBusInbound(t *testing.T) *oracleClasses {
	classes := oracleNormalize()
	runtime := newEEBusInboundTestRuntime(t)
	var calls []any
	step := ""
	provider := newEEBusPromotedSemanticProvider(&eebusRuntimeAdapter{runtime: &oracleEEBusRuntime{eebusInboundTestRuntime: runtime, step: &step, calls: &calls}})
	var previous map[string]string
	observe := func(name string, stimulus string) {
		step = name
		provider.Refresh(context.Background())
		overlay := provider.Overlay()
		encoded := oracleJSON(overlay)
		leaves := map[string]string{}
		oracleLeaves("", encoded, leaves)
		classes.Publications = append(classes.Publications, map[string]any{"step": name, "stimulus": stimulus, "overlay": encoded})
		classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": name, "graphql_overlay": encoded, "filled": eebusInboundFilled(graphql.NewPromotedSemanticProvider(eebusInboundTestBase(), provider.Overlay)), "empty": eebusInboundEmpty(graphql.NewPromotedSemanticProvider(eebusInboundTestBase(), provider.Overlay))})
		if previous != nil {
			if gone := oracleWithdrawn(previous, leaves); len(gone) > 0 {
				classes.Withdrawals = append(classes.Withdrawals, map[string]any{"step": name, "paths": gone})
			}
		}
		previous = leaves
		classes.Outcomes = append(classes.Outcomes, map[string]any{"step": name, "refreshed": true})
	}
	observe("observation", "remote values of the synthetic node")
	runtime.setValue(8, "Measurement", "measurementDescriptionListData", map[string]any{"measurementDescriptionData": []any{map[string]any{
		"measurementId": int64(0), "commodityType": "air", "measurementType": "temperature", "scopeType": "drifted", "unit": "degC",
	}}})
	observe("profile-drift", "outdoor measurement description drifts to another scope")
	runtime.setSnapshot(eebusInboundTestSnapshot(t, eebusruntime.ObservedRuntimeStateV1Degraded))
	observe("runtime-degraded", "the remote runtime snapshot turns degraded")
	for _, call := range calls {
		classes.Acquisitions = append(classes.Acquisitions, call)
	}
	return classes
}

// oracleEEBusOutbound relays one peer request through the pinned output binding, which serves no eeBUS feature.
func oracleEEBusOutbound(t *testing.T) *oracleClasses {
	classes := oracleNormalize()
	binding, err := eebusoutput.NewBinding(eebusoutput.Config{})
	if err != nil {
		t.Fatal(err)
	}
	request := semanticoperations.Request{
		AssetID: "asset:synthetic", BindingID: "binding:synthetic", CapabilityInstanceID: "capability:synthetic",
		Operation:                semreg.DefinitionRef{Pack: semreg.PackRef{ID: "helianthus.pack.synthetic", Version: "1.0.0"}, ID: "synthetic.operation.set", Version: "1.0.0"},
		ExpectedSemanticRevision: "1", ExpectedCapabilityRevision: "1", ExpectedCapabilityInstanceRevision: "1", ExpectedSourceEpochID: "epoch:synthetic", ExpectedDriverGeneration: "1",
	}
	result, relayErr := binding.Relay(context.Background(), request)
	outcome := map[string]any{"step": "peer-request", "request": oracleJSON(request), "result": oracleJSON(result)}
	if relayErr != nil {
		outcome["error"] = relayErr.Error()
		var typed *semanticoperations.Error
		if asErr, ok := relayErr.(*semanticoperations.Error); ok {
			typed = asErr
			outcome["error_code"] = string(typed.Code)
		}
	}
	classes.Outcomes = append(classes.Outcomes, outcome)
	return classes
}

// TestOracleSessionEEBus runs one eeBUS session of the published input and records the six classes.
func TestOracleSessionEEBus(t *testing.T) {
	session := oracleLoadSession(t)
	var classes *oracleClasses
	switch session.Scenario {
	case "inbound-observation-and-withdrawal":
		classes = oracleEEBusInbound(t)
		again := oracleEEBusInbound(t)
		a, _ := json.Marshal(classes)
		b, _ := json.Marshal(again)
		if string(a) != string(b) {
			t.Fatal("two runs of the session differ")
		}
	case "outbound-peer-request":
		classes = oracleEEBusOutbound(t)
	default:
		t.Fatalf("unknown scenario %q", session.Scenario)
	}
	oracleWriteClasses(t, classes)
}
