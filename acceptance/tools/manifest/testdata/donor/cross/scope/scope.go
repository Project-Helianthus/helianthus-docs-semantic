package scope

var pending = 1

var value = 2

var count = 3

type base struct {
	count int
}

type view = base

func SelectMove(ch chan int) int {
	select {
	case pending := <-ch:
		return pending
	default:
		return pending
	}
}

func ElseMove(items []int) int {
	if value := len(items); value > 1 {
		return value
	} else if value > 0 {
		return value
	} else {
		return value
	}
}

func AliasMove() int {
	held := view{count: 1}
	return held.count
}
