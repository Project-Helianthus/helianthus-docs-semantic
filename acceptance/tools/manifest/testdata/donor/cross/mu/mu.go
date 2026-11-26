package mu

import "example.test/closure/cross/mb"

type Local struct{}

func (Local) Need() int { return 1 }

func Use(x mb.Box) int { return x.Required() }

func Expr() int { return mb.Box.Required(mb.Box{}) }

func Redeclare(x Local) int {
	x, ok := x, true
	if ok {
		return x.Need()
	}
	return 0
}

func Shadow(x Local) int {
	{
		x, ok := x, true
		_ = ok
		return x.Need()
	}
}
