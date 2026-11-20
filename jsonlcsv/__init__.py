"""jsonl-csv: JSONL 与 CSV 双向转换。"""

from jsonlcsv.convert import ConversionError, csv_to_jsonl, jsonl_to_csv, read_jsonl

__all__ = ["ConversionError", "csv_to_jsonl", "jsonl_to_csv", "read_jsonl"]
__version__ = "0.1.0"
