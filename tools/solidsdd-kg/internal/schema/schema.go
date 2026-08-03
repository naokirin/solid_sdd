package schema

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// Schema is .solidsdd/kg/schema.yaml
type Schema struct {
	SchemaVersion int                   `yaml:"schema_version"`
	NodeTypes     map[string]NodeType   `yaml:"node_types"`
	EdgeTypes     map[string]EdgeType   `yaml:"edge_types"`
	Rules         []Rule                `yaml:"rules"`
}

type NodeType struct {
	Required []string `yaml:"required"`
	Statuses []string `yaml:"statuses"`
}

type EdgeType struct {
	From       []string `yaml:"from"`
	To         []string `yaml:"to"`
	DeclaredBy string   `yaml:"declared_by"`
}

type Rule struct {
	ID       string `yaml:"id"`
	Severity string `yaml:"severity"`
	Assert   string `yaml:"assert"`
}

func Load(path string) (Schema, error) {
	var s Schema
	data, err := os.ReadFile(path)
	if err != nil {
		return s, err
	}
	if err := yaml.Unmarshal(data, &s); err != nil {
		return s, fmt.Errorf("parse schema %s: %w", path, err)
	}
	if s.NodeTypes == nil {
		s.NodeTypes = map[string]NodeType{}
	}
	if s.EdgeTypes == nil {
		s.EdgeTypes = map[string]EdgeType{}
	}
	return s, nil
}

func (s Schema) HasNodeType(t string) bool {
	_, ok := s.NodeTypes[t]
	return ok
}

func (s Schema) HasEdgeType(t string) bool {
	_, ok := s.EdgeTypes[t]
	return ok
}

// KnownEdgeKeys are frontmatter keys that declare outbound edges.
func KnownEdgeKeys() []string {
	return []string{
		"derives_from",
		"refines",
		"implements",
		"verifies",
		"depends_on",
		"rationale",
		"contradicts",
		"supersedes",
		"deviates_from",
		"mentions",
		"superseded_by",
	}
}
