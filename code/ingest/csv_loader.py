"""
Dynamic CSV Loader.
Discovers and ingests all tabular data dynamically at runtime.
Guaranteed zero hardcoded filenames.
"""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from code.ingest.schema_validator import DynamicSchemaValidator

logger = logging.getLogger(__name__)


class DynamicCSVLoader:
    """
    Scans a directory for CSV files, loads them with resilient parsing,
    and returns a normalized dictionary of DataFrames.
    """

    def __init__(self, schema_validator: Optional[DynamicSchemaValidator] = None):
        self.validator = schema_validator or DynamicSchemaValidator()
        self.loaded_tables: Dict[str, pd.DataFrame] = {}

    def load_directory(self, directory_path: str | Path) -> Dict[str, pd.DataFrame]:
        """
        Discovers and loads all .csv files from the given directory path.
        """
        path = Path(directory_path)
        if not path.exists():
            logger.warning(f"Dataset directory '{path}' does not exist.")
            return {}

        # Prioritize top-level CSV files in the target directory
        top_level_csvs = [
            f for f in path.glob("*.csv") 
            if not f.stem.lower().startswith("output") and not f.stem.lower().endswith("output")
        ]
        
        if top_level_csvs:
            csv_files = top_level_csvs
        else:
            # If no top-level CSVs, search subdirectories excluding fixtures and cache
            csv_files = [
                f for f in path.rglob("*.csv")
                if not f.stem.lower().startswith("output") 
                and not f.stem.lower().endswith("output")
                and "fixtures" not in f.parts
                and ".cache" not in f.parts
            ]

        # Deduplicate files by absolute resolved path
        unique_files = list({f.resolve(): f for f in csv_files}.values())
        
        logger.info(f"Discovered {len(unique_files)} CSV files in '{path}'.")

        for file_path in unique_files:
            table_name = file_path.stem.lower()
            try:
                # Try standard comma, then fallback to sniffing delimiter
                try:
                    df = pd.read_csv(file_path, skipinitialspace=True)
                except Exception:
                    df = pd.read_csv(file_path, sep=None, engine='python', skipinitialspace=True)
                
                # Standardize column names (lowercase, strip whitespace)
                df.columns = [str(c).strip().lower() for c in df.columns]
                
                # Run schema validation
                self.validator.validate_table(table_name, df)
                self.loaded_tables[table_name] = df
                logger.info(f"Successfully loaded table '{table_name}' from {file_path.name} ({len(df)} rows).")
            except Exception as e:
                logger.error(f"Failed to load CSV '{file_path}': {e}")

        return self.loaded_tables

    def get_table(self, name: str) -> Optional[pd.DataFrame]:
        """Returns table by case-insensitive name if present."""
        return self.loaded_tables.get(name.lower())
