package query

import (
	"sort"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

// Direction for impact traversal.
type Direction string

const (
	Out  Direction = "out"
	In   Direction = "in"
	Both Direction = "both"
)

// Hit is one node reached by impact query (FR-301).
type Hit struct {
	ID     string   `json:"id"`
	Type   string   `json:"type"`
	Title  string   `json:"title"`
	Status string   `json:"status"`
	Hops   int      `json:"hops"`
	Via    []string `json:"via,omitempty"`
	Path   []string `json:"path,omitempty"`
}

// Impact walks the graph from start up to maxHops (FR-301; In covers reverse links FR-303).
func Impact(g *model.Graph, start string, dir Direction, maxHops int, includeTypes map[string]bool) []Hit {
	if maxHops < 0 {
		maxHops = 0
	}
	byID := map[string]*model.Node{}
	for i := range g.Nodes {
		byID[g.Nodes[i].ID] = &g.Nodes[i]
	}
	if byID[start] == nil {
		return nil
	}

	outEdges := map[string][]model.Edge{}
	inEdges := map[string][]model.Edge{}
	for _, e := range g.Edges {
		outEdges[e.From] = append(outEdges[e.From], e)
		inEdges[e.To] = append(inEdges[e.To], e)
	}

	type step struct {
		to       string
		edgeType string
	}
	neighbors := func(id string) []step {
		var steps []step
		if dir == Out || dir == Both {
			for _, e := range outEdges[id] {
				steps = append(steps, step{to: e.To, edgeType: e.Type})
			}
		}
		if dir == In || dir == Both {
			for _, e := range inEdges[id] {
				steps = append(steps, step{to: e.From, edgeType: e.Type})
			}
		}
		return steps
	}

	type state struct {
		id   string
		hops int
		via  []string
		path []string
	}
	seen := map[string]int{start: 0}
	var hits []Hit
	queue := []state{{id: start, hops: 0, path: []string{start}}}

	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		if cur.hops > 0 {
			n := byID[cur.id]
			if n != nil && (len(includeTypes) == 0 || includeTypes[n.Type]) {
				hits = append(hits, Hit{
					ID: n.ID, Type: n.Type, Title: n.Title, Status: n.Status,
					Hops: cur.hops, Via: cur.via, Path: cur.path,
				})
			}
		}
		if cur.hops >= maxHops {
			continue
		}
		for _, s := range neighbors(cur.id) {
			if byID[s.to] == nil {
				continue
			}
			nh := cur.hops + 1
			if prev, ok := seen[s.to]; ok && prev <= nh {
				continue
			}
			seen[s.to] = nh
			via := append(append([]string{}, cur.via...), s.edgeType)
			path := append(append([]string{}, cur.path...), s.to)
			queue = append(queue, state{id: s.to, hops: nh, via: via, path: path})
		}
	}

	sort.Slice(hits, func(i, j int) bool {
		if hits[i].Hops != hits[j].Hops {
			return hits[i].Hops < hits[j].Hops
		}
		return hits[i].ID < hits[j].ID
	})
	return hits
}
