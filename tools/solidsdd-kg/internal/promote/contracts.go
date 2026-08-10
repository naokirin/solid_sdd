package promote

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/config"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

var (
	oclPostErrorRe = regexp.MustCompile(`(?m)^\s*post\s+(\w+Error)\s*:`)
	oclTypeRe      = regexp.MustCompile(`\b(?:context|class)\s+(\w+)`)
	oclReturnRe    = regexp.MustCompile(`:\s*(Hold)\b`)
	openAPISchemaRe = regexp.MustCompile(`(?m)^\s{4}(\w+):\s*$`)
	openAPIRefRe    = regexp.MustCompile(`#/components/schemas/(\w+)`)
)

// ContractVocabulary scans OCL/OpenAPI for domain identifiers not yet covered by concept nodes.
func ContractVocabulary(projectRoot string, g *model.Graph) []Candidate {
	paths, _, _, err := config.LoadProjectConfig(projectRoot)
	if err != nil {
		return nil
	}
	covered := conceptTerms(g)
	var terms map[string][]string // term -> source paths
	add := func(term, path string) {
		term = strings.TrimSpace(term)
		if term == "" || isGenericTerm(term) {
			return
		}
		if covered[ normalizeTitle(term) ] {
			return
		}
		if terms == nil {
			terms = map[string][]string{}
		}
		for _, p := range terms[term] {
			if p == path {
				return
			}
		}
		terms[term] = append(terms[term], path)
	}

	root := projectRoot
	if !filepath.IsAbs(root) {
		root, _ = filepath.Abs(root)
	}
	contractsDir := filepath.Join(root, paths.Contracts)
	_ = filepath.Walk(contractsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(path, ".ocl") {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		body := string(data)
		for _, m := range oclPostErrorRe.FindAllStringSubmatch(body, -1) {
			add(m[1], path)
		}
		for _, m := range oclTypeRe.FindAllStringSubmatch(body, -1) {
			add(m[1], path)
		}
		for _, m := range oclReturnRe.FindAllStringSubmatch(body, -1) {
			add(m[1], path)
		}
		return nil
	})

	openAPIPath := filepath.Join(root, paths.OpenAPI)
	if data, err := os.ReadFile(openAPIPath); err == nil {
		body := string(data)
		inSchemas := false
		for _, line := range strings.Split(body, "\n") {
			if strings.TrimSpace(line) == "schemas:" {
				inSchemas = true
				continue
			}
			if inSchemas {
				if len(line) > 0 && line[0] != ' ' {
					inSchemas = false
					continue
				}
				if m := openAPISchemaRe.FindStringSubmatch(line); len(m) == 2 {
					add(m[1], openAPIPath)
				}
			}
		}
		for _, m := range openAPIRefRe.FindAllStringSubmatch(body, -1) {
			add(m[1], openAPIPath)
		}
	}

	var out []Candidate
	for term, paths := range terms {
		out = append(out, Candidate{
			Kind:    "contract_vocabulary",
			IDs:     []string{term},
			Summary: fmtSummary(term, paths),
			Paths:   paths,
		})
	}
	return out
}

func fmtSummary(term string, paths []string) string {
	return "contract term " + term + " has no concept node — consider CON-* with facets: vocabulary (" + strings.Join(uniquePaths(sliceRefs(paths)), ", ") + ")"
}

func sliceRefs(paths []string) []ref {
	out := make([]ref, len(paths))
	for i, p := range paths {
		out[i] = ref{path: p}
	}
	return out
}

func conceptTerms(g *model.Graph) map[string]bool {
	covered := map[string]bool{}
	if g == nil {
		return covered
	}
	for _, n := range g.Nodes {
		if n.Type != "concept" {
			continue
		}
		covered[normalizeTitle(n.ID)] = true
		covered[normalizeTitle(n.Title)] = true
		for _, a := range n.Aliases {
			covered[normalizeTitle(a)] = true
		}
		id := strings.TrimPrefix(n.ID, "CON-")
		covered[normalizeTitle(strings.ReplaceAll(id, "-", " "))] = true
		for _, m := range regexp.MustCompile(`\b(\w+Error)\b`).FindAllStringSubmatch(n.Body, -1) {
			covered[normalizeTitle(m[1])] = true
		}
	}
	return covered
}

func isGenericTerm(term string) bool {
	switch term {
	case "Reservation", "String", "Integer", "Boolean", "Sequence", "Error", "Response":
		return true
	}
	return false
}
