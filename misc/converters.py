# This is a misc script for converting specific data files, not part of the library

# Imports
from pathlib import Path
import pandas as pd
import json
from loguru import logger
from tqdm.auto import tqdm

# Configure
ring_data: Path = Path("/media/m/data_drive_2/monero/reboot/flood-ring-member-ages-for-isthmus.csv")
label_data: Path = Path("/media/m/data_drive_2/monero/package/transactions_labeled.feather")

output_tag: str = "d1"
output_path: Path = Path("/home/m/Projects/GitHub/ringxor/data/local_only/")
logger.info(f"Starting: {output_tag=}")

# Check and load inputs
if not ring_data.exists():
    logger.error(f"Ring data file not found: {ring_data}")
    raise FileNotFoundError(f"Ring data file not found: {ring_data}")
else:
    df_rings: pd.DataFrame = pd.read_csv(ring_data)
    logger.info(f"Loaded ring data: {df_rings.shape}")
if not label_data.exists():
    logger.error(f"Label data file not found: {label_data}")
    raise FileNotFoundError(f"Label data file not found: {label_data}")
else:
    df_labels: pd.DataFrame = pd.read_feather(label_data)
    logger.info(f"Loaded label data: {df_labels.shape}")

# Process
df_rings["key_image_pointer"] = df_rings["tx_hash"] + "-" + df_rings["input_num"].astype(str)
logger.info(f"Added key_image_pointer column from tx hash + input num")
df_rings["output_pointer"] = df_rings["output_index"].astype(int).astype(str)
logger.info(f"Added output_pointer column from output index")


def aggregate_and_output_to_json(df: pd.DataFrame, output_file: Path):
    logger.info(f"Aggregating data ({len(df)=}) to: {output_file}")
    aggregated_data = {}

    for _, row in tqdm(df.iterrows(), mininterval=2, total=len(df), desc="Aggregating data"):
        key_image_pointer = row["key_image_pointer"]
        output_pointer = row["output_pointer"]

        if key_image_pointer not in aggregated_data:
            aggregated_data[key_image_pointer] = []

        aggregated_data[key_image_pointer].append(output_pointer)

    logger.info("About to save aggregated data...")
    with open(output_file, "w") as json_file:
        json.dump(aggregated_data, json_file, indent=2)
    logger.info(f"Saved aggregated data to: {output_file}")


# Save just the subset of transactions with potential anomalous decoy reuse labels
anomalous_tx_hashes = df_labels[
    (df_labels["anomalous_intertransaction_decoy_reuse"] == True)
    | (df_labels["anomalous_intratransaction_decoy_reuse"] == True)
]["tx_hash"].unique()
num_txns: int = df_rings["tx_hash"].nunique()
logger.info(f"Flagged subset {len(anomalous_tx_hashes)=} out of {num_txns=} transactions.")
subset_path = output_path / f"subset_{output_tag}.json"
aggregate_and_output_to_json(df_rings[df_rings["tx_hash"].isin(anomalous_tx_hashes)], subset_path)
logger.info(f"Output subset data to: {subset_path}")

# Save everything
all_rows_path = output_path / f"all_rows_{output_tag}.json"
aggregate_and_output_to_json(df_rings, all_rows_path)
logger.info(f"Output all data to: {all_rows_path}")
