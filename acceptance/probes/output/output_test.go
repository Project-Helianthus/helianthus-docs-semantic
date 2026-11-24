package output

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

	v1 "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/graph"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/operation"

	"github.com/Project-Helianthus/helianthus-docs-semantic/acceptance/probes/support"
)

func TestStartOutputCapturesAndInvokes(t *testing.T) {
	var _ driver.SemanticOutput = (*Output)(nil)
	input := &cutInput{cut: support.Cut("cut-probe")}
	ops := &recordingOps{}
	out := &Output{Request: support.OperationRequest(time.Second)}
	if err := out.StartOutput(context.Background(), input, ops); err != nil {
		t.Fatal(err)
	}
	if !input.captured || len(ops.invoked) != 1 || len(ops.callBound) != 0 {
		t.Fatalf("captured=%v invoke=%d callbound=%d", input.captured, len(ops.invoked), len(ops.callBound))
	}
	if !reflect.DeepEqual(ops.invoked[0], out.Request) {
		t.Fatalf("invoked = %+v", ops.invoked[0])
	}
	if err := input.filter.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestZeroTimeoutStaysOnInvoke(t *testing.T) {
	input := &cutInput{cut: support.Cut("cut-probe")}
	ops := &recordingOps{}
	out := &Output{Request: support.OperationRequest(0)}
	if err := out.StartOutput(context.Background(), input, ops); err != nil {
		t.Fatal(err)
	}
	if len(ops.invoked) != 1 || ops.invoked[0].Timeout != 0 || len(ops.callBound) != 0 {
		t.Fatalf("invoke=%d timeout=%s callbound=%d", len(ops.invoked), ops.invoked[0].Timeout, len(ops.callBound))
	}
}

func TestInvalidCutDoesNotInvoke(t *testing.T) {
	ops := &recordingOps{}
	out := &Output{Request: support.OperationRequest(time.Second)}
	if err := out.StartOutput(context.Background(), &cutInput{}, ops); err == nil || len(ops.invoked) != 0 {
		t.Fatalf("err=%v invoked=%d", err, len(ops.invoked))
	}
}

func TestUnattemptedCompoundStepCarriesNoDelivery(t *testing.T) {
	if err := (driver.CompoundStep{Point: "point.one"}).Validate(); err != nil {
		t.Fatal(err)
	}
	if err := (driver.CompoundStep{Point: "point.one", Delivery: operation.DeliverySent}).Validate(); err == nil {
		t.Fatal("accepted delivery on a step that was not attempted")
	}
}

type cutInput struct {
	cut      driver.SemanticCut
	filter   driver.Filter
	captured bool
}

func (c *cutInput) Capture(_ context.Context, f driver.Filter) (driver.SemanticCut, error) {
	c.filter = f
	c.captured = true
	return c.cut, nil
}

func (c *cutInput) Resume(context.Context, driver.Cursor, driver.Filter) (driver.Changes, error) {
	return driver.Changes{}, errors.New("the merged module exports no resume runtime")
}

func (c *cutInput) RetrieveLens(context.Context, graph.CutRef, graph.LensRequest) (graph.LensResult, error) {
	return graph.LensResult{}, errors.New("the merged module exports no session lens runtime")
}

func (c *cutInput) SumMembers(context.Context, graph.CutRef, graph.LensRequest, v1.DefinitionRef, v1.ResourceID) (graph.MemberSum, error) {
	return graph.MemberSum{}, errors.New("the merged module exports no session sum runtime")
}

type recordingOps struct {
	invoked   []driver.OperationRequest
	callBound []driver.OperationRequest
}

func (o *recordingOps) Invoke(_ context.Context, r driver.OperationRequest) (driver.OperationResult, error) {
	if err := r.Validate(); err != nil {
		return driver.OperationResult{}, err
	}
	o.invoked = append(o.invoked, r)
	return driver.OperationResult{Status: "accepted"}, nil
}

func (o *recordingOps) InvokeCallBound(_ context.Context, r driver.OperationRequest) (driver.OperationResult, error) {
	o.callBound = append(o.callBound, r)
	return driver.OperationResult{}, errors.New("call-bound invocation has no router in the merged module")
}
