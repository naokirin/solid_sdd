package store

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"
)

// SourceMeta is a scanned input file fingerprint.
type SourceMeta struct {
	Path    string
	Hash    string
	ModTime int64
}

// EnsureMetaSchema creates tables used for incremental build (FR-102).
func EnsureMetaSchema(db *sql.DB) error {
	_, err := db.Exec(`
CREATE TABLE IF NOT EXISTS build_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_files (
  path TEXT PRIMARY KEY,
  hash TEXT NOT NULL,
  mtime INTEGER NOT NULL
);
`)
	return err
}

// FileHash returns sha256 hex of file contents.
func FileHash(path string) (string, int64, error) {
	st, err := os.Stat(path)
	if err != nil {
		return "", 0, err
	}
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", 0, err
	}
	return hex.EncodeToString(h.Sum(nil)), st.ModTime().UnixNano(), nil
}

// Unchanged reports whether the DB sources match the provided fingerprint set.
func Unchanged(db *sql.DB, sources []SourceMeta, schemaHash, configHash string) (bool, error) {
	if err := EnsureMetaSchema(db); err != nil {
		return false, err
	}
	var sh, ch string
	_ = db.QueryRow(`SELECT value FROM build_meta WHERE key='schema_hash'`).Scan(&sh)
	_ = db.QueryRow(`SELECT value FROM build_meta WHERE key='config_hash'`).Scan(&ch)
	if sh != schemaHash || ch != configHash {
		return false, nil
	}
	rows, err := db.Query(`SELECT path, hash, mtime FROM source_files`)
	if err != nil {
		return false, err
	}
	defer rows.Close()
	prev := map[string]SourceMeta{}
	for rows.Next() {
		var m SourceMeta
		if err := rows.Scan(&m.Path, &m.Hash, &m.ModTime); err != nil {
			return false, err
		}
		prev[m.Path] = m
	}
	if len(prev) != len(sources) {
		return false, nil
	}
	for _, s := range sources {
		p, ok := prev[s.Path]
		if !ok || p.Hash != s.Hash {
			return false, nil
		}
	}
	// require nodes table exists and non-empty or allow empty graphs
	var n int
	err = db.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='nodes'`).Scan(&n)
	if err != nil || n == 0 {
		return false, nil
	}
	return true, nil
}

// WriteMeta replaces source fingerprints after a successful build.
func WriteMeta(db *sql.DB, sources []SourceMeta, schemaHash, configHash string) error {
	if err := EnsureMetaSchema(db); err != nil {
		return err
	}
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()
	if _, err := tx.Exec(`DELETE FROM source_files`); err != nil {
		return err
	}
	if _, err := tx.Exec(`DELETE FROM build_meta`); err != nil {
		return err
	}
	stmt, err := tx.Prepare(`INSERT INTO source_files(path, hash, mtime) VALUES (?,?,?)`)
	if err != nil {
		return err
	}
	defer stmt.Close()
	for _, s := range sources {
		if _, err := stmt.Exec(s.Path, s.Hash, s.ModTime); err != nil {
			return err
		}
	}
	now := time.Now().UTC().Format(time.RFC3339)
	for k, v := range map[string]string{
		"schema_hash": schemaHash,
		"config_hash": configHash,
		"built_at":    now,
	} {
		if _, err := tx.Exec(`INSERT INTO build_meta(key, value) VALUES (?,?)`, k, v); err != nil {
			return err
		}
	}
	return tx.Commit()
}

// CollectSources hashes existing paths.
func CollectSources(paths []string) ([]SourceMeta, error) {
	var out []SourceMeta
	seen := map[string]bool{}
	for _, p := range paths {
		if p == "" || seen[p] {
			continue
		}
		seen[p] = true
		abs, err := filepath.Abs(p)
		if err != nil {
			return nil, err
		}
		if _, err := os.Stat(abs); err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return nil, err
		}
		h, mt, err := FileHash(abs)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", abs, err)
		}
		out = append(out, SourceMeta{Path: abs, Hash: h, ModTime: mt})
	}
	return out, nil
}
