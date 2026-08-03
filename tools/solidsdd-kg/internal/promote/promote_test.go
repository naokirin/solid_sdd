package promote_test

import (
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/promote"
)

func TestDuplicateAndShared(t *testing.T) {
	g := &model.Graph{Nodes: []model.Node{
		{ID: "A", Title: "Session TTL", Body: "abcdefghijklmnopqrstuvwxyz0123456789EXTRA", SourcePath: "a.md"},
		{ID: "B", Title: "session-ttl", Body: "abcdefghijklmnopqrstuvwxyz0123456789EXTRA", SourcePath: "b.md"},
	}}
	dups := promote.DuplicateNodes(g)
	if len(dups) != 1 {
		t.Fatalf("dups=%+v", dups)
	}
	shared := promote.SharedPhrases(g, 20)
	if len(shared) != 1 {
		t.Fatalf("shared=%+v", shared)
	}
}
