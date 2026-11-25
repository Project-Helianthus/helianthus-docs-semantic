package sig

type T struct{}

func Move(T T) T {
	return T
}

type Reader interface {
	Read() (out int)
}

var out = 1

func Keep() int { return out }
