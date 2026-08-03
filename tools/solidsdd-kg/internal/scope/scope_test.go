package scope_test

import (
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/scope"
)

func TestChainAndResolve(t *testing.T) {
	ch := scope.Chain("org.solid_sdd.kg")
	if len(ch) != 3 || ch[0] != "org.solid_sdd.kg" || ch[2] != "org" {
		t.Fatalf("chain=%v", ch)
	}
	if !scope.Covers("org.solid_sdd", "org.solid_sdd.kg") {
		t.Fatal("expected cover")
	}
	if scope.Covers("org.other", "org.solid_sdd.kg") {
		t.Fatal("should not cover")
	}

	g := &model.Graph{Nodes: []model.Node{
		{ID: "POL-ORG", Type: "policy", Title: "org", Status: "active", Scope: "org"},
		{ID: "POL-KG", Type: "policy", Title: "kg", Status: "active", Scope: "org.solid_sdd"},
		{ID: "POL-OTHER", Type: "policy", Title: "x", Status: "active", Scope: "org.other"},
	}}
	pols := scope.ResolvePolicies(g, "org.solid_sdd.kg")
	if len(pols) != 2 || pols[0].ID != "POL-KG" || pols[1].ID != "POL-ORG" {
		t.Fatalf("pols=%+v", pols)
	}
}
