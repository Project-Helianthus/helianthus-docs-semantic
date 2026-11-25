package al

import "example.test/closure/cross/qb"

const Size = 1

type Alias = qb.Box

func Build() Alias { return Alias{Size: 2} }
