package promote

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	"unicode"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

// Candidate is a human-reviewable promotion or merge suggestion (FR-501/502/212).
type Candidate struct {
	Kind    string   `json:"kind"` // duplicate_title | shared_phrase | inline_definition | contract_vocabulary
	IDs     []string `json:"ids"`
	Summary string   `json:"summary"`
	Paths   []string `json:"paths,omitempty"`
}

type ref struct {
	id, path string
}

func normalizeTitle(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	var b strings.Builder
	for _, r := range s {
		if unicode.IsLetter(r) || unicode.IsDigit(r) || unicode.Is(unicode.Hiragana, r) ||
			unicode.Is(unicode.Katakana, r) || unicode.Is(unicode.Han, r) {
			b.WriteRune(r)
		}
	}
	return b.String()
}

// DuplicateNodes finds normalized title/alias collisions (FR-212).
func DuplicateNodes(g *model.Graph) []Candidate {
	byKey := map[string][]ref{}
	for _, n := range g.Nodes {
		keys := []string{normalizeTitle(n.Title)}
		for _, a := range n.Aliases {
			keys = append(keys, normalizeTitle(a))
		}
		seen := map[string]bool{}
		for _, k := range keys {
			if k == "" || seen[k] {
				continue
			}
			seen[k] = true
			byKey[k] = append(byKey[k], ref{id: n.ID, path: n.SourcePath})
		}
	}
	var out []Candidate
	emitted := map[string]bool{}
	for _, hits := range byKey {
		ids := uniqueIDs(hits)
		if len(ids) < 2 {
			continue
		}
		key := strings.Join(ids, "|")
		if emitted[key] {
			continue
		}
		emitted[key] = true
		out = append(out, Candidate{
			Kind:    "duplicate_title",
			IDs:     ids,
			Summary: fmt.Sprintf("normalized title/alias collision among %s", strings.Join(ids, ", ")),
			Paths:   uniquePaths(hits),
		})
	}
	return out
}

// SharedPhrases finds identical normalized bodies (≥ minLen runes) across ≥2 nodes (FR-501 light).
func SharedPhrases(g *model.Graph, minLen int) []Candidate {
	if minLen <= 0 {
		minLen = 40
	}
	byBody := map[string][]model.Node{}
	for _, n := range g.Nodes {
		body := normalizeTitle(n.Body)
		if len([]rune(body)) < minLen {
			continue
		}
		byBody[body] = append(byBody[body], n)
	}
	var out []Candidate
	for _, nodes := range byBody {
		if len(nodes) < 2 {
			continue
		}
		ids := make([]string, 0, len(nodes))
		paths := make([]string, 0, len(nodes))
		for _, n := range nodes {
			ids = append(ids, n.ID)
			paths = append(paths, n.SourcePath)
		}
		out = append(out, Candidate{
			Kind:    "shared_phrase",
			IDs:     ids,
			Summary: fmt.Sprintf("shared body text among %s — consider promoting to policy/concept", strings.Join(ids, ", ")),
			Paths:   paths,
		})
	}
	return out
}

var defRe = regexp.MustCompile(`(?i)(?:「[^」]{2,40}」とは、|[A-Za-z][A-Za-z0-9_-]{2,40}\s+is defined as|[A-Za-z][A-Za-z0-9_-]{2,40}\s+means that)\s*.{0,80}`)

// also reject bare とは without 「」
func looksLikeDefinition(body string) string {
	if m := defRe.FindString(body); m != "" {
		return strings.TrimSpace(m)
	}
	return ""
}

// InlineDefinitions heuristically finds definitional prose in non-concept nodes (FR-502 light).
func InlineDefinitions(g *model.Graph) []Candidate {
	var out []Candidate
	for _, n := range g.Nodes {
		if n.Type == "concept" || n.Body == "" {
			continue
		}
		if m := looksLikeDefinition(n.Body); m != "" {
			out = append(out, Candidate{
				Kind:    "inline_definition",
				IDs:     []string{n.ID},
				Summary: fmt.Sprintf("possible inline definition in %s: %q", n.ID, m),
				Paths:   []string{n.SourcePath},
			})
		}
	}
	return out
}

// AllCandidates returns Phase 5 suggestion list (never applies automatically).
func AllCandidates(g *model.Graph) []Candidate {
	var out []Candidate
	out = append(out, DuplicateNodes(g)...)
	out = append(out, SharedPhrases(g, 40)...)
	out = append(out, InlineDefinitions(g)...)
	return out
}

// AllCandidatesWithContracts merges graph heuristics with OCL/OpenAPI vocabulary hints.
func AllCandidatesWithContracts(projectRoot string, g *model.Graph) []Candidate {
	out := AllCandidates(g)
	out = append(out, ContractVocabulary(projectRoot, g)...)
	return out
}

func uniqueIDs(hits []ref) []string {
	seen := map[string]bool{}
	var ids []string
	for _, h := range hits {
		if seen[h.id] {
			continue
		}
		seen[h.id] = true
		ids = append(ids, h.id)
	}
	return ids
}

func uniquePaths(hits []ref) []string {
	seen := map[string]bool{}
	var paths []string
	for _, h := range hits {
		if h.path == "" || seen[h.path] {
			continue
		}
		seen[h.path] = true
		paths = append(paths, h.path)
	}
	return paths
}

// ApplyResult is the outcome of an approved promotion (FR-503/504).
type ApplyResult struct {
	CreatedPath string
	NodeID      string
}

var typeDir = map[string]string{
	"policy":    "policies",
	"concept":   "concepts",
	"decision":  "decisions",
	"lesson":    "lessons",
	"pattern":   "patterns",
	"invariant": "invariants",
}

// ApplyNode writes a new knowledge markdown file. Must be invoked explicitly (FR-504).
func ApplyNode(cfgRoot, knowledgeDir, nodeType, id, title, scope, sourceBody string) (ApplyResult, error) {
	if id == "" || title == "" {
		return ApplyResult{}, fmt.Errorf("id and title required")
	}
	if nodeType == "" {
		nodeType = "policy"
	}
	sub, ok := typeDir[nodeType]
	if !ok {
		return ApplyResult{}, fmt.Errorf("unsupported type %q (want concept|policy|invariant|pattern|decision|lesson)", nodeType)
	}
	dir := filepath.Join(cfgRoot, knowledgeDir, sub)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return ApplyResult{}, err
	}
	path := filepath.Join(dir, id+".md")
	if _, err := os.Stat(path); err == nil {
		return ApplyResult{}, fmt.Errorf("already exists: %s", path)
	}
	var b strings.Builder
	b.WriteString("---\n")
	fmt.Fprintf(&b, "id: %s\n", id)
	fmt.Fprintf(&b, "type: %s\n", nodeType)
	fmt.Fprintf(&b, "title: %s\n", title)
	b.WriteString("status: active\n")
	b.WriteString("maturity: canonical\n")
	if scope != "" || nodeType == "policy" || nodeType == "invariant" {
		if scope == "" {
			scope = "org"
		}
		fmt.Fprintf(&b, "scope: %s\n", scope)
	}
	b.WriteString("aliases: []\n")
	fmt.Fprintf(&b, "verified_at: %q\n", time.Now().UTC().Format("2006-01-02"))
	b.WriteString("---\n\n")
	b.WriteString(strings.TrimSpace(sourceBody))
	b.WriteString("\n")
	if err := os.WriteFile(path, []byte(b.String()), 0o644); err != nil {
		return ApplyResult{}, err
	}
	return ApplyResult{CreatedPath: path, NodeID: id}, nil
}

// ApplyPolicy is a convenience wrapper for type=policy.
func ApplyPolicy(cfgRoot, knowledgeDir, id, title, scope, sourceBody string) (ApplyResult, error) {
	return ApplyNode(cfgRoot, knowledgeDir, "policy", id, title, scope, sourceBody)
}
