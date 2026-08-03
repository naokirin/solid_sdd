package parse

import (
	"bufio"
	"os"
	"regexp"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"
)

var (
	scenarioRe = regexp.MustCompile(`^\s*Scenario(?: Outline)?:\s*(.+)\s*$`)
	tagLineRe  = regexp.MustCompile(`^\s*(@.+)\s*$`)
	tagTokenRe = regexp.MustCompile(`@([A-Za-z0-9_.-]+)`)
)

// Features registers Scenario nodes and records tag references as mentions edges
// when a change_id prefix is provided via path heuristics is not enough —
// tags like @R1 are change-local. We emit edges only when the tag looks like a
// full graph id (contains "/"); otherwise we register alias tags on the scenario
// node for later phases.
func Features(paths []string, g *model.Graph) {
	for _, path := range paths {
		f, err := os.Open(path)
		if err != nil {
			g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: 1, Message: err.Error()})
			continue
		}
		sc := bufio.NewScanner(f)
		lineNo := 0
		var pendingTags []string
		scenarioIdx := 0
		for sc.Scan() {
			lineNo++
			line := sc.Text()
			if tagLineRe.MatchString(line) {
				for _, m := range tagTokenRe.FindAllStringSubmatch(line, -1) {
					pendingTags = append(pendingTags, m[1])
				}
				continue
			}
			if m := scenarioRe.FindStringSubmatch(line); m != nil {
				scenarioIdx++
				title := strings.TrimSpace(m[1])
				id := featureScenarioID(path, scenarioIdx)
				g.Nodes = append(g.Nodes, model.Node{
					ID:         id,
					Type:       "acceptance_criterion",
					Title:      title,
					Status:     "active",
					Tags:       append([]string{}, pendingTags...),
					SourcePath: path,
					SourceLine: lineNo,
					Layer:      "feature",
				})
				pendingTags = nil
				continue
			}
			// non-tag, non-scenario resets pending tags only after Feature/Rule headers keep them —
			// Gherkin applies tags to the next Scenario; blank lines ok; other keywords clear.
			trim := strings.TrimSpace(line)
			if trim == "" || strings.HasPrefix(trim, "#") {
				continue
			}
			if strings.HasPrefix(trim, "Given") || strings.HasPrefix(trim, "When") ||
				strings.HasPrefix(trim, "Then") || strings.HasPrefix(trim, "And") ||
				strings.HasPrefix(trim, "But") || strings.HasPrefix(trim, "*") {
				continue
			}
			if strings.HasPrefix(trim, "Feature:") || strings.HasPrefix(trim, "Rule:") ||
				strings.HasPrefix(trim, "Background:") {
				pendingTags = nil
			}
		}
		_ = f.Close()
		if err := sc.Err(); err != nil {
			g.Issues = append(g.Issues, model.ParseIssue{Path: path, Line: lineNo, Message: err.Error()})
		}
	}
}

func featureScenarioID(path string, idx int) string {
	base := strings.TrimSuffix(filepathBaseNoExt(path), "")
	return "feature:" + base + "/S" + itoa(idx)
}

func filepathBaseNoExt(path string) string {
	base := path
	if i := strings.LastIndexAny(base, `/\`); i >= 0 {
		base = base[i+1:]
	}
	if i := strings.LastIndex(base, "."); i >= 0 {
		base = base[:i]
	}
	return base
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	var b [16]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + n%10)
		n /= 10
	}
	return string(b[i:])
}
