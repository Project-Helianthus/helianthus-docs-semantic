package ue

import "example.org/ext"

type T int

func (T) M() int { return 1 }

func Move() int { return ext.Identity(T(0)).M() }
