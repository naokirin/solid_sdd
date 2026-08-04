package parse

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/schema"
	"gopkg.in/yaml.v3"
)

var edgeKeySet = func() map[string]struct{} {
	m := map[string]struct{}{}
	for _, k := range schema.KnownEdgeKeys() {
		m[k] = struct{}{}
	}
	return m
}()

// KnowledgeFile parses one knowledge markdown file (frontmatter + body).
func KnowledgeFile(path string) (model.Node, []model.Edge, *model.ParseIssue) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Node{}, nil, &model.ParseIssue{Path: path, Line: 1, Message: err.Error()}
	}
	fm, body, lineOffset, err := splitFrontmatter(data)
	if err != nil {
		return model.Node{}, nil, &model.ParseIssue{Path: path, Line: 1, Message: err.Error()}
	}

	var raw map[string]any
	if err := yaml.Unmarshal(fm, &raw); err != nil {
		return model.Node{}, nil, &model.ParseIssue{Path: path, Line: 2, Message: fmt.Sprintf("frontmatter yaml: %v", err)}
	}

	n := model.Node{
		SourcePath: path,
		SourceLine: 2,
		Body:       body,
		Layer:      "knowledge",
	}
	var edges []model.Edge

	getString := func(key string) string {
		v, ok := raw[key]
		if !ok || v == nil {
			return ""
		}
		switch t := v.(type) {
		case string:
			return t
		case time.Time:
			return t.Format("2006-01-02")
		default:
			return fmt.Sprint(t)
		}
	}
	getStrings := func(key string) []string {
		v, ok := raw[key]
		if !ok || v == nil {
			return nil
		}
		switch t := v.(type) {
		case []any:
			out := make([]string, 0, len(t))
			for _, item := range t {
				out = append(out, fmt.Sprint(item))
			}
			return out
		case []string:
			return t
		case string:
			if t == "" {
				return nil
			}
			return []string{t}
		default:
			return nil
		}
	}

	n.ID = getString("id")
	n.Type = getString("type")
	n.Title = getString("title")
	n.Status = getString("status")
	n.Scope = getString("scope")
	n.VerifiedAt = getString("verified_at")
	n.Confidence = getString("confidence")
	n.Maturity = getString("maturity")
	n.Owner = getString("owner")
	n.Aliases = getStrings("aliases")
	n.Tags = getStrings("tags")
	n.Facets = getStrings("facets")
	n.Supersedes = getStrings("supersedes")
	n.SupersededBy = getStrings("superseded_by")

	if n.ID == "" {
		return n, nil, &model.ParseIssue{Path: path, Line: lineOffset, Message: "missing required frontmatter field: id"}
	}
	if n.Type == "" {
		return n, nil, &model.ParseIssue{Path: path, Line: lineOffset, Message: "missing required frontmatter field: type"}
	}
	if n.Title == "" {
		return n, nil, &model.ParseIssue{Path: path, Line: lineOffset, Message: "missing required frontmatter field: title"}
	}
	if n.Status == "" {
		n.Status = "active"
	}

	for key := range raw {
		if _, ok := edgeKeySet[key]; !ok {
			continue
		}
		for _, pe := range parseEdgeList(raw[key]) {
			if pe.To == "" {
				continue
			}
			edges = append(edges, model.Edge{
				Type:       key,
				From:       n.ID,
				To:         pe.To,
				Reason:     pe.Reason,
				SourcePath: path,
				SourceLine: lineOffset,
			})
		}
	}

	return n, edges, nil
}

type parsedEdge struct {
	To     string
	Reason string
}

func parseEdgeList(v any) []parsedEdge {
	if v == nil {
		return nil
	}
	switch t := v.(type) {
	case string:
		if strings.TrimSpace(t) == "" {
			return nil
		}
		return []parsedEdge{{To: strings.TrimSpace(t)}}
	case []any:
		var out []parsedEdge
		for _, item := range t {
			switch it := item.(type) {
			case string:
				if s := strings.TrimSpace(it); s != "" {
					out = append(out, parsedEdge{To: s})
				}
			case map[string]any:
				to := firstString(it, "to", "target", "id")
				reason := firstString(it, "reason")
				if to != "" {
					out = append(out, parsedEdge{To: to, Reason: reason})
				}
			}
		}
		return out
	case []string:
		out := make([]parsedEdge, 0, len(t))
		for _, s := range t {
			if s = strings.TrimSpace(s); s != "" {
				out = append(out, parsedEdge{To: s})
			}
		}
		return out
	default:
		return nil
	}
}

func firstString(m map[string]any, keys ...string) string {
	for _, k := range keys {
		if v, ok := m[k]; ok && v != nil {
			if s, ok := v.(string); ok {
				return strings.TrimSpace(s)
			}
			return strings.TrimSpace(fmt.Sprint(v))
		}
	}
	return ""
}

func splitFrontmatter(data []byte) (fm []byte, body string, bodyStartLine int, err error) {
	text := string(data)
	if !strings.HasPrefix(text, "---\n") && !strings.HasPrefix(text, "---\r\n") {
		return nil, "", 1, fmt.Errorf("expected YAML frontmatter starting with ---")
	}
	rest := text[3:]
	if strings.HasPrefix(rest, "\r\n") {
		rest = rest[2:]
	} else if strings.HasPrefix(rest, "\n") {
		rest = rest[1:]
	}
	idx := strings.Index(rest, "\n---")
	if idx < 0 {
		return nil, "", 1, fmt.Errorf("unterminated YAML frontmatter")
	}
	fm = []byte(rest[:idx])
	after := rest[idx+1:] // starts with ---
	after = strings.TrimPrefix(after, "---")
	after = strings.TrimPrefix(after, "\r\n")
	after = strings.TrimPrefix(after, "\n")
	bodyStartLine = 2 + bytes.Count(fm, []byte("\n")) + 1
	return fm, after, bodyStartLine, nil
}

// KnowledgeDir walks a knowledge directory tree.
func KnowledgeDir(dir string, g *model.Graph) {
	_ = filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: err.Error()})
			return nil
		}
		if d.IsDir() {
			return nil
		}
		if !strings.HasSuffix(strings.ToLower(path), ".md") {
			return nil
		}
		n, edges, issue := KnowledgeFile(path)
		if issue != nil {
			g.Issues = append(g.Issues, *issue)
			return nil
		}
		g.Nodes = append(g.Nodes, n)
		g.Edges = append(g.Edges, edges...)
		return nil
	})
}

var (
	headingAnchorRe = regexp.MustCompile(`(?m)^(#{1,6})\s+(.+?)\s*\{#([A-Za-z0-9_./:-]+)\}\s*$`)
	htmlMetaRe      = regexp.MustCompile(`(?m)<!--\s*@([a-zA-Z0-9_]+)\s+([^>]*?)-->`)
)

// SpecFile parses document-anchor markdown (optional Phase 1 support).
func SpecFile(path string, g *model.Graph) {
	data, err := os.ReadFile(path)
	if err != nil {
		g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: err.Error()})
		return
	}
	lines := strings.Split(string(data), "\n")
	type pending struct {
		id   string
		line int
		title string
	}
	var current *pending

	flush := func() {}
	_ = flush

	for i, line := range lines {
		lineNo := i + 1
		if m := headingAnchorRe.FindStringSubmatch(line); m != nil {
			id := m[3]
			title := strings.TrimSpace(m[2])
			// strip leading id echo from title if present
			title = strings.TrimSpace(strings.TrimPrefix(title, id))
			if title == "" {
				title = id
			}
			current = &pending{id: id, line: lineNo, title: title}
			g.Nodes = append(g.Nodes, model.Node{
				ID:         id,
				Type:       "design", // default; @node may override via later pass
				Title:      title,
				Status:     "active",
				SourcePath: path,
				SourceLine: lineNo,
				Layer:      "spec",
			})
			continue
		}
		if current == nil {
			continue
		}
		for _, m := range htmlMetaRe.FindAllStringSubmatch(line, -1) {
			directive := m[1]
			args := strings.TrimSpace(m[2])
			if directive == "node" {
				fields := parseHTMLAttrs(args)
				n := g.NodeByID(current.id)
				if n != nil {
					if t := fields["type"]; t != "" {
						n.Type = t
					}
					if s := fields["status"]; s != "" {
						n.Status = s
					}
				}
				continue
			}
			if _, ok := edgeKeySet[directive]; ok {
				for _, to := range strings.Fields(args) {
					g.Edges = append(g.Edges, model.Edge{
						Type:       directive,
						From:       current.id,
						To:         to,
						SourcePath: path,
						SourceLine: lineNo,
					})
				}
			}
		}
	}
}

func parseHTMLAttrs(s string) map[string]string {
	out := map[string]string{}
	for _, part := range strings.Fields(s) {
		k, v, ok := strings.Cut(part, "=")
		if !ok {
			continue
		}
		out[k] = strings.Trim(v, `"'`)
	}
	return out
}
