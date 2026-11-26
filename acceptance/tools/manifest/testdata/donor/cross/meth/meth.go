package meth

type Record struct{ V int }

func (r Record) Value() int { return r.V }
