package pm

type T struct{}

func (t *T) Method() int { return 1 }

func Move(t *T) int { return (*T).Method(t) }
