package api

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/Project-Helianthus/helianthus-ship-go/cert"
	"github.com/Project-Helianthus/helianthus-ship-go/mdns"
	spinemodel "github.com/Project-Helianthus/helianthus-spine-go/model"
)

// TestOracleAPIConfiguration records api/configuration.go. The stimulus is the
// pin's own Test_Configuration; api/api.go, features.go, featuresclient.go,
// featuresserver.go, usecases.go, errors.go and types.go declare interfaces,
// error values and one string type, and the tests of the package at the pin
// supply no input to any of them.
func TestOracleAPIConfiguration(t *testing.T) {
	certificate, err := cert.CreateCertificate("unit", "org", "DE", "CN")
	if err != nil {
		t.Fatal(err)
	}
	vendor, brand, model, serial := "vendor", "brand", "model", "serial"
	port := 4567
	heartbeat := time.Second * 4
	entityTypes := []spinemodel.EntityTypeType{spinemodel.EntityTypeTypeCEM}
	deviceType := spinemodel.DeviceTypeTypeEnergyManagementSystem

	construction := []any{}
	attempts := []struct {
		name                         string
		vendor, brand, model, serial string
		deviceType                   spinemodel.DeviceTypeType
		entityTypes                  []spinemodel.EntityTypeType
		port                         int
	}{
		{"empty vendor and zero port", "", brand, model, serial, deviceType, entityTypes, 0},
		{"empty vendor", "", brand, model, serial, deviceType, entityTypes, port},
		{"empty brand", vendor, "", model, serial, deviceType, entityTypes, port},
		{"empty model", vendor, brand, "", serial, deviceType, entityTypes, port},
		{"empty serial", vendor, brand, model, "", deviceType, entityTypes, port},
		{"empty device type", vendor, brand, model, serial, "", entityTypes, port},
		{"empty entity types", vendor, brand, model, serial, deviceType, []spinemodel.EntityTypeType{}, port},
		{"all required fields", vendor, brand, model, serial, deviceType, entityTypes, port},
	}
	var config *Configuration
	for _, attempt := range attempts {
		built, err := NewConfiguration(attempt.vendor, attempt.brand, attempt.model, attempt.serial, attempt.deviceType,
			attempt.entityTypes, attempt.port, certificate, heartbeat)
		record := map[string]any{
			"case": attempt.name, "configuration_returned": built != nil, "error": nil,
			"input": map[string]any{
				"vendor_code": attempt.vendor, "brand": attempt.brand, "model": attempt.model, "serial": attempt.serial,
				"device_type": string(attempt.deviceType), "entity_type_count": len(attempt.entityTypes), "port": attempt.port,
			},
		}
		if err != nil {
			record["error"] = map[string]any{"text": err.Error()}
		}
		construction = append(construction, record)
		if built != nil {
			config = built
		}
	}
	if config == nil {
		t.Fatal("no valid configuration")
	}

	accessors := []any{}
	note := func(call string, value any) { accessors = append(accessors, map[string]any{"call": call, "result": value}) }
	note("MdnsProviderSelection/default", fmt.Sprint(config.MdnsProviderSelection()))
	config.SetMdnsProviderSelection(mdns.MdnsProviderSelectionAvahiOnly)
	note("MdnsProviderSelection/after-SetMdnsProviderSelection(AvahiOnly)", fmt.Sprint(config.MdnsProviderSelection()))
	note("Interfaces/default-is-nil", config.Interfaces() == nil)
	config.SetInterfaces([]string{"lo", "eth0"})
	note("Interfaces/after-SetInterfaces(lo,eth0)", config.Interfaces())
	note("generateIdentifier", config.generateIdentifier())
	note("Identifier/default", config.Identifier())
	note("MdnsServiceName/default", config.MdnsServiceName())
	config.SetAlternateIdentifier("alternate")
	note("Identifier/after-SetAlternateIdentifier(alternate)", config.Identifier())
	note("MdnsServiceName/after-SetAlternateIdentifier-only", config.MdnsServiceName())
	config.SetAlternateMdnsServiceName("alternate")
	note("MdnsServiceName/after-SetAlternateMdnsServiceName(alternate)", config.MdnsServiceName())
	note("Port", config.Port())
	note("HeartbeatTimeout_ns", int64(config.HeartbeatTimeout()))
	note("VendorCode", config.VendorCode())
	note("DeviceBrand", config.DeviceBrand())
	note("DeviceModel", config.DeviceModel())
	note("DeviceSerialNumber", config.DeviceSerialNumber())
	note("DeviceType", string(config.DeviceType()))
	entities := []any{}
	for _, entity := range config.EntityTypes() {
		entities = append(entities, string(entity))
	}
	note("EntityTypes", entities)
	note("FeatureSet", fmt.Sprint(config.FeatureSet()))
	note("Certificate/chain-length-before-SetCertificate", len(config.Certificate().Certificate))
	config.SetCertificate(tls.Certificate{})
	note("Certificate/chain-length-after-SetCertificate(empty)", len(config.Certificate().Certificate))

	directory := os.Getenv("ORACLE_OUT")
	if directory == "" {
		t.Fatal("ORACLE_OUT is not set")
	}
	document := map[string]any{
		"format":    "helianthus-oracle-qv06-case/1",
		"component": "api/configuration.go (NewConfiguration and the Configuration accessors and setters)",
		"source":    "api/configuration.go",
		"stimulus":  "api/configuration_test.go ConfigurationSuite.Test_Configuration",
		"input": map[string]any{
			"bytes": "",
			"qualifiers": map[string]any{
				"certificate": "generated per run by the pin's certificate helper; only the length of its chain is an output",
				"heartbeat_timeout_ns": int64(heartbeat), "port": port,
			},
			"clock": map[string]any{}, "state": map[string]any{},
		},
		"output": map[string]any{
			"symbols_written": []any{}, "decisions": construction, "cache": map[string]any{}, "observations": accessors, "counters": map[string]any{},
		},
	}
	data, err := json.MarshalIndent(document, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, "configuration-go", "new-configuration-and-accessors.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(data, '\n'), 0o644); err != nil {
		t.Fatal(err)
	}
}
