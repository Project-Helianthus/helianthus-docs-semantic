package gm

type T[V any] struct{}

func (t *T[V]) Method() int { return 1 }

func (t T[V]) Value() int { return 2 }

func Move(t *T[int]) int { return (*T[int]).Method(t) }

func Plain(t T[int]) int { return T[int].Value(t) }
