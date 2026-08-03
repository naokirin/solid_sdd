package parse_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/parse"
)

func TestChangeBriefImport(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "change-brief.json")
	content := `{
  "version": "1",
  "change_id": "demo-change",
  "summary": "s",
  "goal": "g",
  "in_scope": [{"id": "R1", "text": "Do the thing"}],
  "out_of_scope": [{"id": "X1", "text": "Not this"}],
  "success_criteria": [{"id": "SC1", "text": "It works"}]
}`
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	g := &model.Graph{}
	parse.ChangeBriefs([]string{path}, "/", g)
	if g.NodeByID("demo-change/R1") == nil {
		t.Fatalf("missing requirement node; nodes=%v", ids(g))
	}
	if g.NodeByID("demo-change/SC1") == nil {
		t.Fatalf("missing AC node; nodes=%v", ids(g))
	}
	n := g.NodeByID("demo-change/R1")
	if n.Type != "requirement" || n.Layer != "brief" {
		t.Fatalf("got %+v", n)
	}
}

func ids(g *model.Graph) []string {
	out := make([]string, 0, len(g.Nodes))
	for _, n := range g.Nodes {
		out = append(out, n.ID)
	}
	return out
}
