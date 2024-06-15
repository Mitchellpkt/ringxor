import json
from src.ringxor import ringxor
import pathlib
from typing import List, Dict, Any
from loguru import logger
import pandas as pd

num_workers: int = 2
# input_data_path: pathlib.Path = pathlib.Path.cwd() / ".." / "data" / "local_only" / "subset_d1.json"
input_data_path: pathlib.Path = pathlib.Path.cwd().parent / "data" / "version_controlled" / "demo_rings.json"
output_data_path: pathlib.Path = pathlib.Path.cwd().parent / "data" / "local_only" / "results" / "result_from_demo_rings.csv"
logger.info(f"Loading data from: {input_data_path} with {num_workers=}")

# Load the test data
with open(input_data_path, "r") as f:
    all_rings_raw = json.load(f)
logger.info(f"Loaded ring data: {len(all_rings_raw)}")

# The code uses sets, but they can't be serialized to json, so we convert back here from temporary list representation
all_rings: ringxor.ring_bucket = {key_image: set(ring) for key_image, ring in all_rings_raw.items()}
logger.info(f"Converted ring data to sets: {len(all_rings)}")

# Do the analysis
results_raw: List[Dict[str, Any]] = ringxor.process_bucket(all_rings, index_pairs=None, diagnostic_level=1)
logger.info(f"Processed bucket: {len(results_raw)}")

# Reshape the results
df: pd.DataFrame = pd.DataFrame(results_raw)
logger.info(f"Converted results to DataFrame: {df.shape}")
logger.info(f"\n{print(df.head(10))}")

# Save
output_data_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_data_path, index=False)
logger.info(f"Saved results to: {output_data_path}")
