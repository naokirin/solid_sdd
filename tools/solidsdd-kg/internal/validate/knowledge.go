package validate

import (
	"fmt"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/schema"
)

// KnowledgeOptions configures Phase 3 knowledge-layer checks.
type KnowledgeOptions struct {
	FreshnessDays int // 0 = skip FR-210
	Now           time.Time
}

// KnowledgeLayer runs FR-207..211 checks.
func KnowledgeLayer(g *model.Graph, opts KnowledgeOptions) []Violation {
	idx := buildIndex(g)
	var out []Violation
	out = append(out, implicitConceptUse(g, idx)...)
	out = append(out, unreferencedKnowledge(idx)...)
	out = append(out, contradictingPolicies(idx, g)...)
	out = append(out, staleKnowledge(idx, opts)...)
	out = append(out, deviateWithoutReason(g)...)
	return out
}

func knowledgeTypes() map[string]bool {
	return map[string]bool{
		"concept": true, "policy": true, "invariant": true,
		"pattern": true, "decision": true, "lesson": true,
	}
}

// FR-207: concept alias/title appears in another node's body without mentions/refines.
func implicitConceptUse(g *model.Graph, idx index) []Violation {
	var concepts []*model.Node
	for _, n := range idx.byID {
		if n.Type == "concept" && n.Status != "deprecated" {
			concepts = append(concepts, n)
		}
	}
	if len(concepts) == 0 {
		return nil
	}

	linked := map[string]map[string]bool{} // from -> to concept
	for _, e := range g.Edges {
		if e.Type != "mentions" && e.Type != "refines" {
			continue
		}
		if linked[e.From] == nil {
			linked[e.From] = map[string]bool{}
		}
		linked[e.From][e.To] = true
	}

	var out []Violation
	for _, n := range idx.byID {
		if n.Type == "concept" {
			continue
		}
		text := n.Title + "\n" + n.Body
		if text == "" {
			continue
		}
		lower := strings.ToLower(text)
		for _, c := range concepts {
			if n.ID == c.ID {
				continue
			}
			if linked[n.ID][c.ID] {
				continue
			}
			terms := append([]string{c.Title}, c.Aliases...)
			for _, term := range terms {
				term = strings.TrimSpace(term)
				if term == "" || utf8.RuneCountInString(term) < 2 {
					continue
				}
				if containsTerm(lower, strings.ToLower(term)) {
					out = append(out, Violation{
						Rule: "IMPLICIT_CONCEPT_USE", Severity: "warn",
						Message: fmt.Sprintf("node %s mentions concept term %q without mentions/refines to %s", n.ID, term, c.ID),
						Path: n.SourcePath, Line: n.SourceLine, Node: n.ID, To: c.ID,
					})
					break
				}
			}
		}
	}
	return out
}

func containsTerm(haystack, term string) bool {
	if term == "" {
		return false
	}
	// Prefer word-ish boundaries for ASCII; substring for CJK.
	if isASCIIWord(term) {
		re := regexp.MustCompile(`(?i)(^|[^A-Za-z0-9_])` + regexp.QuoteMeta(term) + `([^A-Za-z0-9_]|$)`)
		return re.MatchString(haystack)
	}
	return strings.Contains(haystack, term)
}

func isASCIIWord(s string) bool {
	for _, r := range s {
		if r > 127 {
			return false
		}
	}
	return true
}

// FR-208: knowledge nodes with zero incoming edges.
func unreferencedKnowledge(idx index) []Violation {
	kt := knowledgeTypes()
	var out []Violation
	for _, n := range idx.byID {
		if !kt[n.Type] || n.Status == "deprecated" {
			continue
		}
		if len(idx.in[n.ID]) == 0 {
			out = append(out, Violation{
				Rule: "UNREFERENCED_KNOWLEDGE", Severity: "warn",
				Message: fmt.Sprintf("knowledge node %s has no incoming references", n.ID),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
		}
	}
	return out
}

// FR-209: active policies in the same scope connected by contradicts.
func contradictingPolicies(idx index, g *model.Graph) []Violation {
	var out []Violation
	seen := map[string]bool{}
	for _, e := range g.Edges {
		if e.Type != "contradicts" {
			continue
		}
		a, b := idx.byID[e.From], idx.byID[e.To]
		if a == nil || b == nil {
			continue
		}
		if a.Type != "policy" || b.Type != "policy" {
			continue
		}
		if a.Status != "active" || b.Status != "active" {
			continue
		}
		if a.Scope == "" || a.Scope != b.Scope {
			continue
		}
		key := a.ID + "|" + b.ID
		if a.ID > b.ID {
			key = b.ID + "|" + a.ID
		}
		if seen[key] {
			continue
		}
		seen[key] = true
		out = append(out, Violation{
			Rule: "CONTRADICTING_POLICIES", Severity: "error",
			Message: fmt.Sprintf("active policies %s and %s contradict within scope %s", a.ID, b.ID, a.Scope),
			Path: e.SourcePath, Line: e.SourceLine, From: a.ID, To: b.ID,
		})
	}
	return out
}

// FR-210: verified_at older than threshold.
func staleKnowledge(idx index, opts KnowledgeOptions) []Violation {
	if opts.FreshnessDays <= 0 {
		return nil
	}
	now := opts.Now
	if now.IsZero() {
		now = time.Now().UTC()
	}
	kt := knowledgeTypes()
	var out []Violation
	for _, n := range idx.byID {
		if !kt[n.Type] || n.Status == "deprecated" {
			continue
		}
		if n.VerifiedAt == "" {
			out = append(out, Violation{
				Rule: "STALE_KNOWLEDGE", Severity: "warn",
				Message: fmt.Sprintf("knowledge node %s has no verified_at", n.ID),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
			continue
		}
		t, err := time.Parse("2006-01-02", n.VerifiedAt)
		if err != nil {
			out = append(out, Violation{
				Rule: "STALE_KNOWLEDGE", Severity: "warn",
				Message: fmt.Sprintf("knowledge node %s has invalid verified_at %q", n.ID, n.VerifiedAt),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
			continue
		}
		age := now.Sub(t)
		if age > time.Duration(opts.FreshnessDays)*24*time.Hour {
			out = append(out, Violation{
				Rule: "STALE_KNOWLEDGE", Severity: "warn",
				Message: fmt.Sprintf("knowledge node %s verified_at %s exceeds %d days", n.ID, n.VerifiedAt, opts.FreshnessDays),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
		}
	}
	return out
}

// FR-211: deviates_from without reason.
func deviateWithoutReason(g *model.Graph) []Violation {
	var out []Violation
	for _, e := range g.Edges {
		if e.Type != "deviates_from" {
			continue
		}
		if strings.TrimSpace(e.Reason) == "" {
			out = append(out, Violation{
				Rule: "DEVIATE_WITHOUT_REASON", Severity: "error",
				Message: fmt.Sprintf("deviates_from %s -> %s has no reason", e.From, e.To),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To,
			})
		}
	}
	return out
}

// Wire knowledge asserts into EvaluateRules for schema-declared rules.
func evalKnowledgeAssert(g *model.Graph, rule schema.Rule, sev string, opts KnowledgeOptions) []Violation {
	var raw []Violation
	switch rule.Assert {
	case "implicit_concept_use":
		raw = implicitConceptUse(g, buildIndex(g))
	case "unreferenced_knowledge":
		raw = unreferencedKnowledge(buildIndex(g))
	case "contradicting_policies":
		raw = contradictingPolicies(buildIndex(g), g)
	case "stale_knowledge":
		raw = staleKnowledge(buildIndex(g), opts)
	case "deviate_without_reason":
		raw = deviateWithoutReason(g)
	default:
		return nil
	}
	for i := range raw {
		raw[i].Rule = rule.ID
		if sev != "" {
			raw[i].Severity = sev
		}
	}
	return raw
}
