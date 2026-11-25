package md

import . "example.test/closure/cross/mb"

func Dot() int { return Required() }

func DotType(x Box) int { return x.Required() }
