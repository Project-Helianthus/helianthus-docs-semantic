package hold

type Box struct{}

func Hold() int { return 1 }

func (b Box) Hold() int { return Hold() }
