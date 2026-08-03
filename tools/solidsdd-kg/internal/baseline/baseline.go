package baseline

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/validate"
)

// File is .solidsdd/kg/baseline.json (FR-213).
type File struct {
	Version    string   `json:"version"`
	UpdatedAt  string   `json:"updated_at"`
	Violations []string `json:"violations"` // fingerprints
}

// Path returns default baseline path under project root.
func Path(projectRoot string) string {
	return filepath.Join(projectRoot, ".solidsdd", "kg", "baseline.json")
}

// Load reads baseline; missing file yields empty baseline.
func Load(path string) (File, error) {
	var f File
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return File{Version: "1", Violations: nil}, nil
		}
		return f, err
	}
	if err := json.Unmarshal(data, &f); err != nil {
		return f, fmt.Errorf("parse baseline %s: %w", path, err)
	}
	if f.Version == "" {
		f.Version = "1"
	}
	return f, nil
}

// Save writes baseline fingerprints.
func Save(path string, violations []validate.Violation) error {
	fps := make([]string, 0, len(violations))
	seen := map[string]struct{}{}
	for _, v := range violations {
		fp := v.Fingerprint()
		if _, ok := seen[fp]; ok {
			continue
		}
		seen[fp] = struct{}{}
		fps = append(fps, fp)
	}
	sort.Strings(fps)
	f := File{
		Version:    "1",
		UpdatedAt:  time.Now().UTC().Format(time.RFC3339),
		Violations: fps,
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(f, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

// Filter returns violations not present in the baseline.
func Filter(base File, violations []validate.Violation) (newOnes, suppressed []validate.Violation) {
	known := map[string]struct{}{}
	for _, fp := range base.Violations {
		known[fp] = struct{}{}
	}
	for _, v := range violations {
		if _, ok := known[v.Fingerprint()]; ok {
			suppressed = append(suppressed, v)
			continue
		}
		newOnes = append(newOnes, v)
	}
	return newOnes, suppressed
}
