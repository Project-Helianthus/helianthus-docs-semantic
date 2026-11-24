// Package host composes driver factories through the SemReg driver contract.
// It is the host side of that contract: it selects factories, returns the
// first handled early dispatch before configuration planning, and starts each
// planned instance with the session the caller supplies. It does not normalize
// retry policy, resolve a secret, or implement driver.Session.
package host

import (
	"context"

	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/driver"
)

// Bound is one factory and the configuration record the host hands it.
type Bound struct {
	Factory driver.Factory
	Config  driver.Config
}

// Running is one instance the host started from a validated plan.
type Running struct {
	Plan     driver.InstancePlan
	Instance driver.Instance
}

// Result is the host's composition result. Handled means an early dispatcher
// recognized the command, so no factory was planned.
type Result struct {
	Handled  bool
	ExitCode int
	Started  []Running
}

// SessionOpener supplies the session for one plan. The merged module exports
// driver.Session and no constructor for it.
type SessionOpener interface {
	Open(driver.InstancePlan) (driver.Session, error)
}

// Families is every family the bound factories declare, in driver order.
func Families(drivers []Bound) driver.Descriptor {
	var out driver.Descriptor
	for _, d := range drivers {
		out.Families = append(out.Families, d.Factory.Descriptor().Families...)
	}
	return out
}

// Compose runs early dispatch, then plans and starts every returned instance.
// The first dispatcher that handles the command ends the call; factories that
// do not implement driver.EarlyDispatcher are skipped. SecretRef stays inside
// Config and is passed only to that factory's Plan.
func Compose(ctx context.Context, drivers []Bound, sessions SessionOpener, args []string) (Result, error) {
	for _, d := range drivers {
		early, ok := d.Factory.(driver.EarlyDispatcher)
		if !ok {
			continue
		}
		handled, code, err := early.DispatchEarly(ctx, args)
		if !handled {
			continue
		}
		return Result{Handled: true, ExitCode: code}, err
	}
	var started []Running
	for _, d := range drivers {
		plans, err := d.Factory.Plan(d.Config)
		if err != nil {
			return Result{}, err
		}
		for _, plan := range plans {
			if err := plan.Validate(); err != nil {
				return Result{}, err
			}
			session, err := sessions.Open(plan)
			if err != nil {
				return Result{}, err
			}
			instance, err := d.Factory.Construct(ctx, plan)
			if err != nil {
				return Result{}, err
			}
			if err := instance.Start(ctx, session); err != nil {
				return Result{}, err
			}
			started = append(started, Running{Plan: plan, Instance: instance})
		}
	}
	return Result{Started: started}, nil
}
