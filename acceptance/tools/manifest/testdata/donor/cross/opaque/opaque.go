package opaque

import "external.example/unavailable"

type Local struct{}

func (Local) Read() int { return 1 }

func External() int { return unavailable.New().Read() + unavailable.New().Write() }
func Resolved() int { return Local{}.Read() }
