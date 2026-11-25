package m2mgraphql

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	pv "github.com/Project-Helianthus/helianthus-ebusreg/pv"
)

type oracleM2MCase struct {
	Name     string `json:"name"`
	Fixture  string `json:"fixture"`
	Method   string `json:"method"`
	Route    string `json:"route"`
	Body     string `json:"body"`
	Status   int    `json:"status"`
	Response any    `json:"response"`
}

func oracleM2MRun(t *testing.T, handler http.Handler, name, fixture, method, route, body string) oracleM2MCase {
	t.Helper()
	var reader *bytes.Buffer
	if body != "" {
		reader = bytes.NewBufferString(body)
	}
	var request *http.Request
	if reader != nil {
		request = httptest.NewRequest(method, route, reader)
		request.Header.Set("Content-Type", "application/json")
	} else {
		request = httptest.NewRequest(method, route, nil)
	}
	request = request.WithContext(WithMTLSPrincipal(request.Context(), "fixture-principal"))
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	var decoded any
	if err := json.Unmarshal(response.Body.Bytes(), &decoded); err != nil {
		t.Fatalf("response is not JSON: %s", response.Body.String())
	}
	return oracleM2MCase{Name: name, Fixture: fixture, Method: method, Route: route, Body: body, Status: response.Code, Response: decoded}
}

// TestOraclePrePortCanonicalPVContract records the dedicated M2M canonical PV v1 contract of the pin: the fixture file and the answers of the handler on the pin's fixture snapshot.
func TestOraclePrePortCanonicalPVContract(t *testing.T) {
	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Skip("ORACLE_OUT is not set")
	}
	var contract contractFixtureShape
	if err := json.Unmarshal(contractFixture, &contract); err != nil {
		t.Fatal(err)
	}
	var fixture any
	if err := json.Unmarshal(contractFixture, &fixture); err != nil {
		t.Fatal(err)
	}
	digest := sha256.Sum256(contractFixture)

	served, err := NewHandler(Config{
		SnapshotByAssetAt: m2mSnapshotAt(func(context.Context, string) (pv.Snapshot, bool) { return m2mFixtureSnapshot(), true }),
		AssetExists:       func(string) bool { return true },
		AllowedAssets:     map[string]struct{}{"pv-asset-fixture": {}},
	})
	if err != nil {
		t.Fatal(err)
	}
	empty, err := NewHandler(Config{
		SnapshotByAssetAt: m2mSnapshotAt(func(context.Context, string) (pv.Snapshot, bool) { return pv.Snapshot{}, false }),
		AssetExists:       func(string) bool { return false },
		AllowedAssets:     map[string]struct{}{},
	})
	if err != nil {
		t.Fatal(err)
	}
	absent, err := NewHandler(Config{
		SnapshotByAssetAt: m2mSnapshotAt(func(context.Context, string) (pv.Snapshot, bool) { return pv.Snapshot{}, false }),
		AssetExists:       func(string) bool { return false },
		AllowedAssets:     map[string]struct{}{"pv-asset-fixture": {}},
	})
	if err != nil {
		t.Fatal(err)
	}

	canonical := m2mCanonicalRequest(canonicalM2MQuery, "pv-asset-fixture")
	cases := []oracleM2MCase{
		oracleM2MRun(t, served, "canonical-request/served", "the pin's fixture snapshot, asset allowed and present", http.MethodPost, contract.Route, canonical),
		oracleM2MRun(t, empty, "canonical-request/asset-not-allowed", "no allowed asset", http.MethodPost, contract.Route, canonical),
		oracleM2MRun(t, absent, "canonical-request/asset-without-snapshot", "asset allowed, no snapshot retained", http.MethodPost, contract.Route, canonical),
		oracleM2MRun(t, empty, "get-on-contract-route", "the pin's no-fallback case", http.MethodGet, "/graphql/m2m/v1", ""),
		oracleM2MRun(t, empty, "query-on-generic-route", "the pin's no-fallback case", http.MethodPost, "/graphql", `{"query":"{ m2mCurrentSnapshot { assetRef } }"}`),
		oracleM2MRun(t, empty, "subscription-on-contract-route", "the pin's no-fallback case", http.MethodPost, "/graphql/m2m/v1", `{"query":"subscription M2MCurrentSnapshot { m2mCurrentSnapshot { assetRef } }"}`),
	}
	document := map[string]any{
		"format":          "helianthus-oracle-pre-port-canonical-pv-m2m-contract/1",
		"description":     "the dedicated M2M contract of the pin and the answers of its handler",
		"contract_path":   "m2mgraphql/testdata/contract.json",
		"contract_sha256": hex.EncodeToString(digest[:]),
		"contract":        fixture,
		"cases":           cases,
	}
	encoded, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "m2m-canonical-pv-contract.json"), append(encoded, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
