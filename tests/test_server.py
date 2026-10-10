"""tests/test_server.py - Unit test stub for server module.

Owner: M1 (Server & Orchestration Lead)
"""



def test_server_module_import():
    """Verify server module, strategy, and aggregators import cleanly."""
    import server
    from server.aggregator import aggregate_encrypted, aggregate_plaintext
    from server.strategy import FedMedFedAvg

    assert server is not None
    assert FedMedFedAvg is not None
    assert aggregate_plaintext is not None
    assert aggregate_encrypted is not None


def test_strategy_instantiation():
    """Verify FedMedFedAvg initializes with encrypted and plaintext configurations."""
    from server.strategy import FedMedFedAvg

    strat_enc = FedMedFedAvg(encrypted=True, min_fit_clients=3)
    assert strat_enc.encrypted is True

    strat_plain = FedMedFedAvg(encrypted=False, min_fit_clients=3)
    assert strat_plain.encrypted is False


def test_plaintext_aggregation():
    """Verify weighted averaging across client parameter lists."""
    import numpy as np

    from server.aggregator import aggregate_plaintext

    w1 = [np.array([1.0, 2.0, 3.0], dtype=np.float32)]
    w2 = [np.array([5.0, 6.0, 7.0], dtype=np.float32)]
    results = [(w1, 10), (w2, 30)]  # total = 40; w1 weight = 0.25, w2 weight = 0.75

    agg = aggregate_plaintext(results)
    expected = 0.25 * w1[0] + 0.75 * w2[0]
    np.testing.assert_allclose(agg[0], expected, rtol=1e-5)


def test_encrypted_homomorphic_aggregation():
    """Verify homomorphic addition of mock or TenSEAL ciphertexts."""
    from privacy.encryption import MockCKKSVector
    from server.aggregator import aggregate_encrypted

    c1 = [[MockCKKSVector([10.0, 20.0])]]
    c2 = [[MockCKKSVector([30.0, 40.0])]]
    results = [(c1, 5), (c2, 5)]  # equal weight 0.5 each

    agg = aggregate_encrypted(results)
    assert len(agg) == 1
    # Check that aggregated ciphertext contains 0.5*10 + 0.5*30 = 20, and 0.5*20 + 0.5*40 = 30
    assert hasattr(agg[0][0], "decrypt")
    decrypted = agg[0][0].decrypt()
    assert abs(decrypted[0] - 20.0) < 1e-4
    assert abs(decrypted[1] - 30.0) < 1e-4


def test_strategy_quorum_enforcement():
    """Verify strategy aborts when below quorum and succeeds when quorum is satisfied."""
    import numpy as np

    from server.strategy import FedMedFedAvg

    strat = FedMedFedAvg(min_fit_clients=3, min_quorum_clients=2, encrypted=False)

    class DummyClient:
        cid = "1"

    class DummyFitRes:
        def __init__(self):
            self.parameters = [np.zeros(5, dtype=np.float32)]
            self.num_examples = 10
            self.metrics = {"dice": 0.82, "loss": 0.25}

    # Only 1 client responsive (below quorum of 2) -> Quorum failure
    res_fail, metrics_fail = strat.aggregate_fit(1, [(DummyClient(), DummyFitRes())], [Exception("dropout")])
    assert res_fail is None
    assert metrics_fail.get("error") == "quorum_failure"

    # 2 clients responsive (quorum satisfied) -> Quorum survival
    client2 = DummyClient()
    client2.cid = "2"
    res_ok, metrics_ok = strat.aggregate_fit(1, [(DummyClient(), DummyFitRes()), (client2, DummyFitRes())], [Exception("Node 3 dropped")])
    assert res_ok is not None
    assert metrics_ok["node_count"] == 2
    assert metrics_ok["node_failures"] == 1

