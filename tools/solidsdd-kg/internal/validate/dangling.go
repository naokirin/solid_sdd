package validate

import (
	"fmt"
	"sort"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

// Violation is a check finding.
type Violation struct {
	Rule     string `json:"rule"`
	Severity string `json:"severity"`
	Message  string `json:"message"`
	Path     string `json:"path,omitempty"`
	Line     int    `json:"line,omitempty"`
	From     string `json:"from,omitempty"`
	To       string `json:"to,omitempty"`
}

// DanglingReferences finds edges whose from/to IDs are missing.
func DanglingReferences(g *model.Graph) []Violation {
	ids := map[string]struct{}{}
	for _, n := range g.Nodes {
		ids[n.ID] = struct{}{}
	}
	var out []Violation
	for _, e := range g.Edges {
		if _, ok := ids[e.From]; !ok {
			out = append(out, Violation{
				Rule:     "NO_DANGLING_REFS",
				Severity: "error",
				Message:  fmt.Sprintf("edge %s: unknown from id %q", e.Type, e.From),
				Path:     e.SourcePath,
				Line:     e.SourceLine,
				From:     e.From,
				To:       e.To,
			})
		}
		if _, ok := ids[e.To]; !ok {
			out = append(out, Violation{
				Rule:     "NO_DANGLING_REFS",
				Severity: "error",
				Message:  fmt.Sprintf("edge %s: unknown to id %q", e.Type, e.To),
				Path:     e.SourcePath,
				Line:     e.SourceLine,
				From:     e.From,
				To:       e.To,
			})
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Path != out[j].Path {
			return out[i].Path < out[j].Path
		}
		if out[i].Line != out[j].Line {
			return out[i].Line < out[j].Line
		}
		return out[i].Message < out[j].Message
	})
	return out
}

// DuplicateIDs finds repeated node IDs across sources.
func DuplicateIDs(g *model.Graph) []Violation {
	seen := map[string]model.Node{}
	var out []Violation
	for _, n := range g.Nodes {
		if prev, ok := seen[n.ID]; ok {
			out = append(out, Violation{
				Rule:     "DUPLICATE_ID",
				Severity: "error",
				Message:  fmt.Sprintf("duplicate node id %q (also at %s:%d)", n.ID, prev.SourcePath, prev.SourceLine),
				Path:     n.SourcePath,
				Line:     n.SourceLine,
			})
			continue
		}
		seen[n.ID] = n
	}
	return out
}
