package ptr

import "testing"

func TestPointerWrite(t *testing.T) {
	result := Host()
	host := Host()
	p := &host
	p = &result
	alias := p
	*alias = Moved()
	if result != 1 {
		t.Fatal("moved value")
	}
	if *alias != 1 {
		t.Fatal("indirect value")
	}
	if host != 2 {
		t.Fatal("host value")
	}
}
