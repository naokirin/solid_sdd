package validate_test

import (
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/schema"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/validate"
)

func testSchema() schema.Schema {
	return schema.Schema{
		NodeTypes: map[string]schema.NodeType{
			"requirement": {Required: []string{"status"}, Statuses: []string{"draft", "active", "deprecated"}},
			"code":        {Required: []string{"status"}, Statuses: []string{"draft", "active", "deprecated"}},
			"test":        {Required: []string{"status"}, Statuses: []string{"draft", "active", "deprecated"}},
			"task":        {Required: []string{"status"}, Statuses: []string{"draft", "active", "deprecated"}},
			"policy":      {Required: []string{"status", "scope"}, Statuses: []string{"draft", "active", "deprecated"}},
			"decision":    {Required: []string{"status"}, Statuses: []string{"draft", "active", "deprecated"}},
		},
		EdgeTypes: map[string]schema.EdgeType{
			"implements": {From: []string{"code"}, To: []string{"requirement"}},
			"verifies":   {From: []string{"test"}, To: []string{"requirement"}},
			"rationale":  {From: []string{"policy"}, To: []string{"decision"}},
		},
		Rules: []schema.Rule{
			{ID: "REQ_MUST_HAVE_IMPL", Severity: "warn", When: map[string]any{"type": "requirement", "status": "active"}, Assert: "has_incoming(implements)"},
			{ID: "REQ_MUST_HAVE_VERIFY", Severity: "warn", When: map[string]any{"type": "requirement", "status": "active"}, Assert: "has_incoming(verifies)"},
			{ID: "ORPHAN_CODE_OR_TASK", Severity: "warn", Assert: "orphan_code_or_task"},
			{ID: "NO_ACTIVE_REFS_TO_DEPRECATED", Severity: "error", Assert: "no_active_refs_to_deprecated"},
		},
	}
}

func TestCoverageAndDeprecated(t *testing.T) {
	g := &model.Graph{
		Nodes: []model.Node{
			{ID: "R1", Type: "requirement", Title: "r", Status: "active"},
			{ID: "CODE-ORPHAN", Type: "code", Title: "c", Status: "active"},
			{ID: "POL", Type: "policy", Title: "p", Status: "active", Scope: "org"},
			{ID: "OLD", Type: "decision", Title: "old", Status: "deprecated"},
		},
		Edges: []model.Edge{
			{Type: "rationale", From: "POL", To: "OLD"},
		},
	}
	vs := validate.All(g, testSchema())
	rules := map[string]int{}
	for _, v := range vs {
		rules[v.Rule]++
	}
	if rules["REQ_MUST_HAVE_IMPL"] != 1 {
		t.Fatalf("expected REQ_MUST_HAVE_IMPL, got %v", rules)
	}
	if rules["REQ_MUST_HAVE_VERIFY"] != 1 {
		t.Fatalf("expected REQ_MUST_HAVE_VERIFY, got %v", rules)
	}
	if rules["ORPHAN_CODE_OR_TASK"] != 1 {
		t.Fatalf("expected orphan code, got %v", rules)
	}
	if rules["NO_ACTIVE_REFS_TO_DEPRECATED"] != 1 {
		t.Fatalf("expected deprecated ref, got %v", rules)
	}
}

func TestSatisfiedCoverage(t *testing.T) {
	g := &model.Graph{
		Nodes: []model.Node{
			{ID: "R1", Type: "requirement", Title: "r", Status: "active"},
			{ID: "C1", Type: "code", Title: "c", Status: "active"},
			{ID: "T1", Type: "test", Title: "t", Status: "active"},
		},
		Edges: []model.Edge{
			{Type: "implements", From: "C1", To: "R1"},
			{Type: "verifies", From: "T1", To: "R1"},
		},
	}
	vs := validate.All(g, testSchema())
	for _, v := range vs {
		if v.Rule == "REQ_MUST_HAVE_IMPL" || v.Rule == "REQ_MUST_HAVE_VERIFY" || v.Rule == "ORPHAN_CODE_OR_TASK" {
			t.Fatalf("unexpected %s: %s", v.Rule, v.Message)
		}
	}
}

func TestFingerprintStable(t *testing.T) {
	v := validate.Violation{Rule: "R", Node: "N", Message: "m"}
	if v.Fingerprint() != "R|N|||m" {
		t.Fatalf("fp=%q", v.Fingerprint())
	}
}
