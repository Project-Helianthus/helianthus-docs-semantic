package gq

import "example.test/closure/cross/gr"

const Key = 1

func Move() int { return gr.Record[int]{Key: 2}.Value }
