import json
from multiprocessing import cpu_count
from src.ringxor import ringxor
import pathlib

# Load the test data
data_path: pathlib.Path = pathlib.Path.cwd() / ".." / "data" / "version_controlled" / "demo_rings.json"
with open(data_path, "r") as f:
    all_rings_raw = json.load(f)

# The code uses sets, but they can't be serialized to json, so we convert back here from temporary list representation
all_rings: ringxor.ring_bucket = {key_image: set(ring) for key_image, ring in all_rings_raw.items()}


def test_ringxor_process_bucket_single_thread_core():
    results = sorted(
        ringxor.process_bucket_single_thread_core(all_rings, index_pairs=None),
        key=lambda x: x["key_image_pointer"],
    )

    assert len(results) == 54
    assert results[0] == {
        "key_image_pointer": "056189f0c3ed7806bc17655152613b3288dfa496b6566b9bbef930efaa87975f",
        "output_pointer": "416e9438f9f69410cf42959dc8ee515318ea6710e5bf8eb76f69c6183a09bded",
        "match_key_image_pointer": "af6cb1936c08108500c3756e81073b6e48b33405be54df891e8b6e433b66b216",
    }
    assert results[53] == {
        "key_image_pointer": "fdfcbe3f85e480905d5db681bf89e5b81dc514871f0735c8a8cc7dffb6d7cde8",
        "output_pointer": "6d1fe6224bfccbb5f660d08bdb23fba89e75cf7d367b16bc40bcb3d337e12b0e",
        "match_key_image_pointer": "7d64ac02c2823257fb88ab2b34c2ecb6fbd60c59a23650d682d42c71105ac32a",
    }


def test_ringxor_process_bucket_1_worker():
    results = sorted(
        ringxor.process_bucket(all_rings, index_pairs=None, num_workers=1),
        key=lambda x: x["key_image_pointer"],
    )

    assert len(results) == 54
    assert results[0] == {
        "key_image_pointer": "056189f0c3ed7806bc17655152613b3288dfa496b6566b9bbef930efaa87975f",
        "output_pointer": "416e9438f9f69410cf42959dc8ee515318ea6710e5bf8eb76f69c6183a09bded",
        "match_key_image_pointer": "af6cb1936c08108500c3756e81073b6e48b33405be54df891e8b6e433b66b216",
    }
    assert results[53] == {
        "key_image_pointer": "fdfcbe3f85e480905d5db681bf89e5b81dc514871f0735c8a8cc7dffb6d7cde8",
        "output_pointer": "6d1fe6224bfccbb5f660d08bdb23fba89e75cf7d367b16bc40bcb3d337e12b0e",
        "match_key_image_pointer": "7d64ac02c2823257fb88ab2b34c2ecb6fbd60c59a23650d682d42c71105ac32a",
    }


def test_ringxor_process_bucket_N_worker():
    if cpu_count() == 1:
        print("Skipping test_ringxor_process_bucket_N_worker because only 1 CPU is available")
    else:
        results = sorted(
            ringxor.process_bucket(all_rings, index_pairs=None, num_workers=2),
            key=lambda x: x["key_image_pointer"],
        )

        assert len(results) == 54
        assert results[0] == {
            "key_image_pointer": "056189f0c3ed7806bc17655152613b3288dfa496b6566b9bbef930efaa87975f",
            "output_pointer": "416e9438f9f69410cf42959dc8ee515318ea6710e5bf8eb76f69c6183a09bded",
            "match_key_image_pointer": "af6cb1936c08108500c3756e81073b6e48b33405be54df891e8b6e433b66b216",
        }
        assert results[53] == {
            "key_image_pointer": "fdfcbe3f85e480905d5db681bf89e5b81dc514871f0735c8a8cc7dffb6d7cde8",
            "output_pointer": "6d1fe6224bfccbb5f660d08bdb23fba89e75cf7d367b16bc40bcb3d337e12b0e",
            "match_key_image_pointer": "7d64ac02c2823257fb88ab2b34c2ecb6fbd60c59a23650d682d42c71105ac32a",
        }


def test_ringxor_process_bucket_diagnostic_level():
    results = sorted(
        ringxor.process_bucket(all_rings, index_pairs=None, diagnostic_level=1),
        key=lambda x: x["key_image_pointer"],
    )
    assert len(results) == 54

    # Check 0th element
    assert results[0] == {
        "key_image_pointer": "056189f0c3ed7806bc17655152613b3288dfa496b6566b9bbef930efaa87975f",
        "output_pointer": "416e9438f9f69410cf42959dc8ee515318ea6710e5bf8eb76f69c6183a09bded",
        "match_key_image_pointer": "af6cb1936c08108500c3756e81073b6e48b33405be54df891e8b6e433b66b216",
    }

    # Check counterpart of 0th element
    counterpart: dict = next(
        x for x in results if x["key_image_pointer"] == results[0]["match_key_image_pointer"]
    )
    assert counterpart["match_key_image_pointer"] == results[0]["key_image_pointer"]
