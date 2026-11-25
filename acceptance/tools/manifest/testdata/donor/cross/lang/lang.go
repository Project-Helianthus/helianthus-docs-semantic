package lang

const Bound = 1

const T = 2

const local = 3

type Array [Bound + 1]int

type Generic[T any] struct{ item T }

func Range() int {
	n := 0
	for _, local := range []int{1, 2} {
		n += local
	}
	return n
}

type Holder struct{}

func (Holder) Helper() int { return 1 }

type Plain struct{ Helper int }

func Call(h Holder) int { return h.Helper() }

func Field(p Plain) int { return p.Helper }
