package sample

import "testing"

func TestProxyENSObserverReplayHarness_CombinedArtifactFixtureRoutesBlameToStreamShape(t *testing.T) {
	if CountTransactionEvents() != 1 {
		t.Fatalf("assertion=transaction-event count")
	}
	if CompletedTransactions() != 1 {
		t.Fatalf("assertion=completedTransactions count")
	}
	if ObservedSymbolCount() != 1 {
		t.Fatalf("assertion=observed-symbol count")
	}
}
