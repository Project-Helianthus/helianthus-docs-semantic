package alpha

import "strings"

type Record struct {
	Name  string
	Zones []int
}

type Store struct {
	items map[string]Record
}

func (store *Store) Put(name string, record Record) {
	store.items[name] = cloneRecord(record)
}

func (store *Store) Get(name string) Record {
	return store.items[name]
}

func cloneRecord(record Record) Record {
	err := error(nil)
	_ = err
	out := Record{Name: strings.TrimSpace(record.Name)}
	for _, zone := range record.Zones {
		out.Zones = append(out.Zones, zone)
	}
	return out
}

func describe(record Record) string {
	return kept(record.Name)
}
