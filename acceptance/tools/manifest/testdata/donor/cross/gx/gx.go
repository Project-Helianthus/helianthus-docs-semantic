package gx

import m `example.test/closure/cross/qt`

type Box[T any] struct{ v T }

func (b *Box[T]) Put(v T) { b.v = v }

func (b Box[T]) Get() T { return b.v }

func Exprs() int {
	put := (*Box[int]).Put
	get := Box[int].Get
	var b Box[int]
	put(&b, 1)
	_ = m.T.M(m.T{})
	return get(b)
}
