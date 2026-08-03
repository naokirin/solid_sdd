package contextx_test

import (
	"strings"
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/contextx"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

func TestExtractIncludesPolicy(t *testing.T) {
	g := &model.Graph{
		Nodes: []model.Node{
			{ID: "R1", Type: "requirement", Title: "req", Status: "active", Body: "must follow policy"},
			{ID: "POL", Type: "policy", Title: "p", Status: "active", Scope: "org", Body: "Always do X."},
			{ID: "DEC", Type: "decision", Title: "d", Status: "active", Body: "Because Y."},
		},
		Edges: []model.Edge{
			{Type: "derives_from", From: "R1", To: "POL"},
			{Type: "rationale", From: "POL", To: "DEC"},
		},
	}
	md, err := contextx.Extract(g, "R1", contextx.Options{Hops: 2})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(md, "POL") || !strings.Contains(md, "Always do X") {
		t.Fatalf("missing policy body: %s", md)
	}
	if !strings.Contains(md, "DEC") {
		t.Fatalf("missing decision: %s", md)
	}
}

func TestParseBudget(t *testing.T) {
	n, err := contextx.ParseBudget("30k")
	if err != nil || n != 30_000*4 {
		t.Fatalf("got %d %v", n, err)
	}
}
