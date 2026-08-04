package contextx

import (
	"fmt"
	"sort"
	"strings"
	"unicode/utf8"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/query"
)

// Options for context extraction (FR-401..405).
type Options struct {
	Hops         int
	IncludeTypes map[string]bool // empty = default priority set
	BudgetChars  int             // approximate token budget via chars/4; 0 = unlimited
}

// priority: policy/invariant > concept > decision > requirement (FR-404)
func typePriority(t string) int {
	switch t {
	case "policy", "invariant":
		return 0
	case "concept":
		return 1
	case "decision", "lesson", "pattern":
		return 2
	case "requirement", "acceptance_criterion":
		return 3
	default:
		return 4
	}
}

// Extract builds a single Markdown context pack for start (FR-401).
func Extract(g *model.Graph, start string, opts Options) (string, error) {
	n := g.NodeByID(start)
	if n == nil {
		return "", fmt.Errorf("unknown node id %q", start)
	}
	hops := opts.Hops
	if hops <= 0 {
		hops = 2
	}

	include := opts.IncludeTypes
	// Always walk; filter at render time if include set.
	hits := query.Impact(g, start, query.Both, hops, nil)

	// FR-405: transitively follow derives_from / refines from start and hits
	extra := map[string]bool{}
	followNormative(g, start, extra, 8)
	for _, h := range hits {
		followNormative(g, h.ID, extra, 8)
	}

	nodes := map[string]*model.Node{start: n}
	for _, h := range hits {
		if nn := g.NodeByID(h.ID); nn != nil {
			nodes[h.ID] = nn
		}
	}
	for id := range extra {
		if nn := g.NodeByID(id); nn != nil {
			nodes[id] = nn
		}
	}

	type item struct {
		n    *model.Node
		hops int
		full bool
	}
	var items []item
	for id, nn := range nodes {
		if len(include) > 0 && id != start && !include[nn.Type] {
			// still keep policy/invariant/concept from FR-405
			if !(nn.Type == "policy" || nn.Type == "invariant" || nn.Type == "concept" || nn.Type == "decision" || nn.Type == "lesson") {
				continue
			}
		}
		h := 0
		if id != start {
			h = 1
			for _, hit := range hits {
				if hit.ID == id {
					h = hit.Hops
					break
				}
			}
		}
		items = append(items, item{n: nn, hops: h, full: true})
	}

	sort.Slice(items, func(i, j int) bool {
		pi, pj := typePriority(items[i].n.Type), typePriority(items[j].n.Type)
		if pi != pj {
			return pi < pj
		}
		mi, mj := model.MaturityRank(items[i].n), model.MaturityRank(items[j].n)
		if mi != mj {
			return mi < mj
		}
		if items[i].hops != items[j].hops {
			return items[i].hops < items[j].hops
		}
		return items[i].n.ID < items[j].n.ID
	})

	// FR-402/403: fit budget — distant nodes degrade to one-line summary
	budget := opts.BudgetChars
	if budget <= 0 && opts.BudgetChars == 0 {
		// allow token-style budgets passed as chars already
	}
	render := func(fullOnly bool) string {
		var b strings.Builder
		b.WriteString("# Context pack\n\n")
		fmt.Fprintf(&b, "Start: `%s` (%s) — hops≤%d\n\n", start, n.Type, hops)
		for _, it := range items {
			full := it.full && (fullOnly || it.hops <= 1 || typePriority(it.n.Type) <= 1)
			b.WriteString(renderNode(it.n, full))
			b.WriteString("\n")
		}
		return b.String()
	}

	out := render(true)
	if budget > 0 && utf8.RuneCountInString(out) > budget {
		// degrade: only start + priority≤1 full; others one-line
		for i := range items {
			if items[i].n.ID == start || typePriority(items[i].n.Type) <= 1 {
				items[i].full = true
			} else {
				items[i].full = false
			}
		}
		out = render(false)
		if utf8.RuneCountInString(out) > budget {
			// keep only priority 0-1 and start
			filtered := items[:0]
			for _, it := range items {
				if it.n.ID == start || typePriority(it.n.Type) <= 1 {
					filtered = append(filtered, it)
				}
			}
			items = filtered
			out = render(false)
		}
	}
	var facetNodes []*model.Node
	for _, it := range items {
		facetNodes = append(facetNodes, it.n)
	}
	out += FacetSections(facetNodes)
	return out, nil
}

func followNormative(g *model.Graph, id string, seen map[string]bool, depth int) {
	if depth <= 0 || seen[id] {
		return
	}
	seen[id] = true
	for _, e := range g.Edges {
		if e.From != id {
			continue
		}
		if e.Type != "derives_from" && e.Type != "refines" && e.Type != "rationale" {
			continue
		}
		followNormative(g, e.To, seen, depth-1)
	}
}

func renderNode(n *model.Node, full bool) string {
	var b strings.Builder
	fmt.Fprintf(&b, "## %s `%s`\n\n", n.Type, n.ID)
	fmt.Fprintf(&b, "- title: %s\n", n.Title)
	fmt.Fprintf(&b, "- status: %s\n", n.Status)
	fmt.Fprintf(&b, "- maturity: %s\n", model.EffectiveMaturity(n))
	if len(n.Facets) > 0 {
		fmt.Fprintf(&b, "- facets: %s\n", strings.Join(n.Facets, ", "))
	}
	if n.Scope != "" {
		fmt.Fprintf(&b, "- scope: %s\n", n.Scope)
	}
	if !full {
		b.WriteString("\n")
		return b.String()
	}
	body := strings.TrimSpace(n.Body)
	if body != "" {
		b.WriteString("\n")
		b.WriteString(body)
		b.WriteString("\n")
	} else {
		b.WriteString("\n")
	}
	return b.String()
}

// FacetSections appends optional Markdown grouping by facet when any node has facets.
func FacetSections(nodes []*model.Node) string {
	by := map[string][]*model.Node{}
	for _, n := range nodes {
		if n == nil {
			continue
		}
		for _, f := range n.Facets {
			by[f] = append(by[f], n)
		}
	}
	if len(by) == 0 {
		return ""
	}
	order := model.AllowedFacets
	var b strings.Builder
	b.WriteString("\n# Facet index\n\n")
	for _, f := range order {
		ns := by[f]
		if len(ns) == 0 {
			continue
		}
		fmt.Fprintf(&b, "## %s\n\n", f)
		for _, n := range ns {
			fmt.Fprintf(&b, "- `%s` (%s, maturity=%s)\n", n.ID, n.Type, model.EffectiveMaturity(n))
		}
		b.WriteString("\n")
	}
	return b.String()
}

// ParseBudget parses "30k" / "8000" style budgets into rune/char budget.
// Approximation: 1 token ≈ 4 chars.
func ParseBudget(s string) (int, error) {
	s = strings.TrimSpace(strings.ToLower(s))
	if s == "" || s == "0" {
		return 0, nil
	}
	mult := 1
	if strings.HasSuffix(s, "k") {
		mult = 1000
		s = strings.TrimSuffix(s, "k")
	}
	var n int
	_, err := fmt.Sscanf(s, "%d", &n)
	if err != nil {
		return 0, fmt.Errorf("invalid budget %q", s)
	}
	tokens := n * mult
	return tokens * 4, nil
}
