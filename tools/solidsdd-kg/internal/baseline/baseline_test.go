package baseline_test

import (
	"path/filepath"
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/baseline"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/validate"
)

func TestBaselineFilterAndSave(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "baseline.json")
	vs := []validate.Violation{
		{Rule: "REQ_MUST_HAVE_IMPL", Node: "R1", Message: "missing", Severity: "warn"},
		{Rule: "NO_DANGLING_REFS", From: "A", To: "B", Message: "dangling", Severity: "error"},
	}
	if err := baseline.Save(path, vs[:1]); err != nil {
		t.Fatal(err)
	}
	base, err := baseline.Load(path)
	if err != nil {
		t.Fatal(err)
	}
	newOnes, suppressed := baseline.Filter(base, vs)
	if len(suppressed) != 1 || len(newOnes) != 1 {
		t.Fatalf("new=%d suppressed=%d", len(newOnes), len(suppressed))
	}
	if newOnes[0].Rule != "NO_DANGLING_REFS" {
		t.Fatalf("got %+v", newOnes)
	}
}
