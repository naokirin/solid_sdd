package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/build"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/config"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/format"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/validate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cmd := os.Args[1]
	args := os.Args[2:]
	switch cmd {
	case "build":
		os.Exit(cmdBuild(args))
	case "check":
		os.Exit(cmdCheck(args))
	case "fmt":
		os.Exit(cmdFmt(args))
	case "help", "-h", "--help":
		usage()
	default:
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", cmd)
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, `solidsdd-kg — solid_sdd knowledge graph (Phase 1)

Usage:
  solidsdd-kg build  [--root DIR] [--config PATH] [--json]
  solidsdd-kg check  [--root DIR] [--config PATH] [--json]
  solidsdd-kg fmt    [--root DIR] [--check] [paths...]

Commands:
  build   Parse knowledge / ChangeBrief / Gherkin / links and rebuild SQLite index
  check   Build then report dangling references (exit 1 on errors)
  fmt     Normalize knowledge frontmatter key/array order (body unchanged)
`)
}

func loadCfg(fs *flag.FlagSet, args []string) (config.Config, bool, error) {
	root := fs.String("root", ".", "project root")
	cfgPath := fs.String("config", "", "path to .solidsdd/kg/config.yaml")
	jsonOut := fs.Bool("json", false, "machine-readable JSON output")
	if err := fs.Parse(args); err != nil {
		return config.Config{}, false, err
	}
	cfg, err := config.Load(*root, *cfgPath)
	return cfg, *jsonOut, err
}

func cmdBuild(args []string) int {
	fs := flag.NewFlagSet("build", flag.ContinueOnError)
	cfg, jsonOut, err := loadCfg(fs, args)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	res, err := build.Full(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if jsonOut {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{
			"ok":           true,
			"db":           res.DBPath,
			"nodes":        len(res.Graph.Nodes),
			"edges":        len(res.Graph.Edges),
			"parse_issues": res.Graph.Issues,
		})
		return 0
	}
	fmt.Printf("built %s\n", res.DBPath)
	fmt.Printf("nodes=%d edges=%d parse_issues=%d\n", len(res.Graph.Nodes), len(res.Graph.Edges), len(res.Graph.Issues))
	for _, iss := range res.Graph.Issues {
		fmt.Fprintf(os.Stderr, "parse: %s:%d: %s\n", iss.Path, iss.Line, iss.Message)
	}
	return 0
}

func cmdCheck(args []string) int {
	fs := flag.NewFlagSet("check", flag.ContinueOnError)
	cfg, jsonOut, err := loadCfg(fs, args)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	res, err := build.Full(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	violations := append(validate.DuplicateIDs(res.Graph), validate.DanglingReferences(res.Graph)...)
	errors := 0
	for _, v := range violations {
		if v.Severity == "error" {
			errors++
		}
	}
	if jsonOut {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{
			"ok":             errors == 0 && len(res.Graph.Issues) == 0,
			"db":             res.DBPath,
			"nodes":          len(res.Graph.Nodes),
			"edges":          len(res.Graph.Edges),
			"parse_issues":   res.Graph.Issues,
			"violations":     violations,
			"error_count":    errors,
		})
	} else {
		for _, iss := range res.Graph.Issues {
			fmt.Fprintf(os.Stderr, "parse: %s:%d: %s\n", iss.Path, iss.Line, iss.Message)
		}
		for _, v := range violations {
			loc := v.Path
			if v.Line > 0 {
				loc = fmt.Sprintf("%s:%d", v.Path, v.Line)
			}
			fmt.Fprintf(os.Stderr, "%s: %s: %s\n", v.Severity, loc, v.Message)
		}
		if errors == 0 && len(res.Graph.Issues) == 0 {
			fmt.Printf("ok — nodes=%d edges=%d\n", len(res.Graph.Nodes), len(res.Graph.Edges))
		}
	}
	if len(res.Graph.Issues) > 0 || errors > 0 {
		return 1
	}
	return 0
}

func cmdFmt(args []string) int {
	fs := flag.NewFlagSet("fmt", flag.ContinueOnError)
	root := fs.String("root", ".", "project root")
	checkOnly := fs.Bool("check", false, "exit 1 if any file would change")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	paths := fs.Args()
	if len(paths) == 0 {
		cfg, err := config.Load(*root, "")
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			return 2
		}
		for _, dir := range cfg.KnowledgeDirs {
			abs := cfg.Abs(dir)
			_ = filepath.WalkDir(abs, func(path string, d os.DirEntry, err error) error {
				if err != nil || d.IsDir() {
					return nil
				}
				if strings.HasSuffix(strings.ToLower(path), ".md") {
					paths = append(paths, path)
				}
				return nil
			})
		}
	}
	changedAny := false
	for _, p := range paths {
		changed, err := format.File(p, !*checkOnly)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: %v\n", p, err)
			return 1
		}
		if changed {
			changedAny = true
			if *checkOnly {
				fmt.Fprintf(os.Stderr, "needs format: %s\n", p)
			} else {
				fmt.Printf("formatted %s\n", p)
			}
		}
	}
	if *checkOnly && changedAny {
		return 1
	}
	return 0
}
