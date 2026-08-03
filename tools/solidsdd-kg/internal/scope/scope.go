package scope

import (
	"sort"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

// Chain returns scope and its parents from most specific to root.
// Example: org.security.auth -> [org.security.auth, org.security, org]
func Chain(scope string) []string {
	scope = strings.TrimSpace(scope)
	if scope == "" {
		return nil
	}
	parts := strings.Split(scope, ".")
	out := make([]string, 0, len(parts))
	for i := len(parts); i >= 1; i-- {
		out = append(out, strings.Join(parts[:i], "."))
	}
	return out
}

// Covers reports whether parentScope applies to childScope (FR-304).
func Covers(parentScope, childScope string) bool {
	if parentScope == "" {
		return true
	}
	if parentScope == childScope {
		return true
	}
	return strings.HasPrefix(childScope+".", parentScope+".")
}

// Policy is a policy node applicable to a scope.
type Policy struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Scope    string `json:"scope"`
	Status   string `json:"status"`
	Distance int    `json:"distance"` // 0 = exact scope, higher = ancestor
}

// ResolvePolicies lists active policies that apply to targetScope.
// More specific scopes first; within same distance, by id (FR-304).
func ResolvePolicies(g *model.Graph, targetScope string) []Policy {
	var out []Policy
	for i := range g.Nodes {
		n := &g.Nodes[i]
		if n.Type != "policy" || n.Status != "active" {
			continue
		}
		if !Covers(n.Scope, targetScope) {
			continue
		}
		dist := scopeDistance(n.Scope, targetScope)
		out = append(out, Policy{
			ID: n.ID, Title: n.Title, Scope: n.Scope, Status: n.Status, Distance: dist,
		})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Distance != out[j].Distance {
			return out[i].Distance < out[j].Distance
		}
		return out[i].ID < out[j].ID
	})
	return out
}

func scopeDistance(policyScope, target string) int {
	if policyScope == target {
		return 0
	}
	chain := Chain(target)
	for i, s := range chain {
		if s == policyScope {
			return i
		}
	}
	return len(chain)
}
