package ts

type Item struct{}

func Move(x any) int {
	switch Item := x.(type) {
	case Item:
		_ = Item
	}
	return 0
}
