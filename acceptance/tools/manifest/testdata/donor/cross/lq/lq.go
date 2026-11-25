package lq

import "example.test/closure/cross/qb"

const Size = 1

func Move() int {
	type Local = qb.Box
	return Local{Size: 3}.Size
}
