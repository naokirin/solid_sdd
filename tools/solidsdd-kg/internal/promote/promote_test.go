package promote_test

import (
	"os"
	"path/filepath"
	"strings"
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

func TestApplyNodeTypes(t *testing.T) {
	root := t.TempDir()
	res, err := promote.ApplyNode(root, "knowledge", "decision", "DEC-T", "Title", "", "body")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(res.CreatedPath); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(res.CreatedPath, "decisions") {
		t.Fatalf("path=%s", res.CreatedPath)
	}
}

func TestContractVocabulary(t *testing.T) {
	root := t.TempDir()
	_ = os.MkdirAll(filepath.Join(root, "contracts"), 0o755)
	ocl := `-- sample
context Reservation
context Reservation::reserve(principal: String, sku: String, quantity: Integer, ttlSeconds: Integer): Hold
post UnauthorizedError:
  true
post InsufficientStockError:
  true
`
	if err := os.WriteFile(filepath.Join(root, "contracts", "R.ocl"), []byte(ocl), 0o644); err != nil {
		t.Fatal(err)
	}
	_ = os.MkdirAll(filepath.Join(root, ".solidsdd", "kg"), 0o755)
	cfg := "version: \"1\"\npaths:\n  contracts: contracts\n  openapi: openapi/openapi.yaml\n"
	if err := os.WriteFile(filepath.Join(root, ".solidsdd", "config.yaml"), []byte(cfg), 0o644); err != nil {
		t.Fatal(err)
	}
	g := &model.Graph{Nodes: []model.Node{
		{ID: "CON-NAMED-DOMAIN-ERROR", Type: "concept", Title: "named domain error", Body: "UnauthorizedError InsufficientStockError PreconditionError"},
	}}
	cands := promote.ContractVocabulary(root, g)
	for _, c := range cands {
		if c.Kind != "contract_vocabulary" {
			t.Fatalf("kind=%q", c.Kind)
		}
		for _, id := range c.IDs {
			if id == "UnauthorizedError" || id == "InsufficientStockError" {
				t.Fatalf("should be covered by concept body: %s", id)
			}
		}
	}
	foundHold := false
	for _, c := range cands {
		for _, id := range c.IDs {
			if id == "Hold" {
				foundHold = true
			}
		}
	}
	if !foundHold {
		t.Fatalf("expected Hold suggestion, got %+v", cands)
	}
}
