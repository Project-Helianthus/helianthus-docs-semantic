package alpha

var err error
var name = "package-level"
var store = 0
var alpha = 1
var zone = 2
var out = 3
var record = 4
var items = 5

func Name() string { return name }

func Zones() []int { return nil }

func kept(value string) string { return value }
