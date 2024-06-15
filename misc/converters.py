# This is a misc script for converting specific data files, not part of the library

from pathlib import Path
import pandas as pd

input_path: Path = Path("...")
output_path: Path = Path("...")

df: pd.DataFrame = pd.read_csv(input_path)
