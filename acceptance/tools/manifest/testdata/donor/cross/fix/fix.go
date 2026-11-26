package fix

import "example.test/closure/cross/keyed"

const Kept = 1

const (
	First = Kept + iota
	Moved
)

type R struct{}

func (R) Read() int { return 1 }

type S struct{}

func (S) Read() int { return 2 }

func Nested() int {
	var x R
	{
		x := S{}
		_ = x
	}
	return x.Read()
}

func Inner() int {
	var x R
	{
		x := S{}
		return x.Read()
	}
	_ = x
	return 0
}

func LocalKeys() int {
	type Local struct{ Kept int }
	v := Local{Kept: 1}
	return v.Kept
}

func MapKeys() int { return len(keyed.M{Kept: 1}) }

func StructKeys() int { return keyed.S{Kept: 1}.Kept }
