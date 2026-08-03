package validate_test

import (
	"testing"
	"time"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/schema"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/validate"
)

func knowledgeSchema() schema.Schema {
	return schema.Schema{
		NodeTypes: map[string]schema.NodeType{
			"concept":  {Required: []string{"status"}, Statuses: []string{"active", "deprecated"}},
			"policy":   {Required: []string{"status", "scope"}, Statuses: []string{"active", "deprecated"}},
			"decision": {Required: []string{"status"}, Statuses: []string{"active", "deprecated"}},
		},
		EdgeTypes: map[string]schema.EdgeType{
			"mentions":      {From: []string{"policy"}, To: []string{"concept"}},
			"contradicts":   {From: []string{"policy"}, To: []string{"policy"}},
			"deviates_from": {From: []string{"policy"}, To: []string{"policy"}},
			"rationale":     {From: []string{"policy"}, To: []string{"decision"}},
		},
		Rules: []schema.Rule{
			{ID: "IMPLICIT_CONCEPT_USE", Severity: "warn", Assert: "implicit_concept_use"},
			{ID: "UNREFERENCED_KNOWLEDGE", Severity: "warn", Assert: "unreferenced_knowledge"},
			{ID: "CONTRADICTING_POLICIES", Severity: "error", Assert: "contradicting_policies"},
			{ID: "STALE_KNOWLEDGE", Severity: "warn", Assert: "stale_knowledge"},
			{ID: "DEVIATE_WITHOUT_REASON", Severity: "error", Assert: "deviate_without_reason"},
		},
	}
}

func TestKnowledgePhase3(t *testing.T) {
	g := &model.Graph{
		Nodes: []model.Node{
			{ID: "CON-TTL", Type: "concept", Title: "session ttl", Status: "active", Aliases: []string{"セッションTTL"}},
			{ID: "POL-A", Type: "policy", Title: "A", Status: "active", Scope: "org.sec", Body: "Uses セッションTTL here.", VerifiedAt: "2020-01-01"},
			{ID: "POL-B", Type: "policy", Title: "B", Status: "active", Scope: "org.sec", VerifiedAt: "2026-08-01"},
			{ID: "DEC-X", Type: "decision", Title: "x", Status: "active", VerifiedAt: "2026-08-01"},
		},
		Edges: []model.Edge{
			{Type: "contradicts", From: "POL-A", To: "POL-B"},
			{Type: "deviates_from", From: "POL-B", To: "POL-A"}, // no reason
			{Type: "rationale", From: "POL-A", To: "DEC-X"},
		},
	}
	opts := validate.KnowledgeOptions{FreshnessDays: 30, Now: time.Date(2026, 8, 4, 0, 0, 0, 0, time.UTC)}
	vs := validate.All(g, knowledgeSchema(), opts)
	rules := map[string]int{}
	for _, v := range vs {
		rules[v.Rule]++
	}
	if rules["IMPLICIT_CONCEPT_USE"] < 1 {
		t.Fatalf("expected implicit concept, got %v / %+v", rules, vs)
	}
	if rules["CONTRADICTING_POLICIES"] != 1 {
		t.Fatalf("expected contradict, got %v", rules)
	}
	if rules["DEVIATE_WITHOUT_REASON"] != 1 {
		t.Fatalf("expected deviate, got %v", rules)
	}
	if rules["STALE_KNOWLEDGE"] < 1 {
		t.Fatalf("expected stale, got %v", rules)
	}
	if rules["UNREFERENCED_KNOWLEDGE"] < 1 {
		t.Fatalf("expected unreferenced, got %v", rules)
	}
}
