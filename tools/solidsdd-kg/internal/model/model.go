package model

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
	Owner        string
	Tags         []string
	SourcePath   string
	SourceLine   int
	Body         string
	Layer        string // knowledge | brief | feature | spec | links
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
