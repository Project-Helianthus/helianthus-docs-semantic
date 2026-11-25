package eebusruntime

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func oracleLens(result LensResult) map[string]any {
	operations := []any{}
	for _, operation := range result.Operations {
		operations = append(operations, map[string]any{"name": operation.Name, "unit": operation.Unit, "own_capability": operation.OwnCapability, "converted": operation.Converted})
	}
	return map[string]any{
		"family": result.Family, "resource_id": result.ResourceID, "parent_resource_id": result.ParentResourceID, "lens_admitted": result.LensAdmitted,
		"runtime_enabled": result.RuntimeEnabled, "input_dimension": result.InputDimension, "contains_cited": result.ContainsCited, "basis": result.Basis,
		"elements": result.Elements, "operations": operations, "use_case": result.UseCase, "actor": result.Actor, "use_case_text": result.UseCaseText,
		"device_actor": result.DeviceActor, "missing_elements": result.MissingElements, "overlapping": result.Overlapping,
	}
}

func oracleApplied(binding *OutputBinding, result LensResult) map[string]any {
	loss := binding.Apply(result)
	if loss == nil {
		loss = []string{}
	}
	return map[string]any{
		"lens_result": oracleLens(result), "loss": loss, "entity_address": binding.EntityAddress(result.ResourceID), "parent_address": binding.ParentAddress(result.ResourceID),
		"server_features": nonNil(binding.ServerFeatures(result.ResourceID)), "monitoring_loss": nonNil(binding.MonitoringLoss(result.ResourceID)),
		"entity_types": nonNil(binding.EntityTypes()),
	}
}

func nonNil(values []string) []string {
	if values == nil {
		return []string{}
	}
	return values
}

func oracleNodeAdded(node *outputBindingFakeNode) []any {
	out := []any{}
	for _, entity := range node.added {
		out = append(out, map[string]any{"kind": entity.kind, "address": entity.address, "parent": entity.parent})
	}
	return out
}

func oracleRecordBindingConstruction(t *testing.T) {
	steps := []any{}
	{
		binding := newOutputBinding(t)
		node := outputBindingNode(t, binding)
		oracleStep(&steps, "NewOutputBinding/before-any-lens-result", map[string]any{
			"AdvertisementCount": binding.AdvertisementCount(), "ServiceCount": binding.ServiceCount(), "DeviceType": binding.DeviceType(),
			"node_AdvertisementCount": node.AdvertisementCount(), "node_ServiceCount": node.ServiceCount(), "node_DeviceType": node.DeviceType(),
			"EntityTypes": binding.EntityTypes(), "EntityAddresses": binding.EntityAddresses(), "node_entities_added": oracleNodeAdded(node),
		})
		applied := oracleApplied(binding, outputBindingInverter("north"))
		applied["node_entities_added"] = oracleNodeAdded(node)
		applied["counts_after"] = map[string]any{"advertisements": binding.AdvertisementCount(), "services": binding.ServiceCount(), "device_type": binding.DeviceType()}
		oracleStep(&steps, "Apply/inverter", applied)
	}
	{
		node := newOutputBindingFakeNode()
		node.advertisements = 4
		node.services = 2
		node.deviceType = "ProbeNode"
		binding, err := openOutputBindingOnFakeNode(t, t.TempDir(), node)
		if err != nil {
			t.Fatal(err)
		}
		before := map[string]any{"AdvertisementCount": binding.AdvertisementCount(), "ServiceCount": binding.ServiceCount(), "DeviceType": binding.DeviceType()}
		inverter := outputBindingInverter("north")
		inverter.Elements = []string{"temperature"}
		applied := oracleApplied(binding, inverter)
		applied["counts_before"] = before
		applied["node_entities_added"] = oracleNodeAdded(node)
		applied["node_features"] = node.features[binding.EntityAddress("north")]
		oracleStep(&steps, "counts-and-device-type-come-from-the-node", applied)
	}
	{
		_, noNodeErr := NewOutputBinding(t.TempDir())
		useOutputBindingNode(t, func() (shipNode, error) { return nil, errors.New("absent") })
		_, absentErr := NewOutputBinding(t.TempDir())
		oracleStep(&steps, "NewOutputBinding/requires-existing-node", map[string]any{
			"without_runtime_node_is_errExistingNode": errors.Is(noNodeErr, errExistingNode), "without_runtime_node_error": oracleErr(noNodeErr),
			"absent_node_is_errExistingNode": errors.Is(absentErr, errExistingNode), "absent_node_error": oracleErr(absentErr),
		})
	}
	{
		var binding *OutputBinding
		oracleStep(&steps, "nil-receiver", map[string]any{
			"Apply_loss": binding.Apply(outputBindingInverter("north")), "EntityAddress": binding.EntityAddress("north"), "ParentAddress": binding.ParentAddress("north"),
			"EntityAddresses": binding.EntityAddresses(), "MonitoringLoss_is_nil": binding.MonitoringLoss("north") == nil,
		})
	}
	oracleWrite(t, "output-binding-go", "construction-counts-and-nil-receiver", oracleCase{
		Component: "output_binding.go (NewOutputBinding, AdvertisementCount, ServiceCount, DeviceType, EntityTypes, EntityAddresses, nil receiver)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBinding, TestOutputBindingObservesNodeCounts, TestOutputBindingRequiresExistingNode, TestOutputBindingNilReceiver",
		Input:     oracleInput{Qualifiers: map[string]any{"node": "the pin's scripted node (one advertisement, one service, device type EnergyManagementSystem), and a node reporting 4, 2 and ProbeNode"}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingResourceFields(t *testing.T) {
	binding := newOutputBinding(t)
	steps := []any{}
	oracleStep(&steps, "Apply/inverter-north", oracleApplied(binding, outputBindingInverter("north")))
	base := LensResult{Family: "pv string", ResourceID: "east", ParentResourceID: "north", LensAdmitted: true, RuntimeEnabled: true, ContainsCited: true}
	baseline := oracleApplied(binding, base)
	node := outputBindingNode(t, binding)
	baseline["node_parent_of_east"] = node.parentOf(binding.EntityAddress("east"))
	baseline["node_address_of_north"] = binding.EntityAddress("north")
	oracleStep(&steps, "Apply/pv-string-baseline", baseline)
	mutations := []struct {
		name   string
		mutate func(*LensResult)
	}{
		{"family", func(result *LensResult) { result.Family = "heating"; result.ResourceID = "heat" }},
		{"lens admitted", func(result *LensResult) { result.LensAdmitted = false; result.ResourceID = "west" }},
		{"runtime enabled", func(result *LensResult) { result.RuntimeEnabled = false; result.ResourceID = "south" }},
		{"input dimension", func(result *LensResult) { result.InputDimension = true; result.ResourceID = "flat" }},
		{"parent", func(result *LensResult) { result.ParentResourceID = ""; result.ResourceID = "orphan" }},
		{"contains cited", func(result *LensResult) { result.ContainsCited = false; result.ResourceID = "loose" }},
	}
	for _, item := range mutations {
		mutated := base
		item.mutate(&mutated)
		record := oracleApplied(binding, mutated)
		record["mutated_field"] = item.name
		oracleStep(&steps, "Apply/pv-string-mutated", record)
	}
	oracleStep(&steps, "Apply/battery", oracleApplied(binding, LensResult{Family: "battery", ResourceID: "pack", LensAdmitted: true, RuntimeEnabled: true}))
	oracleStep(&steps, "Apply/charger", oracleApplied(binding, LensResult{Family: "charger", ResourceID: "bay", LensAdmitted: true, RuntimeEnabled: true}))
	oracleStep(&steps, "node-after-all", map[string]any{"node_entities_added": oracleNodeAdded(node)})
	oracleWrite(t, "output-binding-go", "resource-fields-admit-or-withhold", oracleCase{
		Component: "output_binding.go (OutputBinding.Apply, admitted, publishedFamily, stringParentAdmitted, ensureEntity)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingResourceFields",
		Input:     oracleInput{Qualifiers: map[string]any{"base_pv_string": oracleLens(base), "mutations": []any{"family", "lens admitted", "runtime enabled", "input dimension", "parent", "contains cited"}}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingBasisAndMerge(t *testing.T) {
	binding := newOutputBinding(t)
	steps := []any{}
	for _, basis := range []string{"index", "name", "address"} {
		result := outputBindingInverter("north")
		result.Basis = basis
		result.ResourceID = basis
		oracleStep(&steps, "Apply/basis", oracleApplied(binding, result))
	}
	oracleStep(&steps, "Apply/empty-basis", oracleApplied(binding, outputBindingInverter("north")))
	charger := LensResult{Family: "charger", ResourceID: "north", LensAdmitted: true, RuntimeEnabled: true}
	oracleStep(&steps, "Apply/second-family-same-resource", oracleApplied(binding, charger))
	oracleWrite(t, "output-binding-go", "basis-and-merged-resources", oracleCase{
		Component: "output_binding.go (OutputBinding.Apply, ensureEntity, applyLoss)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingBasisAndMerge",
		Input:     oracleInput{Qualifiers: map[string]any{"bases": []any{"index", "name", "address", ""}}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingProhibition(t *testing.T) {
	binding := newOutputBinding(t)
	steps := []any{}
	refused := outputBindingInverter("north")
	refused.Actor = "Inverter"
	refused.UseCaseText = "The actor Inverter forbids device type EnergyManagementSystem"
	oracleStep(&steps, "Apply/matching-prohibition", oracleApplied(binding, refused))
	permitted := refused
	permitted.ResourceID = "south"
	permitted.UseCaseText = "The actor Inverter describes device type EnergyManagementSystem"
	oracleStep(&steps, "Apply/text-without-prohibition", oracleApplied(binding, permitted))
	otherActor := refused
	otherActor.ResourceID = "bay"
	otherActor.Family = "charger"
	otherActor.Actor = "EVSE"
	oracleStep(&steps, "Apply/text-naming-another-actor", oracleApplied(binding, otherActor))
	otherType := refused
	otherType.ResourceID = "roof"
	otherType.UseCaseText = "The actor Inverter forbids device type GridGuard"
	oracleStep(&steps, "Apply/text-forbidding-another-type", oracleApplied(binding, otherType))
	exempt := outputBindingInverter("exempt")
	exempt.Actor = "Inverter"
	exempt.UseCaseText = "The actor Inverter forbids every device type except EnergyManagementSystem"
	oracleStep(&steps, "Apply/exception-for-this-type", oracleApplied(binding, exempt))
	kept := outputBindingInverter("kept")
	kept.Actor = "Inverter"
	kept.UseCaseText = "The actor Inverter forbids device type EnergyManagementSystem except GridGuard"
	oracleStep(&steps, "Apply/prohibition-with-unrelated-exception", oracleApplied(binding, kept))
	silent := outputBindingInverter("silent")
	silent.LensAdmitted = false
	silent.Actor = "Inverter"
	silent.UseCaseText = "The actor Inverter forbids device type EnergyManagementSystem"
	oracleStep(&steps, "Apply/not-admitted-prohibition", oracleApplied(binding, silent))
	oracleWrite(t, "output-binding-go", "device-type-prohibition", oracleCase{
		Component: "output_binding.go (prohibitedDeviceType, textForbidsDeviceType, sentenceForbidsDeviceType, indexWord)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingDeviceTypeProhibition",
		Input:     oracleInput{Qualifiers: map[string]any{"device_type_of_node": "EnergyManagementSystem"}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingAddresses(t *testing.T) {
	steps := []any{}
	directory := t.TempDir()
	stored := func() any {
		data, err := os.ReadFile(filepath.Join(directory, addressFileName))
		if err != nil {
			return map[string]any{"read_error_is_not_exist": os.IsNotExist(err)}
		}
		return map[string]any{"text": string(data)}
	}
	first := newOutputBindingAt(t, directory)
	oracleStep(&steps, "Apply/north", oracleApplied(first, outputBindingInverter("north")))
	oracleStep(&steps, "Apply/south", oracleApplied(first, outputBindingInverter("south")))
	oracleStep(&steps, "stored-address-file", map[string]any{"file": stored(), "EntityAddresses": first.EntityAddresses()})
	replacement := first.noteAddress("north", "other")
	oracleStep(&steps, "noteAddress/replacement-of-a-stored-address", map[string]any{
		"error": oracleErr(replacement), "is_errStoredAddressReplacement": errors.Is(replacement, errStoredAddressReplacement), "address_after": first.EntityAddress("north"),
	})
	second := newOutputBindingAt(t, directory)
	oracleStep(&steps, "restart/Apply/north", oracleApplied(second, outputBindingInverter("north")))
	oracleStep(&steps, "restart/EntityAddress-before-Apply-of-south", map[string]any{"south": second.EntityAddress("south")})
	oracleStep(&steps, "restart/Apply/east", oracleApplied(second, outputBindingInverter("east")))
	oracleStep(&steps, "stored-address-file-after-restart", map[string]any{"file": stored()})
	if err := os.WriteFile(filepath.Join(directory, addressFileName), []byte("east a\neast b\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	_, conflictErr := openOutputBindingOnFakeNode(t, directory, newOutputBindingFakeNode())
	oracleStep(&steps, "NewOutputBinding/conflicting-stored-addresses", map[string]any{"error": oracleErr(conflictErr), "is_errStoredAddressReplacement": errors.Is(conflictErr, errStoredAddressReplacement)})

	syncDirectory := t.TempDir()
	binding := newOutputBindingAt(t, syncDirectory)
	original := syncBindingFile
	syncBindingFile = func(file *os.File) error {
		if err := file.Sync(); err != nil {
			return err
		}
		return errors.New("sync failed")
	}
	syncErr := binding.noteAddress("north", "aa")
	syncBindingFile = original
	_, finalErr := os.Stat(filepath.Join(syncDirectory, addressFileName))
	_, temporaryErr := os.Stat(filepath.Join(syncDirectory, addressFileName+".new"))
	oracleStep(&steps, "noteAddress/failed-sync", map[string]any{
		"error": oracleErr(syncErr), "is_errAddressStore": errors.Is(syncErr, errAddressStore), "address_file_renamed": finalErr == nil, "temporary_file_left_behind": temporaryErr == nil,
		"address_retained_in_memory": binding.addresses["north"] != "",
	})
	oracleWrite(t, "output-binding-go", "address-identity-persistence-and-sync", oracleCase{
		Component: "output_binding.go (allocate, freshAddress, letterToken, noteAddress, persist, renderAddresses, loadAddresses)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingAddressIdentity, TestOutputBindingAddressSync",
		Input:     oracleInput{Qualifiers: map[string]any{"directory": "an empty sandbox directory per scenario", "resources": []any{"north", "south", "east"}, "conflicting_stored_file": "east a / east b", "stored_file_names": []any{addressFileName, addressFileName + ".new"}}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingFeatures(t *testing.T) {
	steps := []any{}
	{
		binding := newOutputBinding(t)
		inverter := outputBindingInverter("north")
		inverter.Elements = []string{"inverter ac measurement", "energy", "temperature", "operating state", "apparent power", "reactive power", "line-to-line voltage", "string dc"}
		inverter.Operations = []LensOperation{{Name: "pv.operation.set_active_power_limit", Unit: "W", OwnCapability: true}}
		record := oracleApplied(binding, inverter)
		record["node_features"] = outputBindingNode(t, binding).features[binding.EntityAddress("north")]
		oracleStep(&steps, "Apply/inverter-with-cited-elements-and-limit", record)
	}
	cases := []struct {
		name       string
		resourceID string
		operation  LensOperation
	}{
		{"system export", "exportop", LensOperation{Name: "system export", Unit: "W", OwnCapability: true}},
		{"amperes", "ampereunit", LensOperation{Name: "pv.operation.set_active_power_limit", Unit: "A", OwnCapability: true}},
		{"visibility", "visibleonly", LensOperation{Name: "pv.operation.set_active_power_limit", Unit: "W"}},
		{"converted", "convertedop", LensOperation{Name: "pv.operation.set_active_power_limit", Unit: "W", OwnCapability: true, Converted: true}},
	}
	for _, item := range cases {
		binding := newOutputBinding(t)
		result := outputBindingInverter("roof")
		result.ResourceID = item.resourceID
		result.Operations = []LensOperation{item.operation}
		record := oracleApplied(binding, result)
		record["operation_case"] = item.name
		oracleStep(&steps, "Apply/inverter-operation", record)
	}
	charger := newOutputBinding(t)
	admitted := LensResult{
		Family: "charger", ResourceID: "bay", LensAdmitted: true, RuntimeEnabled: true,
		Operations: []LensOperation{{Name: "evse.operation.set_allocated_current", Unit: "A", OwnCapability: true}},
	}
	oracleStep(&steps, "Apply/charger-allocated-current", oracleApplied(charger, admitted))
	watts := admitted
	watts.ResourceID = "otherbay"
	watts.Operations = []LensOperation{{Name: "active power", Unit: "W", OwnCapability: true}}
	oracleStep(&steps, "Apply/charger-active-power", oracleApplied(charger, watts))
	oracleWrite(t, "output-binding-go", "server-features-from-elements-and-operations", oracleCase{
		Component: "output_binding.go (bindFeatures, featuresForElement, featuresForOperation)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingServerFeatures",
		Input:     oracleInput{Qualifiers: map[string]any{"cases": []any{"inverter with cited elements and a production limit", "system export", "amperes", "visibility only", "converted", "charger allocated current", "charger active power"}}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingAnnouncement(t *testing.T) {
	binding := newOutputBinding(t)
	steps := []any{}
	overlap := outputBindingInverter("north")
	overlap.Overlapping = true
	overlap.UseCase = "Limitation of Power Production"
	overlap.Operations = []LensOperation{{Name: "pv.operation.set_active_power_limit", Unit: "W", OwnCapability: true}}
	oracleStep(&steps, "Apply/overlapping", oracleApplied(binding, overlap))
	ev := LensResult{Family: "ev", ResourceID: "car", LensAdmitted: true, RuntimeEnabled: true, DeviceActor: "EV", UseCase: "Overload protection"}
	oracleStep(&steps, "Apply/ev-device-actor", oracleApplied(binding, ev))
	partial := outputBindingInverter("south")
	partial.UseCase = "Monitoring of Inverter"
	partial.MissingElements = []string{"energy", "temperature"}
	partial.Elements = []string{"energy", "temperature", "operating state"}
	oracleStep(&steps, "Apply/missing-elements", oracleApplied(binding, partial))
	charger := LensResult{
		Family: "charger", ResourceID: "bay", LensAdmitted: true, RuntimeEnabled: true, UseCase: "Limitation of Power Consumption",
		Operations: []LensOperation{{Name: "evse.operation.set_allocated_current", Unit: "A", OwnCapability: true}},
	}
	oracleStep(&steps, "Apply/charger-consumption-limit-not-applied", oracleApplied(binding, charger))
	oracleWrite(t, "output-binding-go", "announcement-losses", oracleCase{
		Component: "output_binding.go (announcementLoss, consumptionApplied, MonitoringLoss, recordGaps)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingAnnouncement",
		Input:     oracleInput{Qualifiers: map[string]any{"cases": []any{"overlapping", "ev device actor", "missing elements", "charger consumption limit"}}},
		Output:    oracleOutput{Decisions: steps},
	})
}

func oracleRecordBindingNodeFollowing(t *testing.T) {
	steps := []any{}
	first := newOutputBindingFakeNode()
	var current shipNode = first
	useOutputBindingNode(t, func() (shipNode, error) {
		if current == nil {
			return nil, errors.New("released")
		}
		return current, nil
	})
	binding, err := NewOutputBinding(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	oracleStep(&steps, "Apply/north-on-first-node", oracleApplied(binding, outputBindingInverter("north")))
	address := binding.EntityAddress("north")
	oracleStep(&steps, "first-node", map[string]any{"entities_added": oracleNodeAdded(first)})
	current = nil
	record := oracleApplied(binding, outputBindingInverter("north"))
	record["AdvertisementCount"] = binding.AdvertisementCount()
	record["EntityAddresses"] = binding.EntityAddresses()
	oracleStep(&steps, "Apply/north-without-a-node", record)
	second := newOutputBindingFakeNode()
	current = second
	oracleStep(&steps, "EntityTypes/new-node-before-a-lens-result", map[string]any{"EntityTypes": binding.EntityTypes()})
	again := oracleApplied(binding, outputBindingInverter("north"))
	again["address_equals_first_address"] = again["entity_address"] == address
	oracleStep(&steps, "Apply/north-on-second-node", again)
	oracleStep(&steps, "nodes", map[string]any{"first_entities_added": oracleNodeAdded(first), "second_entities_added": oracleNodeAdded(second)})
	oracleWrite(t, "output-binding-go", "binding-follows-a-replaced-node", oracleCase{
		Component: "output_binding.go (liveNodeLocked)",
		Source:    "output_binding.go",
		Stimulus:  "output_binding_test.go TestOutputBindingFollowsReplacedNode",
		Input:     oracleInput{Qualifiers: map[string]any{"sequence": []any{"Apply on the first node", "the runtime releases its node", "Apply", "a second node runs", "Apply"}}},
		Output:    oracleOutput{Decisions: steps},
	})
}
