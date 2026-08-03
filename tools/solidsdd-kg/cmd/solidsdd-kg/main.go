package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/baseline"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/build"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/config"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/format"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/query"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/scope"
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
	case "impact":
		os.Exit(cmdImpact(args))
	case "scope":
		os.Exit(cmdScope(args))
	case "help", "-h", "--help":
		usage()
	default:
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", cmd)
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, `solidsdd-kg — solid_sdd knowledge graph

Usage:
  solidsdd-kg build   [--root DIR] [--config PATH] [--json]
  solidsdd-kg check   [--root DIR] [--config PATH] [--json]
                      [--baseline] [--update-baseline] [--fail-on-warn]
  solidsdd-kg fmt     [--root DIR] [--check] [paths...]
  solidsdd-kg impact  <node-id> [--root DIR] [--direction out|in|both]
                      [--hops N] [--types a,b] [--json]
  solidsdd-kg scope   <scope> [--root DIR] [--json]

Commands:
  build    Parse sources and rebuild SQLite index
  check    Build then validate (dangling, schema rules, coverage, knowledge); baseline filters known violations
  fmt      Normalize knowledge frontmatter key/array order
  impact   List nodes reachable from a start id (FR-301)
  scope    Resolve policies applicable to a dotted scope (FR-304)
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
	root := fs.String("root", ".", "project root")
	cfgPath := fs.String("config", "", "path to .solidsdd/kg/config.yaml")
	jsonOut := fs.Bool("json", false, "machine-readable JSON output")
	useBaseline := fs.Bool("baseline", false, "suppress violations listed in baseline.json (FR-213)")
	updateBaseline := fs.Bool("update-baseline", false, "write current violations to baseline.json")
	failOnWarn := fs.Bool("fail-on-warn", false, "exit 1 when warnings remain after baseline filter")
	baselinePath := fs.String("baseline-path", "", "override baseline.json path")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	cfg, err := config.Load(*root, *cfgPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	res, err := build.Full(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	all := validate.All(res.Graph, res.Schema, validate.KnowledgeOptions{
		FreshnessDays: cfg.FreshnessDays,
	})
	bp := *baselinePath
	if bp == "" {
		bp = baseline.Path(cfg.ProjectRoot)
	}

	if *updateBaseline {
		if err := baseline.Save(bp, all); err != nil {
			fmt.Fprintln(os.Stderr, err)
			return 1
		}
		fmt.Printf("wrote baseline %s (%d violations)\n", bp, len(all))
	}

	active := all
	var suppressed []validate.Violation
	if *useBaseline {
		base, err := baseline.Load(bp)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			return 2
		}
		active, suppressed = baseline.Filter(base, all)
	}

	errors, warns := 0, 0
	for _, v := range active {
		switch v.Severity {
		case "error":
			errors++
		default:
			warns++
		}
	}

	if *jsonOut {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{
			"ok":               errors == 0 && len(res.Graph.Issues) == 0 && (!*failOnWarn || warns == 0),
			"db":               res.DBPath,
			"nodes":            len(res.Graph.Nodes),
			"edges":            len(res.Graph.Edges),
			"parse_issues":     res.Graph.Issues,
			"violations":       active,
			"suppressed":       suppressed,
			"error_count":      errors,
			"warn_count":       warns,
			"baseline":         *useBaseline,
		})
	} else {
		for _, iss := range res.Graph.Issues {
			fmt.Fprintf(os.Stderr, "parse: %s:%d: %s\n", iss.Path, iss.Line, iss.Message)
		}
		for _, v := range active {
			loc := v.Path
			if v.Line > 0 {
				loc = fmt.Sprintf("%s:%d", v.Path, v.Line)
			}
			if loc == "" {
				loc = v.Node
			}
			fmt.Fprintf(os.Stderr, "%s: %s: [%s] %s\n", v.Severity, loc, v.Rule, v.Message)
		}
		if len(suppressed) > 0 {
			fmt.Fprintf(os.Stderr, "baseline: suppressed %d known violation(s)\n", len(suppressed))
		}
		if errors == 0 && len(res.Graph.Issues) == 0 && (!*failOnWarn || warns == 0) {
			fmt.Printf("ok — nodes=%d edges=%d (errors=%d warns=%d)\n",
				len(res.Graph.Nodes), len(res.Graph.Edges), errors, warns)
		}
	}

	if len(res.Graph.Issues) > 0 || errors > 0 || (*failOnWarn && warns > 0) {
		return 1
	}
	return 0
}

func cmdImpact(args []string) int {
	fs := flag.NewFlagSet("impact", flag.ContinueOnError)
	root := fs.String("root", ".", "project root")
	cfgPath := fs.String("config", "", "path to config.yaml")
	jsonOut := fs.Bool("json", false, "JSON output")
	dir := fs.String("direction", "out", "out | in | both")
	hops := fs.Int("hops", 2, "max hops")
	types := fs.String("types", "", "comma-separated node types to include (empty=all)")
	flagArgs, positional := splitFlags(args)
	if err := fs.Parse(flagArgs); err != nil {
		return 2
	}
	if len(positional) < 1 {
		fmt.Fprintln(os.Stderr, "impact requires a node id")
		return 2
	}
	start := positional[0]
	cfg, err := config.Load(*root, *cfgPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	res, err := build.Full(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	var include map[string]bool
	if *types != "" {
		include = map[string]bool{}
		for _, t := range strings.Split(*types, ",") {
			t = strings.TrimSpace(t)
			if t != "" {
				include[t] = true
			}
		}
	}
	d := query.Direction(*dir)
	hits := query.Impact(res.Graph, start, d, *hops, include)
	if by := res.Graph.NodeByID(start); by == nil {
		fmt.Fprintf(os.Stderr, "unknown node id %q\n", start)
		return 1
	}
	if *jsonOut {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{
			"start":     start,
			"direction": *dir,
			"hops":      *hops,
			"hits":      hits,
		})
		return 0
	}
	if len(hits) == 0 {
		fmt.Printf("no neighbors within %d hop(s) from %s (%s)\n", *hops, start, *dir)
		return 0
	}
	for _, h := range hits {
		fmt.Printf("hops=%d %s %s  %s\n", h.Hops, h.Type, h.ID, h.Title)
	}
	return 0
}

func cmdScope(args []string) int {
	fs := flag.NewFlagSet("scope", flag.ContinueOnError)
	root := fs.String("root", ".", "project root")
	cfgPath := fs.String("config", "", "path to config.yaml")
	jsonOut := fs.Bool("json", false, "JSON output")
	flagArgs, positional := splitFlags(args)
	if err := fs.Parse(flagArgs); err != nil {
		return 2
	}
	if len(positional) < 1 {
		fmt.Fprintln(os.Stderr, "scope requires a dotted scope string (e.g. org.solid_sdd.kg)")
		return 2
	}
	target := positional[0]
	cfg, err := config.Load(*root, *cfgPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	res, err := build.Full(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	pols := scope.ResolvePolicies(res.Graph, target)
	if *jsonOut {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{
			"scope":    target,
			"chain":    scope.Chain(target),
			"policies": pols,
		})
		return 0
	}
	fmt.Printf("scope %s  chain=%v\n", target, scope.Chain(target))
	if len(pols) == 0 {
		fmt.Println("no applicable policies")
		return 0
	}
	for _, p := range pols {
		fmt.Printf("dist=%d %s  %s (scope=%s)\n", p.Distance, p.ID, p.Title, p.Scope)
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

// splitFlags separates GNU-style flags from positional args so flags may follow the node id.
func splitFlags(args []string) (flagArgs, positional []string) {
	for i := 0; i < len(args); i++ {
		a := args[i]
		if a == "--" {
			positional = append(positional, args[i+1:]...)
			break
		}
		if strings.HasPrefix(a, "-") {
			flagArgs = append(flagArgs, a)
			// boolean flags without = may consume next token if it looks like a value
			name := strings.TrimLeft(a, "-")
			if strings.Contains(name, "=") {
				continue
			}
			switch name {
			case "json", "check", "baseline", "update-baseline", "fail-on-warn", "h", "help":
				continue
			}
			if i+1 < len(args) && !strings.HasPrefix(args[i+1], "-") {
				i++
				flagArgs = append(flagArgs, args[i])
			}
			continue
		}
		positional = append(positional, a)
	}
	return flagArgs, positional
}
