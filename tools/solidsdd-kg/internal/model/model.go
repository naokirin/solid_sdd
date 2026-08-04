package model

// AllowedMaturity values for knowledge epistemic certainty (not lifecycle status).
var AllowedMaturity = []string{"hypothesized", "confirmed", "canonical"}

// AllowedFacets optional semantic facets (intent-inspired; complements Type).
var AllowedFacets = []string{"vocabulary", "invariant", "decider", "acceptance-property"}

// Node is a graph vertex loaded from text sources.
type Node struct {
	ID           string
	Type         string
	Title        string
	Status       string
	Aliases      []string
	Scope        string
	Supersedes   []string
	SupersededBy []string
	VerifiedAt   string
	Confidence   string
	Maturity     string   // hypothesized | confirmed | canonical; empty → EffectiveMaturity = confirmed
	Facets       []string // optional: vocabulary | invariant | decider | acceptance-property
	Owner        string
	Tags         []string
	SourcePath   string
	SourceLine   int
	Body         string
	Layer        string // knowledge | brief | feature | spec | links
}

// EffectiveMaturity returns n.Maturity or "confirmed" when unset/unknown.
func EffectiveMaturity(n *Node) string {
	if n == nil {
		return "confirmed"
	}
	switch n.Maturity {
	case "hypothesized", "confirmed", "canonical":
		return n.Maturity
	default:
		return "confirmed"
	}
}

// MaturityRank sorts canonical before confirmed before hypothesized (lower is better).
func MaturityRank(n *Node) int {
	switch EffectiveMaturity(n) {
	case "canonical":
		return 0
	case "confirmed":
		return 1
	default:
		return 2
	}
}

// Edge is a directed typed relation.
type Edge struct {
	Type       string
	From       string
	To         string
	SourcePath string
	SourceLine int
	Reason     string // required for some edge types later
}

// ParseIssue is a non-fatal parse problem.
type ParseIssue struct {
	Path    string
	Line    int
	Message string
}

// Graph is the in-memory parse result before indexing.
type Graph struct {
	Nodes  []Node
	Edges  []Edge
	Issues []ParseIssue
}

// NodeByID returns the first node with id, or nil.
func (g *Graph) NodeByID(id string) *Node {
	for i := range g.Nodes {
		if g.Nodes[i].ID == id {
			return &g.Nodes[i]
		}
	}
	return nil
}
