package validate

import (
	"fmt"
	"sort"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/schema"
)

// Violation is a check finding.
type Violation struct {
	Rule     string `json:"rule"`
	Severity string `json:"severity"`
	Message  string `json:"message"`
	Path     string `json:"path,omitempty"`
	Line     int    `json:"line,omitempty"`
	Node     string `json:"node,omitempty"`
	From     string `json:"from,omitempty"`
	To       string `json:"to,omitempty"`
}

// Fingerprint is a stable id for baseline matching (FR-213).
func (v Violation) Fingerprint() string {
	parts := []string{v.Rule, v.Node, v.From, v.To, v.Message}
	return strings.Join(parts, "|")
}

type index struct {
	byID       map[string]*model.Node
	out        map[string][]model.Edge // from -> edges
	in         map[string][]model.Edge // to -> edges
	nodesByType map[string][]*model.Node
}

func buildIndex(g *model.Graph) index {
	idx := index{
		byID:        map[string]*model.Node{},
		out:         map[string][]model.Edge{},
		in:          map[string][]model.Edge{},
		nodesByType: map[string][]*model.Node{},
	}
	for i := range g.Nodes {
		n := &g.Nodes[i]
		if _, ok := idx.byID[n.ID]; ok {
			continue
		}
		idx.byID[n.ID] = n
		idx.nodesByType[n.Type] = append(idx.nodesByType[n.Type], n)
	}
	for _, e := range g.Edges {
		idx.out[e.From] = append(idx.out[e.From], e)
		idx.in[e.To] = append(idx.in[e.To], e)
	}
	return idx
}

// All runs structural checks plus schema rules (FR-201..211, dangling, duplicates).
func All(g *model.Graph, sch schema.Schema, opts KnowledgeOptions) []Violation {
	var out []Violation
	out = append(out, DuplicateIDs(g)...)
	out = append(out, DanglingReferences(g)...)
	out = append(out, Structural(g, sch)...)
	out = append(out, EvaluateRules(g, sch, opts)...)
	sortViolations(out)
	return out
}

func sortViolations(out []Violation) {
	sort.Slice(out, func(i, j int) bool {
		if out[i].Rule != out[j].Rule {
			return out[i].Rule < out[j].Rule
		}
		if out[i].Path != out[j].Path {
			return out[i].Path < out[j].Path
		}
		if out[i].Line != out[j].Line {
			return out[i].Line < out[j].Line
		}
		if out[i].Node != out[j].Node {
			return out[i].Node < out[j].Node
		}
		return out[i].Message < out[j].Message
	})
}

// DanglingReferences finds edges whose from/to IDs are missing (FR-202).
func DanglingReferences(g *model.Graph) []Violation {
	ids := map[string]struct{}{}
	for _, n := range g.Nodes {
		ids[n.ID] = struct{}{}
	}
	var out []Violation
	for _, e := range g.Edges {
		if _, ok := ids[e.From]; !ok {
			out = append(out, Violation{
				Rule: "NO_DANGLING_REFS", Severity: "error",
				Message: fmt.Sprintf("edge %s: unknown from id %q", e.Type, e.From),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To,
			})
		}
		if _, ok := ids[e.To]; !ok {
			out = append(out, Violation{
				Rule: "NO_DANGLING_REFS", Severity: "error",
				Message: fmt.Sprintf("edge %s: unknown to id %q", e.Type, e.To),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To,
			})
		}
	}
	return out
}

// DuplicateIDs finds repeated node IDs across sources.
func DuplicateIDs(g *model.Graph) []Violation {
	seen := map[string]model.Node{}
	var out []Violation
	for _, n := range g.Nodes {
		if prev, ok := seen[n.ID]; ok {
			out = append(out, Violation{
				Rule: "DUPLICATE_ID", Severity: "error",
				Message: fmt.Sprintf("duplicate node id %q (also at %s:%d)", n.ID, prev.SourcePath, prev.SourceLine),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
			continue
		}
		seen[n.ID] = n
	}
	return out
}

// Structural validates node/edge types, required fields, statuses, and edge endpoints (FR-201 base).
func Structural(g *model.Graph, sch schema.Schema) []Violation {
	var out []Violation
	idx := buildIndex(g)
	for _, n := range g.Nodes {
		nt, ok := sch.NodeType(n.Type)
		if !ok {
			out = append(out, Violation{
				Rule: "UNKNOWN_NODE_TYPE", Severity: "error",
				Message: fmt.Sprintf("unknown node type %q", n.Type),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
			continue
		}
		for _, req := range nt.Required {
			if !nodeHasRequired(n, req) {
				out = append(out, Violation{
					Rule: "MISSING_REQUIRED_FIELD", Severity: "error",
					Message: fmt.Sprintf("node %s missing required field %q", n.ID, req),
					Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
				})
			}
		}
		if len(nt.Statuses) > 0 && n.Status != "" && !contains(nt.Statuses, n.Status) {
			out = append(out, Violation{
				Rule: "INVALID_STATUS", Severity: "error",
				Message: fmt.Sprintf("node %s has invalid status %q", n.ID, n.Status),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
		}
	}
	for _, e := range g.Edges {
		et, ok := sch.EdgeType(e.Type)
		if !ok {
			// superseded_by is stored as edge for dangling but may not be in edge_types
			if e.Type == "superseded_by" {
				continue
			}
			out = append(out, Violation{
				Rule: "UNKNOWN_EDGE_TYPE", Severity: "error",
				Message: fmt.Sprintf("unknown edge type %q", e.Type),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To,
			})
			continue
		}
		from := idx.byID[e.From]
		to := idx.byID[e.To]
		if from != nil && len(et.From) > 0 && !contains(et.From, from.Type) {
			out = append(out, Violation{
				Rule: "EDGE_FROM_TYPE", Severity: "error",
				Message: fmt.Sprintf("edge %s: from node %s has type %q not in %v", e.Type, e.From, from.Type, et.From),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To,
			})
		}
		if to != nil && len(et.To) > 0 && !contains(et.To, to.Type) {
			out = append(out, Violation{
				Rule: "EDGE_TO_TYPE", Severity: "error",
				Message: fmt.Sprintf("edge %s: to node %s has type %q not in %v", e.Type, e.To, to.Type, et.To),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To,
			})
		}
	}
	return out
}

func nodeHasRequired(n model.Node, field string) bool {
	switch field {
	case "status":
		return n.Status != ""
	case "scope":
		return n.Scope != ""
	case "title":
		return n.Title != ""
	case "type":
		return n.Type != ""
	case "id":
		return n.ID != ""
	default:
		return true
	}
}

func contains(xs []string, v string) bool {
	for _, x := range xs {
		if x == v {
			return true
		}
	}
	return false
}

// EvaluateRules runs schema.yaml rules with when/assert (FR-201, 203-211).
func EvaluateRules(g *model.Graph, sch schema.Schema, opts KnowledgeOptions) []Violation {
	idx := buildIndex(g)
	var out []Violation
	for _, rule := range sch.Rules {
		sev := rule.Severity
		if sev == "" {
			sev = "error"
		}
		switch rule.Assert {
		case "no_dangling_references":
			continue
		case "has_incoming(implements)":
			out = append(out, checkHasIncoming(idx, rule, sev, "implements", "requirement")...)
		case "has_incoming(verifies)":
			out = append(out, checkHasIncoming(idx, rule, sev, "verifies", "requirement")...)
		case "orphan_code_or_task":
			out = append(out, checkOrphans(idx, rule, sev)...)
		case "no_active_refs_to_deprecated":
			out = append(out, checkDeprecatedRefs(idx, g, rule, sev)...)
		case "implicit_concept_use", "unreferenced_knowledge", "contradicting_policies", "stale_knowledge", "deviate_without_reason":
			out = append(out, evalKnowledgeAssert(g, rule, sev, opts)...)
		default:
			if edge, ok := parseHasIncoming(rule.Assert); ok {
				typeFilter := whenType(rule.When)
				out = append(out, checkHasIncoming(idx, rule, sev, edge, typeFilter)...)
				continue
			}
			if edge, ok := parseHasOutgoing(rule.Assert); ok {
				typeFilter := whenType(rule.When)
				out = append(out, checkHasOutgoing(idx, rule, sev, edge, typeFilter)...)
				continue
			}
			out = append(out, Violation{
				Rule: rule.ID, Severity: "error",
				Message: fmt.Sprintf("unknown assert %q", rule.Assert),
			})
		}
	}
	return out
}

func whenType(when map[string]any) string {
	if when == nil {
		return ""
	}
	if t, ok := when["type"].(string); ok {
		return t
	}
	return ""
}

func whenStatus(when map[string]any) string {
	if when == nil {
		return ""
	}
	if s, ok := when["status"].(string); ok {
		return s
	}
	return ""
}

func matchWhen(n *model.Node, when map[string]any) bool {
	if when == nil {
		return true
	}
	if t := whenType(when); t != "" && n.Type != t {
		return false
	}
	if s := whenStatus(when); s != "" && n.Status != s {
		return false
	}
	return true
}

func checkHasIncoming(idx index, rule schema.Rule, sev, edgeType, fallbackType string) []Violation {
	var out []Violation
	typeFilter := whenType(rule.When)
	if typeFilter == "" {
		typeFilter = fallbackType
	}
	for _, n := range idx.byID {
		if typeFilter != "" && n.Type != typeFilter {
			continue
		}
		if !matchWhen(n, rule.When) {
			continue
		}
		ok := false
		for _, e := range idx.in[n.ID] {
			if e.Type == edgeType {
				ok = true
				break
			}
		}
		if !ok {
			out = append(out, Violation{
				Rule: rule.ID, Severity: sev,
				Message: fmt.Sprintf("%s %s has no incoming %s edge", n.Type, n.ID, edgeType),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
		}
	}
	return out
}

func checkHasOutgoing(idx index, rule schema.Rule, sev, edgeType, typeFilter string) []Violation {
	var out []Violation
	for _, n := range idx.byID {
		if typeFilter != "" && n.Type != typeFilter {
			continue
		}
		if !matchWhen(n, rule.When) {
			continue
		}
		ok := false
		for _, e := range idx.out[n.ID] {
			if e.Type == edgeType {
				ok = true
				break
			}
		}
		if !ok {
			out = append(out, Violation{
				Rule: rule.ID, Severity: sev,
				Message: fmt.Sprintf("%s %s has no outgoing %s edge", n.Type, n.ID, edgeType),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
		}
	}
	return out
}

// FR-205: code/task not tied to any requirement.
func checkOrphans(idx index, rule schema.Rule, sev string) []Violation {
	var out []Violation
	for _, n := range idx.byID {
		if n.Type != "code" && n.Type != "task" {
			continue
		}
		if n.Status == "deprecated" {
			continue
		}
		linked := false
		if n.Type == "code" {
			for _, e := range idx.out[n.ID] {
				if e.Type != "implements" {
					continue
				}
				if t := idx.byID[e.To]; t != nil && (t.Type == "requirement" || t.Type == "acceptance_criterion") {
					linked = true
					break
				}
			}
		} else {
			// task: any path of depends_on then somehow to req is Phase 2-light —
			// require at least one edge involving a requirement/AC/design that implements req.
			linked = taskLinkedToRequirement(idx, n.ID, map[string]bool{})
		}
		if !linked {
			out = append(out, Violation{
				Rule: rule.ID, Severity: sev,
				Message: fmt.Sprintf("%s %s is not linked to any requirement", n.Type, n.ID),
				Path: n.SourcePath, Line: n.SourceLine, Node: n.ID,
			})
		}
	}
	return out
}

func taskLinkedToRequirement(idx index, id string, seen map[string]bool) bool {
	if seen[id] {
		return false
	}
	seen[id] = true
	n := idx.byID[id]
	if n == nil {
		return false
	}
	if n.Type == "requirement" || n.Type == "acceptance_criterion" {
		return true
	}
	for _, e := range idx.out[id] {
		if taskLinkedToRequirement(idx, e.To, seen) {
			return true
		}
	}
	for _, e := range idx.in[id] {
		// design/code implementing req may point elsewhere; follow neighbors lightly
		if e.Type == "depends_on" || e.Type == "implements" || e.Type == "verifies" {
			if taskLinkedToRequirement(idx, e.From, seen) {
				return true
			}
		}
	}
	return false
}

// FR-206: active nodes referencing deprecated nodes.
func checkDeprecatedRefs(idx index, g *model.Graph, rule schema.Rule, sev string) []Violation {
	var out []Violation
	for _, e := range g.Edges {
		from := idx.byID[e.From]
		to := idx.byID[e.To]
		if from == nil || to == nil {
			continue
		}
		if from.Status == "active" && to.Status == "deprecated" {
			out = append(out, Violation{
				Rule: rule.ID, Severity: sev,
				Message: fmt.Sprintf("active node %s references deprecated node %s via %s", e.From, e.To, e.Type),
				Path: e.SourcePath, Line: e.SourceLine, From: e.From, To: e.To, Node: e.From,
			})
		}
	}
	return out
}

func parseHasIncoming(assert string) (string, bool) {
	const p = "has_incoming("
	if !strings.HasPrefix(assert, p) || !strings.HasSuffix(assert, ")") {
		return "", false
	}
	return strings.TrimSuffix(strings.TrimPrefix(assert, p), ")"), true
}

func parseHasOutgoing(assert string) (string, bool) {
	const p = "has_outgoing("
	if !strings.HasPrefix(assert, p) || !strings.HasSuffix(assert, ")") {
		return "", false
	}
	return strings.TrimSuffix(strings.TrimPrefix(assert, p), ")"), true
}
