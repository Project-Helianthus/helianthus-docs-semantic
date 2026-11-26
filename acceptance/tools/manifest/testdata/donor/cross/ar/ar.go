package ar

type T struct{}

type Alias = T

func (Alias) M() int { return 1 }
