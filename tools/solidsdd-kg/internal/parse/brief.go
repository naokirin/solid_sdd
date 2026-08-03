package parse

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"gopkg.in/yaml.v3"
)

type briefFile struct {
	ChangeID         string      `json:"change_id"`
	InScope          []scopedItem `json:"in_scope"`
	SuccessCriteria  []scopedItem `json:"success_criteria"`
}

type scopedItem struct {
	ID   string `json:"id"`
	Text string `json:"text"`
}

// ChangeBriefs loads requirement / AC nodes from ChangeBrief JSON files.
func ChangeBriefs(paths []string, sep string, g *model.Graph) {
	for _, path := range paths {
		data, err := os.ReadFile(path)
		if err != nil {
			g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: err.Error()})
			continue
		}
		var b briefFile
		if err := json.Unmarshal(data, &b); err != nil {
			g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: fmt.Sprintf("json: %v", err)})
			continue
		}
		changeID := b.ChangeID
		if changeID == "" {
			// fall back to parent dir name
			changeID = filepath.Base(filepath.Dir(path))
		}
		for _, item := range b.InScope {
			if item.ID == "" {
				continue
			}
			id := changeID + sep + item.ID
			g.Nodes = append(g.Nodes, model.Node{
				ID:         id,
				Type:       "requirement",
				Title:      truncate(item.Text, 120),
				Status:     "active",
				SourcePath: path,
				SourceLine: 1,
				Body:       item.Text,
				Layer:      "brief",
			})
		}
		for _, item := range b.SuccessCriteria {
			if item.ID == "" {
				continue
			}
			id := changeID + sep + item.ID
			g.Nodes = append(g.Nodes, model.Node{
				ID:         id,
				Type:       "acceptance_criterion",
				Title:      truncate(item.Text, 120),
				Status:     "active",
				SourcePath: path,
				SourceLine: 1,
				Body:       item.Text,
				Layer:      "brief",
			})
		}
	}
}

func truncate(s string, n int) string {
	s = strings.TrimSpace(s)
	if len(s) <= n {
		return s
	}
	return s[:n-1] + "…"
}

type linksFile struct {
	Edges []struct {
		Type   string `yaml:"type" json:"type"`
		From   string `yaml:"from" json:"from"`
		To     string `yaml:"to" json:"to"`
		Reason string `yaml:"reason" json:"reason"`
	} `yaml:"edges" json:"edges"`
}

// LinksFile loads explicit edges from links.yaml.
func LinksFile(path string, g *model.Graph) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return
		}
		g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: err.Error()})
		return
	}
	var lf linksFile
	if err := yaml.Unmarshal(data, &lf); err != nil {
		g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: fmt.Sprintf("yaml: %v", err)})
		return
	}
	for i, e := range lf.Edges {
		if e.Type == "" || e.From == "" || e.To == "" {
			g.Issues = append(g.Issues, model.ParseIssue{
				Path: path, Line: i + 1,
				Message: "links edge requires type, from, and to",
			})
			continue
		}
		g.Edges = append(g.Edges, model.Edge{
			Type:       e.Type,
			From:       e.From,
			To:         e.To,
			Reason:     e.Reason,
			SourcePath: path,
			SourceLine: i + 1,
		})
	}
}
