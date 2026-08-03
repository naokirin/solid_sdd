package store

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/naokirin/solid_sdd/tools/solidsdd-kg/internal/model"

	_ "modernc.org/sqlite"
)

// Open creates/opens the derived SQLite database.
func Open(dbPath string) (*sql.DB, error) {
	if err := os.MkdirAll(filepath.Dir(dbPath), 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return db, nil
}

// ResetSchema drops and recreates tables (full rebuild).
func ResetSchema(db *sql.DB) error {
	stmts := []string{
		`DROP TABLE IF EXISTS edges`,
		`DROP TABLE IF EXISTS nodes`,
		`DROP TABLE IF EXISTS parse_issues`,
		`CREATE TABLE nodes (
			id TEXT PRIMARY KEY,
			type TEXT NOT NULL,
			title TEXT NOT NULL,
			status TEXT NOT NULL,
			aliases TEXT,
			scope TEXT,
			supersedes TEXT,
			superseded_by TEXT,
			verified_at TEXT,
			confidence TEXT,
			owner TEXT,
			tags TEXT,
			source_path TEXT,
			source_line INTEGER,
			layer TEXT,
			body TEXT
		)`,
		`CREATE TABLE edges (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			type TEXT NOT NULL,
			"from" TEXT NOT NULL,
			"to" TEXT NOT NULL,
			source_path TEXT,
			source_line INTEGER,
			reason TEXT
		)`,
		`CREATE INDEX idx_edges_from ON edges("from")`,
		`CREATE INDEX idx_edges_to ON edges("to")`,
		`CREATE TABLE parse_issues (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			path TEXT,
			line INTEGER,
			message TEXT
		)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			return fmt.Errorf("schema: %w", err)
		}
	}
	return nil
}

// WriteGraph replaces DB contents with the graph.
func WriteGraph(db *sql.DB, g *model.Graph) error {
	if err := ResetSchema(db); err != nil {
		return err
	}
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()

	nodeStmt, err := tx.Prepare(`INSERT INTO nodes (
		id, type, title, status, aliases, scope, supersedes, superseded_by,
		verified_at, confidence, owner, tags, source_path, source_line, layer, body
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
	if err != nil {
		return err
	}
	defer nodeStmt.Close()

	seen := map[string]struct{}{}
	for _, n := range g.Nodes {
		if _, ok := seen[n.ID]; ok {
			// keep first; duplicate IDs reported as issues by validate later if needed
			continue
		}
		seen[n.ID] = struct{}{}
		if _, err := nodeStmt.Exec(
			n.ID, n.Type, n.Title, n.Status,
			joinCSV(n.Aliases), n.Scope, joinCSV(n.Supersedes), joinCSV(n.SupersededBy),
			n.VerifiedAt, n.Confidence, n.Owner, joinCSV(n.Tags),
			n.SourcePath, n.SourceLine, n.Layer, n.Body,
		); err != nil {
			return fmt.Errorf("insert node %s: %w", n.ID, err)
		}
	}

	edgeStmt, err := tx.Prepare(`INSERT INTO edges (type, "from", "to", source_path, source_line, reason) VALUES (?, ?, ?, ?, ?, ?)`)
	if err != nil {
		return err
	}
	defer edgeStmt.Close()
	for _, e := range g.Edges {
		if _, err := edgeStmt.Exec(e.Type, e.From, e.To, e.SourcePath, e.SourceLine, e.Reason); err != nil {
			return err
		}
	}

	issueStmt, err := tx.Prepare(`INSERT INTO parse_issues (path, line, message) VALUES (?, ?, ?)`)
	if err != nil {
		return err
	}
	defer issueStmt.Close()
	for _, iss := range g.Issues {
		if _, err := issueStmt.Exec(iss.Path, iss.Line, iss.Message); err != nil {
			return err
		}
	}

	return tx.Commit()
}

// LoadGraph reads nodes/edges/issues from an existing DB.
func LoadGraph(db *sql.DB) (*model.Graph, error) {
	g := &model.Graph{}
	rows, err := db.Query(`SELECT id, type, title, status, aliases, scope, supersedes, superseded_by,
		verified_at, confidence, owner, tags, source_path, source_line, layer, body FROM nodes`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var n model.Node
		var aliases, supersedes, supersededBy, tags string
		if err := rows.Scan(
			&n.ID, &n.Type, &n.Title, &n.Status, &aliases, &n.Scope, &supersedes, &supersededBy,
			&n.VerifiedAt, &n.Confidence, &n.Owner, &tags, &n.SourcePath, &n.SourceLine, &n.Layer, &n.Body,
		); err != nil {
			return nil, err
		}
		n.Aliases = splitCSV(aliases)
		n.Supersedes = splitCSV(supersedes)
		n.SupersededBy = splitCSV(supersededBy)
		n.Tags = splitCSV(tags)
		g.Nodes = append(g.Nodes, n)
	}
	erows, err := db.Query(`SELECT type, "from", "to", source_path, source_line, reason FROM edges`)
	if err != nil {
		return nil, err
	}
	defer erows.Close()
	for erows.Next() {
		var e model.Edge
		if err := erows.Scan(&e.Type, &e.From, &e.To, &e.SourcePath, &e.SourceLine, &e.Reason); err != nil {
			return nil, err
		}
		g.Edges = append(g.Edges, e)
	}
	irows, err := db.Query(`SELECT path, line, message FROM parse_issues`)
	if err != nil {
		return nil, err
	}
	defer irows.Close()
	for irows.Next() {
		var iss model.ParseIssue
		if err := irows.Scan(&iss.Path, &iss.Line, &iss.Message); err != nil {
			return nil, err
		}
		g.Issues = append(g.Issues, iss)
	}
	return g, nil
}

func joinCSV(xs []string) string {
	if len(xs) == 0 {
		return ""
	}
	return strings.Join(xs, ",")
}

func splitCSV(s string) []string {
	if s == "" {
		return nil
	}
	return strings.Split(s, ",")
}
