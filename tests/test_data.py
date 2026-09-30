"""tests/test_data.py - Unit test stub for data module.

Owner: M2 (Models & Data Lead)
"""



def test_data_module_import():
    """Verify data package, dataset, transforms, and partitioners import cleanly."""
    import data
    from data.brats_dataset import BraTSDataset
    from data.partitioner import partition_data
    from data.transforms import get_train_transforms, get_val_transforms

    assert data is not None
    assert BraTSDataset is not None
    assert get_train_transforms is not None
    assert get_val_transforms is not None
    assert partition_data is not None


def test_partitioner_iid_and_dirichlet():
    """Verify IID and Dirichlet partitioning across 3 hospital nodes."""
    from data.partitioner import partition_data

    total_samples = 30
    
    # 1. Test IID Partition
    iid_splits = partition_data(total_samples, num_nodes=3, partition_type="iid", seed=42)
    assert len(iid_splits) == 3
    assert sum(len(indices) for indices in iid_splits.values()) == total_samples
    assert len(iid_splits[1]) == 10
    assert len(iid_splits[2]) == 10
    assert len(iid_splits[3]) == 10

    # 2. Test Dirichlet Non-IID Partition
    dir_splits = partition_data(total_samples, num_nodes=3, partition_type="dirichlet", alpha=0.5, seed=42)
    assert len(dir_splits) == 3
    assert sum(len(indices) for indices in dir_splits.values()) == total_samples
    # Each node should have at least 1 sample
    for node_id in [1, 2, 3]:
        assert len(dir_splits[node_id]) > 0


def test_synthetic_dataset_generation():
    """Verify synthetic BraTS dataset generates 4-channel image and 3-channel mask."""
    from data.brats_dataset import BraTSDataset

    ds = BraTSDataset(is_synthetic=True, num_synthetic_samples=3)
    assert len(ds) == 3
    sample = ds[0]
    assert "image" in sample
    assert "mask" in sample
    assert "patient_id" in sample
    assert sample["image"].shape == (4, 64, 64, 64)
    assert sample["mask"].shape == (3, 64, 64, 64)
