package config_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/config"
)

func TestLoadDefaultsWithoutConfigs(t *testing.T) {
	dir := t.TempDir()
	cfg, err := config.Load(dir, "")
	if err != nil {
		t.Fatal(err)
	}
	if cfg.BriefGlob != ".solidsdd/changes/*/change-brief.json" {
		t.Fatalf("brief_glob=%q", cfg.BriefGlob)
	}
	if cfg.FeatureGlob != "requirements/**/*.feature" {
		t.Fatalf("feature_glob=%q", cfg.FeatureGlob)
	}
	if cfg.KgDir != ".solidsdd/kg" {
		t.Fatalf("kg=%q", cfg.KgDir)
	}
	if cfg.BaselineFile() != filepath.Join(dir, ".solidsdd", "kg", "baseline.json") {
		t.Fatalf("baseline=%q", cfg.BaselineFile())
	}
}

func TestProjectConfigOverridesPaths(t *testing.T) {
	dir := t.TempDir()
	sdd := filepath.Join(dir, ".solidsdd")
	if err := os.MkdirAll(sdd, 0o755); err != nil {
		t.Fatal(err)
	}
	body := "version: \"1\"\npaths:\n  changes: alt/changes\n  knowledge:\n    - docs/knowledge\n  cache: .cache/sdd\n  requirements_glob: specs/**/*.feature\n  kg: .solidsdd/kg\n"
	if err := os.WriteFile(filepath.Join(sdd, "config.yaml"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	cfg, err := config.Load(dir, "")
	if err != nil {
		t.Fatal(err)
	}
	if cfg.BriefGlob != "alt/changes/*/change-brief.json" {
		t.Fatalf("brief_glob=%q", cfg.BriefGlob)
	}
	if cfg.FeatureGlob != "specs/**/*.feature" {
		t.Fatalf("feature_glob=%q", cfg.FeatureGlob)
	}
	if len(cfg.KnowledgeDirs) != 1 || cfg.KnowledgeDirs[0] != "docs/knowledge" {
		t.Fatalf("knowledge=%v", cfg.KnowledgeDirs)
	}
	if cfg.CacheDir != ".cache/sdd" {
		t.Fatalf("cache=%q", cfg.CacheDir)
	}
	if cfg.SchemaPath != ".solidsdd/kg/schema.yaml" {
		t.Fatalf("schema=%q", cfg.SchemaPath)
	}
}

func TestKgConfigOverlaysProject(t *testing.T) {
	dir := t.TempDir()
	sdd := filepath.Join(dir, ".solidsdd")
	kg := filepath.Join(sdd, "kg")
	if err := os.MkdirAll(kg, 0o755); err != nil {
		t.Fatal(err)
	}
	proj := "version: \"1\"\npaths:\n  changes: from-project/changes\n  requirements_glob: from-project/**/*.feature\n"
	if err := os.WriteFile(filepath.Join(sdd, "config.yaml"), []byte(proj), 0o644); err != nil {
		t.Fatal(err)
	}
	kgBody := "brief_glob: from-kg/*/change-brief.json\nfreshness_days: 30\n"
	if err := os.WriteFile(filepath.Join(kg, "config.yaml"), []byte(kgBody), 0o644); err != nil {
		t.Fatal(err)
	}
	cfg, err := config.Load(dir, "")
	if err != nil {
		t.Fatal(err)
	}
	if cfg.BriefGlob != "from-kg/*/change-brief.json" {
		t.Fatalf("brief_glob=%q (kg should overlay)", cfg.BriefGlob)
	}
	if cfg.FeatureGlob != "from-project/**/*.feature" {
		t.Fatalf("feature_glob=%q", cfg.FeatureGlob)
	}
	if cfg.FreshnessDays != 30 {
		t.Fatalf("freshness=%d", cfg.FreshnessDays)
	}
}

func TestSolidsddMismatch(t *testing.T) {
	dir := t.TempDir()
	sdd := filepath.Join(dir, ".solidsdd")
	if err := os.MkdirAll(sdd, 0o755); err != nil {
		t.Fatal(err)
	}
	body := "version: \"1\"\npaths:\n  solidsdd: other\n"
	if err := os.WriteFile(filepath.Join(sdd, "config.yaml"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	_, err := config.Load(dir, "")
	if err == nil {
		t.Fatal("expected mismatch error")
	}
}
