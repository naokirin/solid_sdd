package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// Config is .solidsdd/kg/config.yaml
type Config struct {
	Root              string   `yaml:"root"`
	KnowledgeDirs     []string `yaml:"knowledge_dirs"`
	BriefGlob         string   `yaml:"brief_glob"`
	FeatureGlob       string   `yaml:"feature_glob"`
	SpecDirs          []string `yaml:"spec_dirs"`
	LinksFiles        []string `yaml:"links_files"`
	CacheDir          string   `yaml:"cache_dir"`
	DBFilename        string   `yaml:"db_filename"`
	BriefIDSeparator  string   `yaml:"brief_id_separator"`
	SchemaPath        string   `yaml:"schema_path"`
	ProjectRoot       string   `yaml:"-"`
	ConfigPath        string   `yaml:"-"`
}

// Default returns Phase 1 defaults.
func Default() Config {
	return Config{
		Root:             ".",
		KnowledgeDirs:    []string{"knowledge"},
		BriefGlob:        ".solidsdd/changes/*/change-brief.json",
		FeatureGlob:      "requirements/**/*.feature",
		SpecDirs:         nil,
		LinksFiles:       []string{".solidsdd/kg/links.yaml"},
		CacheDir:         ".solidsdd-cache",
		DBFilename:       "kg.db",
		BriefIDSeparator: "/",
		SchemaPath:       ".solidsdd/kg/schema.yaml",
	}
}

// Load reads config from path (or default location under projectRoot).
func Load(projectRoot, configPath string) (Config, error) {
	cfg := Default()
	if projectRoot == "" {
		projectRoot = "."
	}
	absRoot, err := filepath.Abs(projectRoot)
	if err != nil {
		return cfg, err
	}
	cfg.ProjectRoot = absRoot

	if configPath == "" {
		configPath = filepath.Join(absRoot, ".solidsdd", "kg", "config.yaml")
	}
	cfg.ConfigPath = configPath

	data, err := os.ReadFile(configPath)
	if err != nil {
		if os.IsNotExist(err) {
			return cfg, nil
		}
		return cfg, err
	}
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return cfg, fmt.Errorf("parse config %s: %w", configPath, err)
	}
	cfg.ProjectRoot = absRoot
	cfg.ConfigPath = configPath
	if cfg.BriefIDSeparator == "" {
		cfg.BriefIDSeparator = "/"
	}
	if cfg.CacheDir == "" {
		cfg.CacheDir = ".solidsdd-cache"
	}
	if cfg.DBFilename == "" {
		cfg.DBFilename = "kg.db"
	}
	if cfg.SchemaPath == "" {
		cfg.SchemaPath = ".solidsdd/kg/schema.yaml"
	}
	if len(cfg.KnowledgeDirs) == 0 {
		cfg.KnowledgeDirs = []string{"knowledge"}
	}
	return cfg, nil
}

// Abs returns path joined with project root when relative.
func (c Config) Abs(p string) string {
	if filepath.IsAbs(p) {
		return p
	}
	return filepath.Join(c.ProjectRoot, p)
}

// DBPath is the derived SQLite path.
func (c Config) DBPath() string {
	return c.Abs(filepath.Join(c.CacheDir, c.DBFilename))
}

// SchemaFile is the schema yaml path.
func (c Config) SchemaFile() string {
	return c.Abs(c.SchemaPath)
}
