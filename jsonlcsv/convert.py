"""JSONL 与 CSV 之间的流式转换。"""

from __future__ import annotations

import csv
import json
from typing import Any, Dict, Iterator, List, Optional, Sequence, TextIO, Tuple


class ConversionError(ValueError):
    """输入数据不符合预期。"""


def _stringify(value: Any) -> str:
    """把 JSON 值转换成适合放入 CSV 单元格的文本。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _coerce(text: str) -> Any:
    """把 CSV 文本按常见类型推断，失败时保留原字符串。"""
    stripped = text.strip()
    if stripped == "":
        return ""
    lowered = stripped.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        return text


def read_jsonl(stream: TextIO) -> Iterator[Tuple[int, Dict[str, Any]]]:
    """逐行解析 JSONL，产出 ``(行号, 对象)``。

    Raises:
        ConversionError: 某一行不是合法 JSON，或不是 JSON 对象。
    """
    for line_number, raw in enumerate(stream, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ConversionError(
                "第 {0} 行不是合法 JSON: {1}".format(line_number, exc.msg)
            ) from exc
        if not isinstance(value, dict):
            raise ConversionError("第 {0} 行不是 JSON 对象".format(line_number))
        yield line_number, value


def jsonl_to_csv(
    source: TextIO,
    destination: TextIO,
    columns: Optional[Sequence[str]] = None,
    delimiter: str = ",",
    drop_extra: bool = False,
) -> int:
    """把 JSONL 流式转换为 CSV，返回写出的数据行数。

    内存占用与文件大小无关：只在第一行时确定表头。

    Raises:
        ConversionError: 字段非法、出现未知字段或参数不合法。
    """
    if len(delimiter) != 1:
        raise ConversionError("分隔符必须是单个字符")
    if columns is not None:
        if not columns:
            raise ConversionError("列名不能为空")
        if len(set(columns)) != len(columns):
            raise ConversionError("列名不能重复")

    writer = csv.writer(destination, delimiter=delimiter, lineterminator="\n")
    fieldnames: Optional[List[str]] = list(columns) if columns is not None else None
    if fieldnames is not None:
        writer.writerow(fieldnames)

    count = 0
    for line_number, record in read_jsonl(source):
        if fieldnames is None:
            fieldnames = list(record.keys())
            writer.writerow(fieldnames)
        extra = [key for key in record if key not in fieldnames]
        if extra:
            if not drop_extra:
                raise ConversionError(
                    "第 {0} 行包含未声明字段: {1}".format(
                        line_number, ", ".join(sorted(extra))
                    )
                )
        writer.writerow([_stringify(record.get(name)) for name in fieldnames])
        count += 1
    return count


def csv_to_jsonl(
    source: TextIO,
    destination: TextIO,
    infer_types: bool = False,
) -> int:
    """把 CSV 流式转换为 JSONL，返回写出的行数。"""
    reader = csv.DictReader(source)
    if reader.fieldnames is None:
        return 0
    if len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ConversionError("CSV 表头存在重复列名")

    count = 0
    for row in reader:
        if None in row:
            raise ConversionError(
                "第 {0} 行字段数多于表头".format(reader.line_num)
            )
        record: Dict[str, Any] = {}
        for name in reader.fieldnames:
            value = row.get(name)
            if value is None:
                record[name] = ""
            else:
                record[name] = _coerce(value) if infer_types else value
        destination.write(json.dumps(record, ensure_ascii=False) + "\n")
        count += 1
    return count
