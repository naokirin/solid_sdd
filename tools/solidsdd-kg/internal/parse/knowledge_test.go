package parse_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/parse"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/validate"
)

func TestKnowledgeParseAndDangling(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "POL-X.md")
	content := `---
id: POL-X
type: policy
title: Example
status: active
scope: org.test
rationale:
  - MISSING-ID
---

Body.
`
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	n, edges, issue := parse.KnowledgeFile(path)
	if issue != nil {
		t.Fatalf("parse issue: %+v", issue)
	}
	if n.ID != "POL-X" || n.Type != "policy" {
		t.Fatalf("node=%+v", n)
	}
	g := &model.Graph{Nodes: []model.Node{n}, Edges: edges}
	v := validate.DanglingReferences(g)
	if len(v) != 1 || v[0].To != "MISSING-ID" {
		t.Fatalf("expected dangling to MISSING-ID, got %+v", v)
	}
}

func TestKnowledgeNoDangling(t *testing.T) {
	dir := t.TempDir()
	a := filepath.Join(dir, "A.md")
	b := filepath.Join(dir, "B.md")
	if err := os.WriteFile(a, []byte(`---
id: DEC-A
type: decision
title: A
status: active
---
`), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(b, []byte(`---
id: POL-B
type: policy
title: B
status: active
scope: org
rationale: [DEC-A]
---
`), 0o644); err != nil {
		t.Fatal(err)
	}
	g := &model.Graph{}
	parse.KnowledgeDir(dir, g)
	if len(g.Issues) != 0 {
		t.Fatalf("issues: %+v", g.Issues)
	}
	if v := validate.DanglingReferences(g); len(v) != 0 {
		t.Fatalf("unexpected violations: %+v", v)
	}
}
