package clause

const Key = 7

func Pick(ch chan int) int {
	select {
	case <-ch:
		Key := 1
		return Key
	default:
		return Key
	}
}

func PickVar(ch chan int) int {
	select {
	case <-ch:
		var Key = 1
		return Key
	default:
		return Key
	}
}
