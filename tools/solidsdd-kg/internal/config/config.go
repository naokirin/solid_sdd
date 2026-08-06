package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// Config is the merged kg runtime config (project paths + .solidsdd/kg/config.yaml).
type Config struct {
	Root             string   `yaml:"root"`
	KnowledgeDirs    []string `yaml:"knowledge_dirs"`
	BriefGlob        string   `yaml:"brief_glob"`
	FeatureGlob      string   `yaml:"feature_glob"`
	SpecDirs         []string `yaml:"spec_dirs"`
	LinksFiles       []string `yaml:"links_files"`
	CacheDir         string   `yaml:"cache_dir"`
	DBFilename       string   `yaml:"db_filename"`
	BriefIDSeparator string   `yaml:"brief_id_separator"`
	SchemaPath       string   `yaml:"schema_path"`
	FreshnessDays    int      `yaml:"freshness_days"`
	ProjectRoot      string   `yaml:"-"`
	ConfigPath       string   `yaml:"-"`
	SolidsddDir      string   `yaml:"-"` // project-relative meta root
	KgDir            string   `yaml:"-"` // project-relative kg directory
	ProjectConfigPath string  `yaml:"-"`
}

// ProjectPaths is the paths block of .solidsdd/config.yaml.
type ProjectPaths struct {
	Solidsdd           string   `yaml:"solidsdd"`
	ActiveChange       string   `yaml:"active_change"`
	Changes            string   `yaml:"changes"`
	HostToolchain      string   `yaml:"host_toolchain"`
	Kg                 string   `yaml:"kg"`
	Cache              string   `yaml:"cache"`
	Knowledge          []string `yaml:"knowledge"`
	Requirements       string   `yaml:"requirements"`
	RequirementsGlob   string   `yaml:"requirements_glob"`
	OpenAPI            string   `yaml:"openapi"`
	GraphQL            string   `yaml:"graphql"`
	Contracts          string   `yaml:"contracts"`
	Formal             string   `yaml:"formal"`
	ContractTestsTS    string   `yaml:"contract_tests_ts"`
	ContractTestsRuby  string   `yaml:"contract_tests_ruby"`
}

// ProjectConfig is .solidsdd/config.yaml.
type ProjectConfig struct {
	Version string       `yaml:"version"`
	Paths   ProjectPaths `yaml:"paths"`
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
		FreshnessDays:    180,
		SolidsddDir:      ".solidsdd",
		KgDir:            ".solidsdd/kg",
	}
}

// DiscoverSolidsddRel returns project-relative meta root (SOLIDSDD_DIR or .solidsdd).
func DiscoverSolidsddRel(projectRoot string) (string, error) {
	raw := strings.TrimSpace(os.Getenv("SOLIDSDD_DIR"))
	if raw == "" {
		return ".solidsdd", nil
	}
	if filepath.IsAbs(raw) {
		absRoot, err := filepath.Abs(projectRoot)
		if err != nil {
			return "", err
		}
		rel, err := filepath.Rel(absRoot, raw)
		if err != nil {
			return "", fmt.Errorf("SOLIDSDD_DIR %q must be under project root %s: %w", raw, absRoot, err)
		}
		if strings.HasPrefix(rel, "..") {
			return "", fmt.Errorf("SOLIDSDD_DIR %q must be under project root %s", raw, absRoot)
		}
		return filepath.ToSlash(rel), nil
	}
	return filepath.ToSlash(raw), nil
}

func defaultProjectPaths(solidsddRel string) ProjectPaths {
	p := ProjectPaths{
		Solidsdd:          ".solidsdd",
		ActiveChange:      ".solidsdd/active-change.json",
		Changes:           ".solidsdd/changes",
		HostToolchain:     ".solidsdd/host-toolchain.json",
		Kg:                ".solidsdd/kg",
		Cache:             ".solidsdd-cache",
		Knowledge:         []string{"knowledge"},
		Requirements:      "requirements",
		RequirementsGlob:  "requirements/**/*.feature",
		OpenAPI:           "openapi/openapi.yaml",
		GraphQL:           "graphql/schema.graphql",
		Contracts:         "contracts",
		Formal:            "formal",
		ContractTestsTS:   "tests/contracts",
		ContractTestsRuby: "spec/contracts",
	}
	if solidsddRel != "" && solidsddRel != ".solidsdd" {
		p.Solidsdd = solidsddRel
		rewrite := func(s string) string {
			if strings.HasPrefix(s, ".solidsdd") {
				return solidsddRel + strings.TrimPrefix(s, ".solidsdd")
			}
			return s
		}
		p.ActiveChange = rewrite(p.ActiveChange)
		p.Changes = rewrite(p.Changes)
		p.HostToolchain = rewrite(p.HostToolchain)
		p.Kg = rewrite(p.Kg)
	}
	return p
}

func mergeProjectPaths(base ProjectPaths, over ProjectPaths) ProjectPaths {
	out := base
	set := func(dst *string, v string) {
		if v != "" {
			*dst = v
		}
	}
	set(&out.Solidsdd, over.Solidsdd)
	set(&out.ActiveChange, over.ActiveChange)
	set(&out.Changes, over.Changes)
	set(&out.HostToolchain, over.HostToolchain)
	set(&out.Kg, over.Kg)
	set(&out.Cache, over.Cache)
	set(&out.Requirements, over.Requirements)
	set(&out.RequirementsGlob, over.RequirementsGlob)
	set(&out.OpenAPI, over.OpenAPI)
	set(&out.GraphQL, over.GraphQL)
	set(&out.Contracts, over.Contracts)
	set(&out.Formal, over.Formal)
	set(&out.ContractTestsTS, over.ContractTestsTS)
	set(&out.ContractTestsRuby, over.ContractTestsRuby)
	if len(over.Knowledge) > 0 {
		out.Knowledge = append([]string(nil), over.Knowledge...)
	}
	return out
}

// LoadProjectConfig reads .solidsdd/config.yaml (or SOLIDSDD_DIR/config.yaml).
// Missing file yields defaults derived from discovery.
func LoadProjectConfig(projectRoot string) (ProjectPaths, string, string, error) {
	absRoot, err := filepath.Abs(projectRoot)
	if err != nil {
		return ProjectPaths{}, "", "", err
	}
	discovered, err := DiscoverSolidsddRel(absRoot)
	if err != nil {
		return ProjectPaths{}, "", "", err
	}
	paths := defaultProjectPaths(discovered)
	configPath := filepath.Join(absRoot, discovered, "config.yaml")
	data, err := os.ReadFile(configPath)
	if err != nil {
		if os.IsNotExist(err) {
			return paths, discovered, "", nil
		}
		return ProjectPaths{}, "", "", err
	}
	var pc ProjectConfig
	if err := yaml.Unmarshal(data, &pc); err != nil {
		return ProjectPaths{}, "", "", fmt.Errorf("parse project config %s: %w", configPath, err)
	}
	if pc.Version != "" && pc.Version != "1" {
		return ProjectPaths{}, "", "", fmt.Errorf("unsupported config.yaml version %q in %s", pc.Version, configPath)
	}
	paths = mergeProjectPaths(paths, pc.Paths)
	if filepath.ToSlash(paths.Solidsdd) != filepath.ToSlash(discovered) {
		return ProjectPaths{}, "", "", fmt.Errorf(
			"paths.solidsdd %q does not match discovery %q (SOLIDSDD_DIR or .solidsdd)",
			paths.Solidsdd, discovered,
		)
	}
	return paths, discovered, configPath, nil
}

func applyProjectPaths(cfg *Config, paths ProjectPaths) {
	cfg.SolidsddDir = paths.Solidsdd
	if paths.Kg != "" {
		cfg.KgDir = paths.Kg
	}
	if len(paths.Knowledge) > 0 {
		cfg.KnowledgeDirs = append([]string(nil), paths.Knowledge...)
	}
	if paths.Changes != "" {
		cfg.BriefGlob = strings.TrimRight(filepath.ToSlash(paths.Changes), "/") + "/*/change-brief.json"
	}
	if paths.RequirementsGlob != "" {
		cfg.FeatureGlob = paths.RequirementsGlob
	} else if paths.Requirements != "" {
		cfg.FeatureGlob = strings.TrimRight(filepath.ToSlash(paths.Requirements), "/") + "/**/*.feature"
	}
	if paths.Cache != "" {
		cfg.CacheDir = paths.Cache
	}
	if paths.Kg != "" {
		kg := strings.TrimRight(filepath.ToSlash(paths.Kg), "/")
		cfg.LinksFiles = []string{kg + "/links.yaml"}
		cfg.SchemaPath = kg + "/schema.yaml"
	}
}

// Load reads kg config from path (or default under paths.kg), after applying project config paths.
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

	paths, _, projectCfgPath, err := LoadProjectConfig(absRoot)
	if err != nil {
		return cfg, err
	}
	cfg.ProjectConfigPath = projectCfgPath
	applyProjectPaths(&cfg, paths)

	if configPath == "" {
		configPath = filepath.Join(absRoot, cfg.KgDir, "config.yaml")
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
	cfg.ProjectConfigPath = projectCfgPath
	cfg.SolidsddDir = paths.Solidsdd
	if cfg.KgDir == "" {
		cfg.KgDir = paths.Kg
	}
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
		cfg.SchemaPath = filepath.ToSlash(filepath.Join(cfg.KgDir, "schema.yaml"))
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

// BaselineFile is the default baseline.json under the kg directory.
func (c Config) BaselineFile() string {
	kg := c.KgDir
	if kg == "" {
		kg = ".solidsdd/kg"
	}
	return c.Abs(filepath.Join(kg, "baseline.json"))
}
