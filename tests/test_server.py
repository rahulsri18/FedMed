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
