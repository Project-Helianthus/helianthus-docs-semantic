package beta

type Record struct {
	Name string
}

func NewRecord(name string) Record {
	return Record{Name: name}
}

func (record Record) Label() string {
	return record.Name
}
