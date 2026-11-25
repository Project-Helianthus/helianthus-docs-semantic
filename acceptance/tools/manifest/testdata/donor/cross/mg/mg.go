package mg

const T = 1

const X = 2

type Box[T any] struct{ item T }

func (b Box[T]) Pass(x T) T { return x }

type R struct{ X int }

func Lits() []*R { return []*R{{X: 1}} }
