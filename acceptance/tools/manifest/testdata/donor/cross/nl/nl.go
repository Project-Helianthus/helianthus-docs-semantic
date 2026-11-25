package nl

const K = "k"

type Item struct{ Count int }

func Count() int { return 1 }

func Maps() int { return len([]map[string]Item{{K: Item{}}}) }

func Fields() int { return len([][]Item{{{Count: 1}}}) }
