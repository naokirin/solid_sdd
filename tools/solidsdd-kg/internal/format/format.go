package format

import (
	"bytes"
	"fmt"
	"os"
	"strings"

	"gopkg.in/yaml.v3"
)

// Preferred key order for knowledge frontmatter (FR-701).
var keyOrder = []string{
	"id",
	"type",
	"title",
	"status",
	"scope",
	"aliases",
	"tags",
	"owner",
	"confidence",
	"verified_at",
	"supersedes",
	"superseded_by",
	"derives_from",
	"refines",
	"implements",
	"verifies",
	"depends_on",
	"rationale",
	"contradicts",
	"deviates_from",
	"mentions",
}

// File normalizes frontmatter key/array order; body prose is unchanged.
func File(path string, write bool) (changed bool, err error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return false, err
	}
	if !bytes.HasPrefix(data, []byte("---\n")) && !bytes.HasPrefix(data, []byte("---\r\n")) {
		return false, fmt.Errorf("%s: no frontmatter", path)
	}
	fm, body, err := split(data)
	if err != nil {
		return false, err
	}

	var raw yaml.Node
	if err := yaml.Unmarshal(fm, &raw); err != nil {
		return false, fmt.Errorf("%s: %w", path, err)
	}
	if raw.Kind != yaml.DocumentNode || len(raw.Content) == 0 {
		return false, fmt.Errorf("%s: empty frontmatter", path)
	}
	doc := raw.Content[0]
	if doc.Kind != yaml.MappingNode {
		return false, fmt.Errorf("%s: frontmatter must be a mapping", path)
	}

	normalizeMapping(doc)

	var buf bytes.Buffer
	enc := yaml.NewEncoder(&buf)
	enc.SetIndent(2)
	if err := enc.Encode(doc); err != nil {
		return false, err
	}
	_ = enc.Close()
	normalizedFM := buf.Bytes()
	// encoder adds trailing newline
	normalizedFM = bytes.TrimSuffix(normalizedFM, []byte("\n"))

	var out bytes.Buffer
	out.WriteString("---\n")
	out.Write(normalizedFM)
	out.WriteString("\n---\n")
	out.Write(body)

	newData := out.Bytes()
	if bytes.Equal(data, newData) {
		return false, nil
	}
	if write {
		if err := os.WriteFile(path, newData, 0o644); err != nil {
			return false, err
		}
	}
	return true, nil
}

func split(data []byte) (fm []byte, body []byte, err error) {
	text := string(data)
	rest := text[3:]
	if strings.HasPrefix(rest, "\r\n") {
		rest = rest[2:]
	} else if strings.HasPrefix(rest, "\n") {
		rest = rest[1:]
	}
	idx := strings.Index(rest, "\n---")
	if idx < 0 {
		return nil, nil, fmt.Errorf("unterminated frontmatter")
	}
	fm = []byte(rest[:idx])
	after := rest[idx+1:]
	after = strings.TrimPrefix(after, "---")
	after = strings.TrimPrefix(after, "\r\n")
	after = strings.TrimPrefix(after, "\n")
	return fm, []byte(after), nil
}

func normalizeMapping(doc *yaml.Node) {
	type kv struct {
		k, v *yaml.Node
	}
	var pairs []kv
	for i := 0; i+1 < len(doc.Content); i += 2 {
		pairs = append(pairs, kv{doc.Content[i], doc.Content[i+1]})
	}

	orderIndex := map[string]int{}
	for i, k := range keyOrder {
		orderIndex[k] = i
	}

	// sort arrays under known list keys
	for _, p := range pairs {
		if p.v.Kind == yaml.SequenceNode {
			sortScalarSeq(p.v)
		}
	}

	// stable sort by preferred order, then alpha for unknown keys
	for i := 0; i < len(pairs); i++ {
		for j := i + 1; j < len(pairs); j++ {
			if lessKey(pairs[j].k.Value, pairs[i].k.Value, orderIndex) {
				pairs[i], pairs[j] = pairs[j], pairs[i]
			}
		}
	}

	doc.Content = doc.Content[:0]
	for _, p := range pairs {
		doc.Content = append(doc.Content, p.k, p.v)
	}
}

func lessKey(a, b string, order map[string]int) bool {
	ia, oka := order[a]
	ib, okb := order[b]
	if oka && okb {
		return ia < ib
	}
	if oka {
		return true
	}
	if okb {
		return false
	}
	return a < b
}

func sortScalarSeq(seq *yaml.Node) {
	nodes := seq.Content
	for i := 0; i < len(nodes); i++ {
		for j := i + 1; j < len(nodes); j++ {
			if nodes[j].Kind == yaml.ScalarNode && nodes[i].Kind == yaml.ScalarNode {
				if nodes[j].Value < nodes[i].Value {
					nodes[i], nodes[j] = nodes[j], nodes[i]
				}
			}
		}
	}
}
