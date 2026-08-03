package query_test

import (
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/query"
)

func TestImpactOutAndIn(t *testing.T) {
	g := &model.Graph{
		Nodes: []model.Node{
			{ID: "A", Type: "policy", Title: "a", Status: "active"},
			{ID: "B", Type: "decision", Title: "b", Status: "active"},
			{ID: "C", Type: "requirement", Title: "c", Status: "active"},
		},
		Edges: []model.Edge{
			{Type: "rationale", From: "A", To: "B"},
			{Type: "derives_from", From: "C", To: "A"},
		},
	}
	out := query.Impact(g, "A", query.Out, 2, nil)
	if len(out) != 1 || out[0].ID != "B" {
		t.Fatalf("out=%+v", out)
	}
	in := query.Impact(g, "A", query.In, 2, nil)
	if len(in) != 1 || in[0].ID != "C" {
		t.Fatalf("in=%+v", in)
	}
	both := query.Impact(g, "A", query.Both, 2, nil)
	if len(both) != 2 {
		t.Fatalf("both=%+v", both)
	}
}
