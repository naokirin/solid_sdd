package build

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/config"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/parse"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/schema"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/store"
)

// Result is a full build outcome.
type Result struct {
	Graph  *model.Graph
	Schema schema.Schema
	DBPath string
}

// Full parses all sources and writes the derived SQLite index.
func Full(cfg config.Config) (*Result, error) {
	sch, err := schema.Load(cfg.SchemaFile())
	if err != nil {
		return nil, fmt.Errorf("load schema: %w", err)
	}

	g := &model.Graph{}

	for _, dir := range cfg.KnowledgeDirs {
		abs := cfg.Abs(dir)
		if st, err := os.Stat(abs); err != nil || !st.IsDir() {
			if err != nil && !os.IsNotExist(err) {
				g.Issues = append(g.Issues, model.ParseIssue{Path: abs, Line: 1, Message: err.Error()})
			}
			continue
		}
		parse.KnowledgeDir(abs, g)
	}

	briefPaths, err := expandGlob(cfg.ProjectRoot, cfg.BriefGlob)
	if err != nil {
		return nil, err
	}
	parse.ChangeBriefs(briefPaths, cfg.BriefIDSeparator, g)

	featurePaths, err := expandGlob(cfg.ProjectRoot, cfg.FeatureGlob)
	if err != nil {
		return nil, err
	}
	parse.Features(featurePaths, g)

	for _, dir := range cfg.SpecDirs {
		abs := cfg.Abs(dir)
		_ = filepath.WalkDir(abs, func(path string, d os.DirEntry, err error) error {
			if err != nil || d.IsDir() {
				return nil
			}
			if filepath.Ext(path) == ".md" {
				parse.SpecFile(path, g)
			}
			return nil
		})
	}

	for _, lf := range cfg.LinksFiles {
		parse.LinksFile(cfg.Abs(lf), g)
	}

	dbPath := cfg.DBPath()
	db, err := store.Open(dbPath)
	if err != nil {
		return nil, err
	}
	defer db.Close()
	if err := store.WriteGraph(db, g); err != nil {
		return nil, err
	}

	return &Result{Graph: g, Schema: sch, DBPath: dbPath}, nil
}

// expandGlob supports "*", "?", and "**" relative to root.
func expandGlob(root, pattern string) ([]string, error) {
	if pattern == "" {
		return nil, nil
	}
	pattern = filepath.ToSlash(pattern)
	if !strings.Contains(pattern, "**") {
		matches, err := filepath.Glob(filepath.Join(root, filepath.FromSlash(pattern)))
		return matches, err
	}
	parts := strings.Split(pattern, "**")
	prefix := strings.TrimSuffix(parts[0], "/")
	suffix := ""
	if len(parts) > 1 {
		suffix = strings.TrimPrefix(parts[1], "/")
	}
	searchRoot := root
	if prefix != "" {
		searchRoot = filepath.Join(root, filepath.FromSlash(prefix))
	}
	var out []string
	err := filepath.WalkDir(searchRoot, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil || d.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(searchRoot, path)
		if err != nil {
			return nil
		}
		rel = filepath.ToSlash(rel)
		if suffix == "" {
			out = append(out, path)
			return nil
		}
		ok, err := filepath.Match(suffix, rel)
		if err != nil {
			return nil
		}
		// also allow match on basename when suffix is like "*.feature"
		if !ok {
			ok, _ = filepath.Match(suffix, filepath.Base(path))
		}
		// suffix may be "**/*.feature" residual like "/*.feature" after split — handle "*.feature"
		if !ok && strings.Contains(suffix, "/") {
			ok, _ = filepath.Match(filepath.Base(suffix), filepath.Base(path))
		}
		if ok {
			out = append(out, path)
		}
		return nil
	})
	return out, err
}
