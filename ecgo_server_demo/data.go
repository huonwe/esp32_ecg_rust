package main

import (
	"sync"

	"gonum.org/v1/plot"
	"gonum.org/v1/plot/plotter"
	"gonum.org/v1/plot/vg"
)

type EcgQueue struct {
	lock    sync.RWMutex
	items   []uint16
	max_len int
}

func NewEcgQueue(max_len int) *EcgQueue {
	q := EcgQueue{}
	q.items = []uint16{}
	q.max_len = max_len
	return &q
}

func (q *EcgQueue) Enqueue(t uint16) {
	q.lock.Lock()
	if len(q.items) >= q.max_len {
		q.items = q.items[1:len(q.items)]
	}
	q.items = append(q.items, t)
	q.lock.Unlock()
}

func (q *EcgQueue) Dequeue() uint16 {
	q.lock.Lock()
	item := q.items[0]
	q.items = q.items[1:len(q.items)]
	q.lock.Unlock()
	return item
}

func (q *EcgQueue) Plot() {
	p := plot.New()
	p.X.Label.Text = "time"
	p.Y.Label.Text = "v"
	p.Y.Max = 3200
	p.Y.Min = 0
	pts := make(plotter.XYs, len(q.items))
	for i := range pts {
		pts[i].X = float64(i) / 500
		pts[i].Y = float64(q.items[i])

	}
	l, _ := plotter.NewLine(pts)
	l.LineStyle.Width = vg.Points(1)
	l.LineStyle.Dashes = []vg.Length{vg.Points(1), vg.Points(1)}
	p.Legend.Add("line", l)
	p.Add(l)
	// err := plotutil.AddLinePoints(p, "ecg", pts)
	// if err != nil {
	// 	panic(err)
	// }
	if err := p.Save(6*vg.Inch, 3*vg.Inch, "points.png"); err != nil {
		panic(err)
	}

}
