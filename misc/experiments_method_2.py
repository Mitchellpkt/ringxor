import json
from src.ringxor import ringxor
import pathlib
from typing import List, Dict, Any, Optional, Set, Tuple
from loguru import logger
import pandas as pd
from tqdm.auto import tqdm

num_workers: int = 1
limit: Optional[int] = 10_000
convert_to_ints: bool = True  # Only do this if your output index can be converted to int
input_data_path: pathlib.Path = pathlib.Path.cwd() / ".." / "data" / "local_only" / "subset_d1.json"
# input_data_path: pathlib.Path = pathlib.Path.cwd().parent / "data" / "version_controlled" / "demo_rings.json"
output_data_path: pathlib.Path = (
    pathlib.Path.cwd().parent / "data" / "local_only" / "results" / "result_d1.csv"
)
logger.info(f"Loading data from: {input_data_path} with {num_workers=}")

# Load the test data
with open(input_data_path, "r") as f:
    all_rings_raw = json.load(f)
logger.info(f"Loaded ring data: {len(all_rings_raw)}")

# The ringxor logic doesn't care if the values are strings or ints, but if using output idx can convert to int here
if convert_to_ints:
    all_rings_raw = {key_image: [int(x) for x in ring] for key_image, ring in all_rings_raw.items()}
    logger.info(f"Converted ring data to ints")

# Sort the elements within rings
all_rings: Dict[str, List[Any]] = {key_image: sorted(ring) for key_image, ring in all_rings_raw.items()}
logger.info(f"Sorted data within rings: {len(all_rings)}")

# Optional limit to speed up testing
if limit:
    all_rings = dict(list(all_rings.items())[:limit])
    logger.info(f"Limited to {len(all_rings)} rings")

# Build the indices of interest
relevant_keys: Set[str] = set()
index_pairs: List[Tuple[str, str]] = []
for left_key, left_ring in tqdm(all_rings.items()):
    for right_key, right_ring in all_rings.items():
        # Only do upper triangle
        if left_key >= right_key:
            continue

        # Only compare rings of the same length
        if len(left_ring) != len(right_ring):
            continue

        # Check how many elements differ
        diff_len: int = len(set(left_ring[:3]) ^ set(right_ring[:3]))
        if diff_len <= 2:  # is potentially relevant
            relevant_keys.add(left_key)
            relevant_keys.add(right_key)
            index_pairs.append((left_key, right_key))
        elif diff_len > 2:
            pass  # If the lists were sorted, we could do more here...
logger.info(f"Built index pairs: {len(index_pairs)}")

# We don't need to pass down rings that won't be inspected
relevant_rings = {key: set(all_rings[key]) for key in relevant_keys if key in relevant_keys}
logger.info(f"Cut down to relevant rings, and converted to sets: {len(relevant_rings)}")

# Do the analysis
results_raw: List[Dict[str, Any]] = ringxor.process_bucket(
    relevant_rings, index_pairs=index_pairs, diagnostic_level=1, num_workers=num_workers
)
logger.info(f"Processed bucket: {len(results_raw)}")

# Reshape the results
df: pd.DataFrame = pd.DataFrame(results_raw)
logger.info(f"Converted results to DataFrame: {df.shape}")
logger.info(f"\n{print(df.head(10))}")

# Save
output_data_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_data_path, index=False)
logger.info(f"Saved results to: {output_data_path}")
