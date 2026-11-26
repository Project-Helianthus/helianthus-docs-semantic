package mb

type Box struct{}

func (Box) Required() int { return 1 }

func Required() int { return 2 }

func Sprint() string { return "" }
