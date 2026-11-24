// Package output is a northbound consumer of the SemReg driver contract.
// StartOutput reads one semantic cut and invokes one scoped operation.
// Timeout zero stays on Invoke. The merged module exports no operation router.
package output

import (
	"context"
	"errors"

	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
)

// Output receives SemanticInput and ScopedOperations and invokes Request.
type Output struct {
	Request driver.OperationRequest
}

// StartOutput captures a cut and calls ScopedOperations.Invoke with Request.
// A zero Timeout does not select InvokeCallBound.
func (o *Output) StartOutput(ctx context.Context, in driver.SemanticInput, ops driver.ScopedOperations) error {
	if in == nil || ops == nil {
		return errors.New("output needs semantic input and scoped operations")
	}
	cut, err := in.Capture(ctx, driver.Filter{})
	if err != nil {
		return err
	}
	if err := cut.Validate(); err != nil {
		return err
	}
	if err := o.Request.Validate(); err != nil {
		return err
	}
	result, err := ops.Invoke(ctx, o.Request)
	if err != nil {
		return err
	}
	return result.Validate()
}
