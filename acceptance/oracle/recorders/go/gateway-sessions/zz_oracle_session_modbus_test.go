package main

import (
	"context"
	cryptorand "crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	ebusgateway "github.com/Project-Helianthus/helianthus-ebusgateway"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/modbusadapter"
	sunspectest "github.com/Project-Helianthus/helianthus-ebusgateway/internal/modbusadapter/testfixture"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semanticview"
	"github.com/Project-Helianthus/helianthus-ebusgateway/internal/semhub"
	"github.com/Project-Helianthus/helianthus-ebusgateway/m2mgraphql"
	"github.com/Project-Helianthus/helianthus-ebusgateway/mcp"
	"github.com/Project-Helianthus/helianthus-ebusgateway/portal"
	modbus "github.com/Project-Helianthus/helianthus-modbus"
	"github.com/Project-Helianthus/helianthus-modbusreg/huawei"
	"github.com/Project-Helianthus/helianthus-modbusreg/sunspec"
	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
)

// oracleModbusClock is the deterministic wall clock of one Modbus session; every reading is a value the session input fixed.
type oracleModbusClock struct {
	mu  sync.Mutex
	now time.Time
}

func (c *oracleModbusClock) Now() time.Time   { c.mu.Lock(); defer c.mu.Unlock(); return c.now }
func (c *oracleModbusClock) Set(at time.Time) { c.mu.Lock(); c.now = at; c.mu.Unlock() }
func (c *oracleModbusClock) Advance(d time.Duration) {
	c.mu.Lock()
	c.now = c.now.Add(d)
	c.mu.Unlock()
}

func oracleModbusOrigin(t *testing.T, text string) time.Time {
	t.Helper()
	origin, err := time.Parse(time.RFC3339, text)
	if err != nil {
		t.Fatal(err)
	}
	return origin.UTC()
}

func oracleWordsFromHex(t *testing.T, text string) []uint16 {
	t.Helper()
	raw, err := hex.DecodeString(text)
	if err != nil || len(raw)%2 != 0 {
		t.Fatalf("register words are not an even hex string: %v", err)
	}
	words := make([]uint16, len(raw)/2)
	for index := range words {
		words[index] = uint16(raw[2*index])<<8 | uint16(raw[2*index+1])
	}
	return words
}

func oracleWordsHex(words []uint16) string {
	raw := make([]byte, 2*len(words))
	for index, word := range words {
		raw[2*index], raw[2*index+1] = byte(word>>8), byte(word)
	}
	return hex.EncodeToString(raw)
}

// oracleModbusWordPatch replaces consecutive register words of the served chain between two polls.
type oracleModbusWordPatch struct {
	Index    int    `json:"index"`
	WordsHex string `json:"words_hex"`
}

func (patch oracleModbusWordPatch) apply(t *testing.T, words []uint16) {
	t.Helper()
	replacement := oracleWordsFromHex(t, patch.WordsHex)
	if patch.Index < 0 || patch.Index+len(replacement) > len(words) {
		t.Fatalf("patch at %d is outside the served chain", patch.Index)
	}
	copy(words[patch.Index:], replacement)
}

// ---------------------------------------------------------------- SunSpec

type oracleSunSpecPoll struct {
	Name          string                  `json:"name"`
	ClockOffsetMS int64                   `json:"clock_offset_ms"`
	PatchWords    []oracleModbusWordPatch `json:"patch_words"`
}

type oracleSunSpecRead struct {
	ClockOffsetMS    int64 `json:"clock_offset_ms"`
	SingleAtOffsetMS int64 `json:"single_at_offset_ms"`
}

type oracleSunSpecIncarnation struct {
	Name                string              `json:"name"`
	Epoch               string              `json:"epoch"`
	Generation          uint64              `json:"generation"`
	StartClockOffsetMS  int64               `json:"start_clock_offset_ms"`
	StartupAdvanceMS    int64               `json:"startup_advance_ms"`
	Polls               []oracleSunSpecPoll `json:"polls"`
	PublicRead          *oracleSunSpecRead  `json:"public_read"`
	RetiresBeforeNextAt string              `json:"retires"`
}

type oracleSunSpecInput struct {
	UnitID        byte                       `json:"unit_id"`
	RegisterBase  int                        `json:"register_base"`
	EndpointPort  int                        `json:"endpoint_port"`
	ClockOrigin   string                     `json:"clock_origin"`
	ChainWordsHex string                     `json:"chain_words_hex"`
	Incarnations  []oracleSunSpecIncarnation `json:"incarnations"`
}

// oracleServeSunSpecChain serves the words of the frozen SunSpec chain fixture with the request recorder of
// sunspectest.ServeSunSpecChain, unchanged, on the endpoint the session names. The frozen helper binds an ephemeral
// port, and the endpoint string enters the PV source identity, so the recorded identities would differ on every run.
func oracleServeSunSpecChain(endpoint string, words []uint16) (net.Listener, func() []sunspectest.ReadRequest, error) {
	listener, err := net.Listen("tcp4", endpoint)
	if err != nil {
		return nil, nil, err
	}
	var mu sync.Mutex
	var requests []sunspectest.ReadRequest
	go func() {
		connection, err := listener.Accept()
		if err != nil {
			return
		}
		defer func() { _ = connection.Close() }()
		for {
			header := make([]byte, 7)
			if _, err := io.ReadFull(connection, header); err != nil {
				return
			}
			length := int(binary.BigEndian.Uint16(header[4:6]))
			body := make([]byte, length-1)
			if _, err := io.ReadFull(connection, body); err != nil || len(body) != 5 {
				return
			}
			request := sunspectest.ReadRequest{
				UnitID: header[6], Function: modbus.FunctionCode(body[0]),
				Offset: binary.BigEndian.Uint16(body[1:3]), WordCount: binary.BigEndian.Uint16(body[3:5]),
			}
			mu.Lock()
			requests = append(requests, request)
			mu.Unlock()
			start := int(request.Offset) - 40000
			end := start + int(request.WordCount)
			if start < 0 || end > len(words) {
				return
			}
			response := make([]byte, 9+2*int(request.WordCount))
			copy(response[:2], header[:2])
			binary.BigEndian.PutUint16(response[4:6], uint16(3+2*int(request.WordCount)))
			response[6], response[7], response[8] = request.UnitID, byte(request.Function), byte(2*request.WordCount)
			for index, word := range words[start:end] {
				binary.BigEndian.PutUint16(response[9+2*index:], word)
			}
			if _, err := connection.Write(response); err != nil {
				return
			}
		}
	}()
	return listener, func() []sunspectest.ReadRequest {
		mu.Lock()
		defer mu.Unlock()
		return append([]sunspectest.ReadRequest(nil), requests...)
	}, nil
}

// oracleSunSpecDriver reports what the production worker's Poll returned for each cycle.
type oracleSunSpecDriver struct {
	inner  *modbusSunSpecLiveSmokeDriver
	onPoll func(sunSpecLiveSmokeAttempt, sunSpecLiveSmokePollResult, error)
}

func (d *oracleSunSpecDriver) Poll(ctx context.Context, attempt sunSpecLiveSmokeAttempt) (sunSpecLiveSmokePollResult, error) {
	result, err := d.inner.Poll(ctx, attempt)
	d.onPoll(attempt, result, err)
	return result, err
}
func (d *oracleSunSpecDriver) Reconnect(ctx context.Context) error { return d.inner.Reconnect(ctx) }

// oracleAdvancingEndpoint advances the injected clock when the native endpoint opens, as the pinned characterization does.
type oracleAdvancingEndpoint struct {
	modbusadapter.Endpoint
	advance func()
}

func (e oracleAdvancingEndpoint) OpenConnection(connection net.Conn) (modbus.TCPConnectionHandle, error) {
	e.advance()
	return e.Endpoint.OpenConnection(connection)
}

// oracleViewJSON records a PV current view; the canonical bytes are a function of the snapshot, so only their digest is kept.
func oracleViewJSON(view modbusadapter.SemanticPVCurrent) any {
	sum := sha256.Sum256(view.Canonical)
	return map[string]any{"snapshot": oracleJSON(view.Snapshot), "canonical_sha256": hex.EncodeToString(sum[:]), "evaluation": oracleJSON(view.Evaluation),
		"selections": oracleJSON(view.Selections), "projection": oracleJSON(view.Projection)}
}

// oracleViewDigest records an adapter getter read of a view the publication record already holds: the digests of the
// snapshot and the evaluation context, and the selections.
func oracleViewDigest(view modbusadapter.SemanticPVCurrent) any {
	sum := sha256.Sum256(view.Canonical)
	return map[string]any{"canonical_sha256": hex.EncodeToString(sum[:]), "asset_id": string(view.Snapshot.AssetID), "evaluation_context": oracleJSON(view.Evaluation.Context),
		"evaluation_digest": oracleJSON(view.Evaluation.EvaluationDigest), "selections": oracleJSON(view.Selections), "fact_count": len(view.Snapshot.Facts)}
}

func oracleSunSpecLeafKeys(view modbusadapter.SemanticPVCurrent) []string {
	var keys []string
	for _, envelope := range view.Snapshot.Facts {
		for _, candidate := range envelope.Candidates {
			keys = append(keys, string(envelope.Key.FactID)+" "+string(candidate.CandidateID))
		}
	}
	sort.Strings(keys)
	return keys
}

func oracleSunSpecSession(t *testing.T, scenario string, input oracleSunSpecInput) *oracleClasses {
	classes := oracleNormalize()
	origin := oracleModbusOrigin(t, input.ClockOrigin)
	baseWords := oracleWordsFromHex(t, input.ChainWordsHex)
	clock := &oracleModbusClock{now: origin}
	hub := newTestSemanticHub(t)
	var previous *modbusadapter.PublicationScope
	var lastView modbusadapter.SemanticPVCurrent
	var lastAdapter *modbusadapter.Adapter
	var retire func(step string)

	for _, incarnation := range input.Incarnations {
		incarnation := incarnation
		words := append([]uint16(nil), baseWords...)
		endpoint := net.JoinHostPort(net.IPv4(127, 0, 0, 1).String(), strconv.Itoa(input.EndpointPort))
		listener, requests, err := oracleServeSunSpecChain(endpoint, words)
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(func() { _ = listener.Close() })
		scope := &modbusadapter.PublicationScope{Epoch: semreg.SourceEpochID(incarnation.Epoch), Generation: incarnation.Generation, Previous: previous}
		config, err := mapModbusInstanceRuntimeConfig(ebusgateway.ModbusTCPConfig{Enabled: true, Endpoint: "tcp://" + endpoint, DialTimeout: time.Second}, nil)
		if err != nil {
			t.Fatal(err)
		}
		config.Clock = clock.Now
		if config.SemanticPV, err = modbusadapter.NewSemanticPVClass(hub, semanticFamilyGraph(semanticFamilyPV)); err != nil {
			t.Fatal(err)
		}
		config.Publication = scope
		advance := func() { clock.Advance(time.Duration(incarnation.StartupAdvanceMS) * time.Millisecond) }
		clock.Set(origin.Add(time.Duration(incarnation.StartClockOffsetMS) * time.Millisecond))
		dial := func(ctx context.Context, network, address string) (net.Conn, error) {
			advance()
			return (&net.Dialer{}).DialContext(ctx, network, address)
		}
		factory := func(endpoint modbus.TCPEndpointConfig) (modbusadapter.Endpoint, error) {
			advance()
			native, err := modbus.NewTCPEndpoint(endpoint)
			if err != nil {
				return nil, err
			}
			return oracleAdvancingEndpoint{Endpoint: native, advance: advance}, nil
		}
		adapter, err := modbusadapter.Start(context.Background(), config, dial, factory)
		if err != nil {
			t.Fatal(err)
		}
		lastAdapter = adapter
		classes.Outcomes = append(classes.Outcomes, map[string]any{"step": incarnation.Name + "/start", "epoch": incarnation.Epoch, "generation": incarnation.Generation, "started": true})
		producer, err := modbusadapter.NewSunSpecProducer(adapter, modbusadapter.SunSpecProducerConfig{UnitID: input.UnitID, AuthorizationScope: sunSpecLiveSmokeAuthorizationScope, ReadTimeout: sunSpecLiveSmokeReadTimeout})
		if err != nil {
			t.Fatal(err)
		}

		var step string
		var decisions []string
		polled := make(chan struct{})
		release := make(chan struct{})
		driver := &oracleSunSpecDriver{inner: &modbusSunSpecLiveSmokeDriver{adapter: adapter, producer: producer}}
		sent := 0
		var lastSample string
		driver.onPoll = func(attempt sunSpecLiveSmokeAttempt, result sunSpecLiveSmokePollResult, pollErr error) {
			all := requests()
			for _, request := range all[sent:] {
				first := int(request.Offset) - input.RegisterBase
				served := words[first : first+int(request.WordCount)]
				classes.Sends = append(classes.Sends, map[string]any{"step": step, "unit": request.UnitID, "function": uint8(request.Function), "offset": request.Offset, "quantity": request.WordCount})
				classes.Acquisitions = append(classes.Acquisitions, map[string]any{"step": step, "poll_generation": attempt.PollID, "deadline_identity": attempt.DeadlineID, "offset": request.Offset, "quantity": request.WordCount, "words_hex": oracleWordsHex(served)})
			}
			sent = len(all)
			if result.Qualification.SampleID != "" {
				lastSample = result.Qualification.SampleID
			}
			qualification := map[string]any{"outcome": string(result.Qualification.Outcome), "capability_id": result.Qualification.CapabilityID, "capability_reason": fmt.Sprint(result.Qualification.CapabilityReason),
				"flavor_id": result.Qualification.FlavorID, "flavor_reason": fmt.Sprint(result.Qualification.FlavorReason), "flavor_evaluations": oracleJSON(result.Qualification.FlavorEvaluations),
				"observation_count": result.Qualification.ObservationCount, "sample_id": result.Qualification.SampleID, "semantic_withhold": result.Qualification.SemanticWithhold}
			outcome := map[string]any{"step": step, "qualification": qualification, "reconnect_required": result.Snapshot.ReconnectRequired}
			if pollErr != nil {
				outcome["error"] = pollErr.Error()
			}
			classes.Outcomes = append(classes.Outcomes, outcome)
		}
		wait := func(ctx context.Context, _ time.Duration) error {
			select {
			case polled <- struct{}{}:
			case <-ctx.Done():
				return ctx.Err()
			}
			select {
			case <-release:
				return nil
			case <-ctx.Done():
				return ctx.Err()
			}
		}
		workerCtx, cancel := context.WithCancel(context.Background())
		logf := func(format string, args ...any) { decisions = append(decisions, fmt.Sprintf(format, args...)) }
		worker := newSunSpecLiveSmokeWorkerCore(workerCtx, sunSpecLiveSmokeAttemptTimeout, sunSpecLiveSmokeCycleInterval, false, driver, modbusSunSpecLiveSmokeQualifier{}, logf, wait)

		for index, poll := range incarnation.Polls {
			step = incarnation.Name + "/" + poll.Name
			clock.Set(origin.Add(time.Duration(poll.ClockOffsetMS) * time.Millisecond))
			for _, patch := range poll.PatchWords {
				patch.apply(t, words)
			}
			if index == 0 {
				worker.Start()
			} else {
				release <- struct{}{}
			}
			<-polled
			view, ok := adapter.SemanticPVCurrentSingle()
			classes.Publications = append(classes.Publications, map[string]any{"step": step, "available": ok, "view": oracleViewJSON(view)})
			if ok {
				lastView = view
			}
		}
		classes.Outcomes = append(classes.Outcomes, map[string]any{"step": incarnation.Name + "/worker-decisions", "decision_lines": decisions})

		if incarnation.PublicRead != nil {
			read := incarnation.PublicRead
			step = incarnation.Name + "/public-read"
			clock.Set(origin.Add(time.Duration(read.ClockOffsetMS) * time.Millisecond))
			classes.PublicOutputs = append(classes.PublicOutputs, oracleSunSpecPublicReads(t, adapter, lastView, step, origin.Add(time.Duration(read.SingleAtOffsetMS)*time.Millisecond), lastSample)...)
		}

		retire = func(stepName string) {
			cancel()
			_ = worker.Close()
			before := oracleSunSpecLeafKeys(lastView)
			scope.Withdraw()
			fenceErr := adapter.WithdrawSemantic()
			view, available := adapter.SemanticPVCurrentSingle()
			after := oracleSunSpecLeafKeys(view)
			afterSet := map[string]bool{}
			for _, key := range after {
				afterSet[key] = true
			}
			var gone []string
			for _, key := range before {
				if !afterSet[key] {
					gone = append(gone, key)
				}
			}
			withdrawal := map[string]any{"step": stepName, "scope_withdrawn": !adapter.PublicationActive(), "readable_after": available, "hub_readable_after": hub.Readable(lastView.Snapshot.AssetID), "withdrawn_facts": gone}
			if fenceErr != nil {
				withdrawal["error"] = fenceErr.Error()
			}
			classes.Withdrawals = append(classes.Withdrawals, withdrawal)
			closeErr := adapter.CloseNative()
			_ = listener.Close()
			outcome := map[string]any{"step": stepName, "native_closed": closeErr == nil}
			if closeErr != nil {
				outcome["error"] = closeErr.Error()
			}
			classes.Outcomes = append(classes.Outcomes, outcome)
		}
		previous = scope
		if incarnation.RetiresBeforeNextAt == "" {
			// The last incarnation is fenced at the end of the session.
			defer func(name string, run func(string)) { run(name + "/fence") }(incarnation.Name, retire)
		} else {
			retire(incarnation.Name + "/fence")
		}
	}
	_ = lastAdapter
	return classes
}

// oracleSunSpecPublicReads replays the registered public reads of the gateway: the adapter getters, the MCP provider and the
// Portal route that forwards to the machine GraphQL surface.
func oracleSunSpecPublicReads(t *testing.T, adapter *modbusadapter.Adapter, view modbusadapter.SemanticPVCurrent, step string, singleAt time.Time, sample string) []any {
	var reads []any
	asset := string(view.Snapshot.AssetID)
	if byAsset, ok := adapter.SemanticPVCurrentByAsset(asset); ok {
		reads = append(reads, map[string]any{"step": step, "read": "adapter.SemanticPVCurrentByAsset", "view": oracleViewDigest(byAsset)})
	}
	if single, ok := adapter.SemanticPVCurrentSingleAt(singleAt); ok {
		reads = append(reads, map[string]any{"step": step, "read": "adapter.SemanticPVCurrentSingleAt", "view": oracleViewDigest(single)})
	}
	provider := newGatewayModbusMCPProvider(adapter).(*gatewayModbusMCPProvider)
	if result, err := provider.SemanticPVCurrent(context.Background(), sunspec.ThreePhaseMonitoringCapabilityID, sample); err == nil {
		reads = append(reads, map[string]any{"step": step, "read": "mcp.provider.SemanticPVCurrent", "result": oracleJSON(result)})
	} else {
		reads = append(reads, map[string]any{"step": step, "read": "mcp.provider.SemanticPVCurrent", "error": err.Error()})
	}
	reads = append(reads, oraclePortalPVRead(t, adapter, asset, step))
	return reads
}

// oraclePortalPVRead reads the composed Portal route over the machine GraphQL runtime, as the pinned PUBLIC05 test does.
func oraclePortalPVRead(t *testing.T, adapter *modbusadapter.Adapter, asset, step string) map[string]any {
	certs := newM2MTLSCertificates(t)
	runtime, err := newM2MGraphQLRuntime(ebusgateway.Config{M2MGraphQL: ebusgateway.M2MGraphQLConfig{
		ListenAddr: net.JoinHostPort(net.IPv4(127, 0, 0, 1).String(), "0"), ServerName: "m2m.gateway.test",
		ServerCertFile: certs.serverCertFile, ServerKeyFile: certs.serverKeyFile,
		AllowedAssets: []string{asset},
	}}, adapter)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = runtime.Close() })
	dir := t.TempDir()
	clientCert := writeM2MPEM(t, dir, "portal-client.pem", "CERTIFICATE", certs.goodClient.Certificate[0])
	clientKey := writeM2MPEM(t, dir, "portal-client-key.pem", "RSA PRIVATE KEY", x509.MarshalPKCS1PrivateKey(certs.goodClient.PrivateKey.(*rsa.PrivateKey)))
	forward, err := newPortalPVClient(ebusgateway.PortalPVConfig{
		SemanticEnabled: true,
		M2MURL:          "https://localhost" + runtime.Addr()[strings.LastIndex(runtime.Addr(), ":"):] + "/graphql/m2m/v1",
		M2MServerName:   "m2m.gateway.test",
		M2MCAFile:       certs.caFile,
		M2MClientCert:   clientCert,
		M2MClientKey:    clientKey,
		AssetRef:        asset,
	})
	if err != nil {
		t.Fatal(err)
	}
	handler := portal.NewHandler(portal.Options{SemanticPVEnabled: true, SemanticPV: forward})
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/semantic/pv/current", nil))
	var body any
	if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
		body = response.Body.String()
	}
	// The forwarded view is the same tuple the MCP read above records in full; the Portal envelope keeps its digest.
	if envelope, ok := body.(map[string]any); ok {
		if data, ok := envelope["data"].(map[string]any); ok {
			if view, ok := data["semantic_pv_current"]; ok {
				encoded, _ := json.Marshal(view)
				sum := sha256.Sum256(encoded)
				data["semantic_pv_current"] = map[string]any{"sha256_of_forwarded_view": hex.EncodeToString(sum[:]), "bytes": len(encoded)}
			}
		}
	}
	return map[string]any{"step": step, "read": "portal GET /api/v1/semantic/pv/current", "status": response.Code, "body": body}
}

// ---------------------------------------------------------------- Gen3 retained owner

type oracleGen3Step struct {
	Kind        string                       `json:"kind"`
	Name        string                       `json:"name"`
	ClockWall   string                       `json:"clock_wall"`
	ReadClockNS int64                        `json:"read_clock_ns"`
	Persistent  *TeslaGen3PersistentOutcome  `json:"persistent"`
	Provisional *TeslaGen3ProvisionalOutcome `json:"provisional"`
	Fence       *struct {
		Current uint64 `json:"current"`
		Next    uint64 `json:"next"`
	} `json:"fence"`
	Successor *ebusgateway.TeslaGen3HSCRetainedConfig `json:"successor"`
	MCPTool   string                                  `json:"mcp_tool"`
	CurrentAt string                                  `json:"current_at"`
}

type oracleGen3Input struct {
	Config      ebusgateway.TeslaGen3HSCRetainedConfig `json:"config"`
	Steps       []oracleGen3Step                       `json:"steps"`
	RawArm      json.RawMessage                        `json:"raw_active_transport_arm"`
	PublicQuery string                                 `json:"graphql_query"`
}

func oracleGen3Wall(t *testing.T, text string) time.Time {
	t.Helper()
	wall, err := time.Parse(time.RFC3339Nano, text)
	if err != nil {
		t.Fatal(err)
	}
	return wall.UTC()
}

// oracleGen3GraphQL reads the registered machine GraphQL surface of an owner and keeps the response status.
func oracleGen3GraphQL(t *testing.T, owner *teslaHSCRetainedOwner, query string) map[string]any {
	handler, err := m2mgraphql.NewHandler(m2mgraphql.Config{
		AllowedAssets: map[string]struct{}{owner.cfg.AssetID: {}},
		SemanticEVSECurrent: func(ctx context.Context, asset string) (json.RawMessage, bool) {
			value, currentErr := currentTeslaEVSEPublic(ctx, asset, owner)
			return value, currentErr == nil
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	request := `{"operationName":"SemanticEVSECurrent","query":` + strconv.Quote(query) + `,"variables":{"request":{"contract_id":"PUBLIC_GRAPHQL_SEMANTIC_EVSE_V1","asset_ref":` + strconv.Quote(owner.cfg.AssetID) + `}}}`
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/graphql/m2m/v1", strings.NewReader(request)).WithContext(m2mgraphql.WithMTLSPrincipal(context.Background(), "retained-owner-session")))
	var body any
	if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
		body = response.Body.String()
	}
	return map[string]any{"read": "m2m graphql semantic_evse_current", "status": response.Code, "body": body}
}

func oracleGen3Session(t *testing.T, input oracleGen3Input) *oracleClasses {
	classes := oracleNormalize()
	hub := newTestSemanticHub(t)
	owner, err := startTeslaHSCRetainedOwner(input.Config, hub)
	if err != nil {
		t.Fatal(err)
	}
	clock := &characterizationClock{}
	injectTeslaCharacterizationClock(t, owner, clock)
	armSum := sha256.Sum256(input.RawArm)
	classes.Outcomes = append(classes.Outcomes, map[string]any{"step": "owner-start", "generation": input.Config.DriverGeneration, "epoch": input.Config.SourceEpoch, "opens_active_endpoint": false,
		"raw_active_transport_arm_sha256": hex.EncodeToString(armSum[:])})
	ctx := context.Background()
	for _, step := range input.Steps {
		if step.ClockWall != "" {
			clock.set(oracleGen3Wall(t, step.ClockWall), time.Duration(step.ReadClockNS))
		}
		record := map[string]any{"step": step.Name, "kind": step.Kind}
		switch step.Kind {
		case "set-clock":
			record["clock_wall"] = step.ClockWall
			record["read_clock_ns"] = step.ReadClockNS
			classes.Outcomes = append(classes.Outcomes, record)
		case "ingest-persistent", "ingest-provisional":
			var ingestErr error
			if step.Kind == "ingest-persistent" {
				ingestErr = owner.IngestPersistent(ctx, *step.Persistent)
			} else {
				ingestErr = owner.IngestProvisional(ctx, *step.Provisional)
			}
			if ingestErr != nil {
				record["error"] = ingestErr.Error()
			}
			record["evidence"] = oracleJSON(owner.RetainedEvidence())
			if source, err := owner.TeslaGen3EVSECurrentLimitV1(ctx); err == nil {
				native := map[string]any{}
				if source.Persistent != nil {
					native["persistent_max_output_current_amps"] = source.Persistent.MaxOutputCurrentAmps()
				}
				if source.Provisional != nil {
					native["provisional_limit_current_max_amps"] = source.Provisional.LimitCurrentMaxAmps()
					native["provisional_limit_timeout_seconds"] = source.Provisional.LimitTimeoutSeconds()
				}
				record["native"] = native
			} else {
				record["native_error"] = err.Error()
			}
			classes.Outcomes = append(classes.Outcomes, record)
		case "read":
			value, readErr := owner.TeslaGen3EVSESemanticCurrent(ctx)
			if readErr != nil {
				record["error"] = readErr.Error()
				classes.Outcomes = append(classes.Outcomes, record)
				break
			}
			public := characterizationJSON(t, value)
			canonical, snapshot := characterizationCanonical(t, public)
			sum := sha256.Sum256(canonical)
			record["canonical_sha256"] = hex.EncodeToString(sum[:])
			record["view"] = oracleJSON(value)
			record["identity"] = string(characterizationIdentity(t, snapshot))
			if step.CurrentAt != "" {
				at, ok := owner.SemanticEVSECurrentAt(oracleGen3Wall(t, step.CurrentAt))
				record["current_at"] = map[string]any{"available": ok, "view": oracleJSON(at)}
			}
			classes.Publications = append(classes.Publications, record)
		case "mcp-call":
			server, err := mcp.NewServer(emptyMCPRegistry{}, nil)
			if err != nil {
				t.Fatal(err)
			}
			mcp.RegisterModbusV1Tools(server, newGatewayModbusMCPProviderWithRuntimes(nil, nil, owner))
			status, body := oracleMCPCall(server.Handler(), step.MCPTool)
			classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": step.Name, "read": "mcp tools/call " + step.MCPTool, "status": status, "body": body})
		case "public-reads":
			server, err := mcp.NewServer(emptyMCPRegistry{}, nil)
			if err != nil {
				t.Fatal(err)
			}
			mcp.RegisterModbusV1Tools(server, newGatewayModbusMCPProviderWithRuntimes(nil, nil, owner))
			status, body := oracleMCPCall(server.Handler(), mcp.SemanticV1EVSECurrentGetTool)
			classes.PublicOutputs = append(classes.PublicOutputs,
				map[string]any{"step": step.Name, "read": "mcp tools/call " + mcp.SemanticV1EVSECurrentGetTool, "status": status, "generation": owner.cfg.DriverGeneration, "epoch": owner.cfg.SourceEpoch, "body": body},
				func() map[string]any {
					out := oracleGen3GraphQL(t, owner, input.PublicQuery)
					out["step"], out["generation"], out["epoch"] = step.Name, owner.cfg.DriverGeneration, owner.cfg.SourceEpoch
					return out
				}())
		case "fence":
			before, _ := hub.Inspect(semreg.AssetID(owner.cfg.AssetID))
			fenceErr := owner.Fence(step.Fence.Current, step.Fence.Next)
			after, _ := hub.Inspect(semreg.AssetID(owner.cfg.AssetID))
			withdrawal := map[string]any{"step": step.Name, "current": step.Fence.Current, "next": step.Fence.Next, "bindings_before": oracleBindingStates(before.Snapshot), "bindings_after": oracleBindingStates(after.Snapshot)}
			if fenceErr != nil {
				withdrawal["error"] = fenceErr.Error()
			}
			if _, readErr := owner.TeslaGen3EVSESemanticCurrent(ctx); readErr != nil {
				withdrawal["read_after_fence_error"] = readErr.Error()
			}
			if _, ok := owner.SemanticEVSECurrentAt(clock.now()); !ok {
				withdrawal["current_at_after_fence"] = "unavailable"
			}
			classes.Withdrawals = append(classes.Withdrawals, withdrawal)
		case "successor":
			successor, err := owner.Successor(*step.Successor)
			if err != nil {
				record["error"] = err.Error()
				classes.Outcomes = append(classes.Outcomes, record)
				t.Fatal(err)
			}
			injectTeslaCharacterizationClock(t, successor, clock)
			owner = successor
			record["epoch"], record["generation"] = successor.cfg.SourceEpoch, successor.cfg.DriverGeneration
			classes.Outcomes = append(classes.Outcomes, record)
		case "inspect":
			view, _ := hub.Inspect(semreg.AssetID(owner.cfg.AssetID))
			record["bindings"] = oracleBindingStates(view.Snapshot)
			record["identity"] = string(characterizationIdentity(t, view.Snapshot))
			record["services"] = oracleAvailability(view.Snapshot)
			classes.Publications = append(classes.Publications, record)
		default:
			t.Fatalf("unknown step kind %q", step.Kind)
		}
	}
	return classes
}

// oracleMCPCall performs one JSON-RPC tool call on the registered MCP handler and keeps the HTTP status and the exact body.
func oracleMCPCall(handler http.Handler, tool string) (int, any) {
	body := `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"` + tool + `","arguments":{}}}`
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(body)))
	var decoded any
	if err := json.Unmarshal(response.Body.Bytes(), &decoded); err != nil {
		decoded = response.Body.String()
	}
	return response.Code, decoded
}

func oracleBindingStates(snapshot semreg.Snapshot) []any {
	var out []any
	for _, binding := range snapshot.Bindings {
		out = append(out, map[string]any{"binding": string(binding.BindingID), "epoch": string(binding.SourceEpochID), "generation": string(binding.DriverGeneration), "state": string(binding.State)})
	}
	return out
}

func oracleAvailability(snapshot semreg.Snapshot) map[string]any {
	services, capabilities := []any{}, []any{}
	for _, service := range snapshot.Services {
		services = append(services, map[string]any{"binding": string(service.BindingID), "availability": string(service.Availability)})
	}
	for _, capability := range snapshot.Capabilities {
		capabilities = append(capabilities, map[string]any{"binding": string(capability.BindingID), "availability": string(capability.Availability)})
	}
	return map[string]any{"services": services, "capabilities": capabilities}
}

// ---------------------------------------------------------------- Huawei TCP providers

type oracleHuaweiStep struct {
	Kind string `json:"kind"`
	Name string `json:"name"`
}

type oracleHuaweiInput struct {
	Family          string             `json:"family"`
	ReplayFixture   string             `json:"replay_fixture"`
	ClockStart      string             `json:"clock_start"`
	Label           string             `json:"label"`
	Source          string             `json:"source"`
	VictimUnit      byte               `json:"victim_unit"`
	MappingUnit     byte               `json:"mapping_unit"`
	Steps           []oracleHuaweiStep `json:"steps"`
	Withholds       []string           `json:"withheld_fact_ids"`
	PublicationName string             `json:"publication_driver"`
	EntropySeed     string             `json:"hub_incarnation_entropy_seed"`
}

// oracleHuaweiNative is h10Native with the start of the provider clock taken from the session rather than the host clock.
func oracleHuaweiNative(t *testing.T, fixture h10Replay, start time.Time) (huaweiRegistryProvider, *h10Conn, *h10Clock) {
	t.Helper()
	clock := &h10Clock{now: start.Add(time.Second)}
	conn := &h10Conn{clock: clock}
	for _, cycle := range fixture.Cycles {
		conn.steps = append(conn.steps, cycle.Steps...)
	}
	config, err := mapModbusRuntimeConfig(ebusgateway.ModbusTCPConfig{Enabled: true, Endpoint: h10Loopback(t, conn), DialTimeout: time.Second})
	if err != nil {
		t.Fatal(err)
	}
	config.Clock = clock.Now
	config.SemanticPV, err = modbusadapter.NewSemanticPVClass(newTestSemanticHub(t), false)
	if err != nil {
		t.Fatal(err)
	}
	config.Endpoint.Framing = modbus.TCPFramingTolerant
	config.Endpoint.MaxBufferedBytes = 7 + modbus.MaxTolerantPDUSize
	adapter, err := modbusadapter.Start(context.Background(), config, func(ctx context.Context, network, address string) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, network, address)
	}, func(config modbus.TCPEndpointConfig) (modbusadapter.Endpoint, error) {
		return modbus.NewTCPEndpoint(config)
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = adapter.Close() })
	session, err := modbusadapter.NewReadOnlySession(adapter)
	if err != nil {
		t.Fatal(err)
	}
	family := modbusTCPFamilyHuaweiSmartLogger
	if fixture.Family == "S-Dongle" {
		family = modbusTCPFamilyHuaweiSDongle
	}
	provider, err := newHuaweiRegistryProvider(family, huawei.ProviderConfig{Source: "alpha", AllowedUnits: fixture.AllowedUnits, Clock: clock.Now, Wait: clock.Wait})
	if err != nil {
		t.Fatal(err)
	}
	if err := provider.Start(session); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = provider.Close() })
	return provider, conn, clock
}

// oracleEntropy is the fixed byte stream that stands in for the operating system's entropy while the hub is constructed.
type oracleEntropy struct {
	seed    string
	counter uint64
}

func (e *oracleEntropy) Read(p []byte) (int, error) {
	filled := 0
	for filled < len(p) {
		block := sha256.Sum256([]byte(fmt.Sprintf("%s\x00%d", e.seed, e.counter)))
		e.counter++
		filled += copy(p[filled:], block[:])
	}
	return len(p), nil
}

// oracleDeterministicHub constructs the production semantic hub with its random incarnation identity drawn from the
// session's fixed seed; the stock reader is restored before anything else runs.
func oracleDeterministicHub(t *testing.T, seed string) *semhub.Hub {
	t.Helper()
	if seed == "" {
		t.Fatal("the session names no hub incarnation seed")
	}
	stock := cryptorand.Reader
	cryptorand.Reader = &oracleEntropy{seed: seed}
	defer func() { cryptorand.Reader = stock }()
	return newTestSemanticHub(t)
}

// oracleHuaweiAsset summarizes one published PV asset: its canonical digest, the quantity of every fact by subject role, the link and binding states.
func oracleHuaweiAsset(t *testing.T, hub *semhub.Hub, unit byte, asset semreg.AssetID) map[string]any {
	view, err := hub.Inspect(asset)
	if err != nil {
		t.Fatal(err)
	}
	canonical, err := semreg.CanonicalJSON(view.Snapshot)
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(canonical)
	resources := map[semreg.ResourceID]semreg.Resource{}
	for _, resource := range view.Snapshot.Resources {
		resources[resource.ResourceID] = resource
	}
	var facts []any
	for _, envelope := range view.Snapshot.Facts {
		for _, candidate := range envelope.Candidates {
			role := ""
			if len(envelope.Key.Dimensions) > 0 && envelope.Key.Dimensions[0].Value.Text != nil {
				if subject, ok := resources[semreg.ResourceID(*envelope.Key.Dimensions[0].Value.Text)]; ok {
					role = string(subject.Kind)
					if subject.Anchor.Slot != nil {
						role += ":" + *subject.Anchor.Slot
					}
				}
			}
			entry := map[string]any{"fact": string(envelope.Key.FactID), "subject": role, "freshness": string(candidate.Quality.Freshness), "received_at": oracleJSON(candidate.Times.ReceivedAt)}
			if candidate.Value != nil && candidate.Value.Quantity != nil {
				entry["quantity"] = oracleJSON(candidate.Value.Quantity)
			}
			facts = append(facts, entry)
		}
	}
	var links, bindings []any
	for _, link := range view.Snapshot.IdentityLinks {
		links = append(links, map[string]any{"binding": string(link.BindingID), "state": string(link.State)})
	}
	for _, binding := range view.Snapshot.Bindings {
		bindings = append(bindings, map[string]any{"binding": string(binding.BindingID), "epoch": string(binding.SourceEpochID), "generation": string(binding.DriverGeneration), "state": string(binding.State)})
	}
	return map[string]any{"unit": unit, "asset": string(asset), "canonical_sha256": hex.EncodeToString(sum[:]), "fact_count": len(facts), "facts": facts, "identity_links": links, "bindings": bindings, "retained_observations": len(view.Snapshot.Retained)}
}

func oracleHuaweiPublished(published map[byte]semreg.AssetID) []int {
	var units []int
	for unit := range published {
		units = append(units, int(unit))
	}
	sort.Ints(units)
	return units
}

func oracleHuaweiSession(t *testing.T, input oracleHuaweiInput) *oracleClasses {
	classes := oracleNormalize()
	fixture := h10Load(t, input.Family)
	start := oracleModbusOrigin(t, input.ClockStart)
	provider, conn, clock := oracleHuaweiNative(t, fixture, start)
	var allSteps []h10Step
	for _, cycle := range fixture.Cycles {
		allSteps = append(allSteps, cycle.Steps...)
	}
	hub := oracleDeterministicHub(t, input.EntropySeed)
	publication, err := newHuaweiPVPublication(hub, input.PublicationName, input.Source, input.Label, nil, func() bool { return true })
	if err != nil {
		t.Fatal(err)
	}
	recorded := 0
	var cycle, original huawei.ProviderCycle
	for _, step := range input.Steps {
		switch step.Kind {
		case "refresh":
			cycle = h10Refresh(t, provider, clock)
			original = cycle
			conn.mu.Lock()
			wire := append([][]byte(nil), conn.recorded...)
			conn.mu.Unlock()
			for index := recorded; index < len(wire); index++ {
				classes.Sends = append(classes.Sends, map[string]any{"step": step.Name, "index": index, "unit": allSteps[index].Unit, "pdu_hex": hex.EncodeToString(wire[index])})
				classes.Acquisitions = append(classes.Acquisitions, map[string]any{"step": step.Name, "index": index, "unit": allSteps[index].Unit, "response_pdu_hex": hex.EncodeToString(allSteps[index].Response), "answered": len(allSteps[index].Response) != 0})
			}
			recorded = len(wire)
			children := []any{}
			for _, child := range cycle.Children {
				children = append(children, oracleJSON(child))
			}
			classes.Outcomes = append(classes.Outcomes, map[string]any{"step": step.Name, "cycle": oracleJSON(cycle)})
		case "publish":
			before := oracleHuaweiPublished(publication.published)
			err := publication.Publish(cycle)
			record := map[string]any{"step": step.Name, "cycle": cycle.Cycle, "cycle_outcome": string(cycle.Outcome)}
			if err != nil {
				record["error"] = err.Error()
			}
			after := oracleHuaweiPublished(publication.published)
			var assets []any
			for _, unit := range after {
				assets = append(assets, oracleHuaweiAsset(t, hub, byte(unit), publication.published[byte(unit)]))
			}
			record["published_units"], record["assets"] = after, assets
			classes.Publications = append(classes.Publications, record)
			gone := []any{}
			for _, unit := range before {
				if _, kept := publication.published[byte(unit)]; !kept {
					view := oracleHuaweiAsset(t, hub, byte(unit), huaweiAssetID(input.Label, "pv", byte(unit)))
					gone = append(gone, map[string]any{"unit": unit, "identity_links": view["identity_links"], "bindings": view["bindings"], "fact_count": view["fact_count"], "retained_observations": view["retained_observations"]})
				}
			}
			if len(gone) > 0 {
				classes.Withdrawals = append(classes.Withdrawals, map[string]any{"step": step.Name, "withdrawn_assets": gone})
			}
		case "lose-child":
			cycle = original
			cycle.Cycle++
			cycle.CompletedAt = cycle.CompletedAt.Add(time.Second)
			cycle.Children = append([]huawei.ProviderChildObservation(nil), cycle.Children...)
			for index := range cycle.Children {
				if cycle.Children[index].UnitID == input.VictimUnit {
					cycle.Children[index].Evidence = huawei.ProviderEvidenceWithheld
					cycle.Children[index].Reason = huawei.ProviderReasonIdentityMismatch
				}
			}
			classes.Outcomes = append(classes.Outcomes, map[string]any{"step": step.Name, "victim_unit": input.VictimUnit, "children": oracleJSON(cycle.Children)})
		case "incomplete-listing":
			cycle.Cycle++
			cycle.CompletedAt = cycle.CompletedAt.Add(time.Second)
			cycle.Outcome = huawei.ProviderCycleIncomplete
			cycle.Children = nil
			classes.Outcomes = append(classes.Outcomes, map[string]any{"step": step.Name, "cycle_outcome": string(cycle.Outcome), "children": 0})
		case "restore":
			restored := original
			restored.Cycle = cycle.Cycle + 1
			restored.CompletedAt = cycle.CompletedAt.Add(time.Second)
			cycle = restored
			classes.Outcomes = append(classes.Outcomes, map[string]any{"step": step.Name, "cycle": restored.Cycle})
		case "mapping":
			asset := huaweiAssetID(input.Label, "pv", input.MappingUnit)
			view, err := hub.Inspect(asset)
			if err != nil {
				t.Fatal(err)
			}
			resources := map[semreg.ResourceID]semreg.Resource{}
			for _, resource := range view.Snapshot.Resources {
				resources[resource.ResourceID] = resource
			}
			quantities := map[string]map[string]any{}
			for _, envelope := range view.Snapshot.Facts {
				for _, candidate := range envelope.Candidates {
					if candidate.Value == nil || candidate.Value.Quantity == nil {
						continue
					}
					subject := resources[semreg.ResourceID(*envelope.Key.Dimensions[0].Value.Text)]
					role := string(subject.Kind)
					if subject.Anchor.Slot != nil && subject.Kind == "resource.dc_input" {
						role += ":" + *subject.Anchor.Slot
					}
					if quantities[string(envelope.Key.FactID)] == nil {
						quantities[string(envelope.Key.FactID)] = map[string]any{}
					}
					quantities[string(envelope.Key.FactID)][role] = oracleJSON(candidate.Value.Quantity.Number)
				}
			}
			absent := []string{}
			for _, id := range input.Withholds {
				if len(quantities[id]) == 0 {
					absent = append(absent, id)
				}
			}
			classes.Outcomes = append(classes.Outcomes, map[string]any{"step": step.Name, "asset": string(asset), "quantities": quantities, "withheld_or_absent_facts": absent})
		case "snapshot-reads":
			snapshotProvider := newGatewaySemanticSnapshotProvider(&gatewayRuntimeControl{hub: hub})
			snapshotProvider.now = clock.Now
			gql, mcpHandler := m11Handlers(t, snapshotProvider)
			for _, unit := range oracleHuaweiPublished(publication.published) {
				asset := string(publication.published[byte(unit)])
				selection := m11Selection(reflect.TypeOf(semanticview.View{}))
				query := fmt.Sprintf("{a:semantic_snapshot(asset_ids:[%q])%s b:semantic_snapshot(asset_ids:[%q])%s}", asset, selection, asset, selection)
				response := mcpRPC(t, mcpHandler, fmt.Sprintf(`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"semantic_v1_snapshot_get","arguments":{"asset_ids":[%q]}}}`, asset))
				if response.Error != nil {
					t.Fatal(response.Error)
				}
				var envelope map[string]any
				if err := json.Unmarshal([]byte(response.Result["content"].([]any)[0].(map[string]any)["text"].(string)), &envelope); err != nil {
					t.Fatal(err)
				}
				result := m11GraphQL(t, gql, query)
				m11AssertParity(t, result, envelope)
				classes.PublicOutputs = append(classes.PublicOutputs, map[string]any{"step": step.Name, "unit": unit, "asset": asset, "view": result["data"].(map[string]any)["a"], "surfaces": "the same view was read twice through GraphQL and once through the MCP tool, and the three agree"})
			}
		default:
			t.Fatalf("unknown step kind %q", step.Kind)
		}
	}
	conn.mu.Lock()
	remaining := len(conn.steps)
	conn.mu.Unlock()
	classes.Outcomes = append(classes.Outcomes, map[string]any{"step": "end", "unreplayed_fixture_steps": remaining})
	classes.Publications = oracleScrubHostTime(classes.Publications).([]any)
	classes.PublicOutputs = oracleScrubHostTime(classes.PublicOutputs).([]any)
	return classes
}

// oracleHostClockMarker stands in for a value that the pinned Huawei publication derives from the host wall clock: the source start
// instant it reads with time.Now when it is constructed, and the digests that cover that instant. They differ on every run and
// are not part of the recorded behaviour; every other field is recorded as the pin produced it.
const oracleHostClockMarker = "host-clock-dependent"

func oracleScrubHostTime(value any) any {
	switch typed := value.(type) {
	case map[string]any:
		for key, child := range typed {
			switch key {
			case "snapshot_id", "evaluation_digest", "last_batch_digest", "canonical_sha256":
				typed[key] = oracleHostClockMarker
			case "started_at":
				typed[key] = oracleHostClockMarker
			default:
				typed[key] = oracleScrubHostTime(child)
			}
		}
		return typed
	case []any:
		for index, child := range typed {
			typed[index] = oracleScrubHostTime(child)
		}
		return typed
	}
	return value
}

func oracleSessionModbusRun(t *testing.T, session oracleSession) *oracleClasses {
	switch session.Scenario {
	case "sunspec-first-incarnation", "sunspec-generation-replacement":
		var input oracleSunSpecInput
		if err := json.Unmarshal(session.Input, &input); err != nil {
			t.Fatal(err)
		}
		return oracleSunSpecSession(t, session.Scenario, input)
	case "gen3-managed-first-incarnation", "gen3-managed-generation-replacement":
		var input oracleGen3Input
		if err := json.Unmarshal(session.Input, &input); err != nil {
			t.Fatal(err)
		}
		return oracleGen3Session(t, input)
	case "dongle-tcp", "logger-tcp":
		var input oracleHuaweiInput
		if err := json.Unmarshal(session.Input, &input); err != nil {
			t.Fatal(err)
		}
		return oracleHuaweiSession(t, input)
	}
	t.Fatalf("unknown scenario %q", session.Scenario)
	return nil
}

// TestOracleSessionModbus runs one Modbus session of the published input and records the six classes.
func TestOracleSessionModbus(t *testing.T) {
	session := oracleLoadSession(t)
	classes := oracleSessionModbusRun(t, session)
	oracleWriteClasses(t, classes)
}
