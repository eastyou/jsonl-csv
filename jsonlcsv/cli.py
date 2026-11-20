"""jsonl-csv 命令行入口。"""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from typing import Iterator, List, Optional, Sequence, TextIO

from jsonlcsv.convert import ConversionError, csv_to_jsonl, jsonl_to_csv


class InputError(Exception):
    """文件读写失败。"""


@contextmanager
def _open_input(path: str) -> Iterator[TextIO]:
    if path == "-":
        yield sys.stdin
        return
    try:
        handle = open(path, "r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise InputError("文件不存在: {0}".format(path)) from exc
    except IsADirectoryError as exc:
        raise InputError("这是一个目录，不是文件: {0}".format(path)) from exc
    except PermissionError as exc:
        raise InputError("没有权限读取: {0}".format(path)) from exc
    except OSError as exc:
        raise InputError(
            "读取失败: {0} ({1})".format(path, exc.strerror or exc)
        ) from exc
    try:
        with handle:
            yield handle
    except UnicodeDecodeError as exc:
        raise InputError("不是 UTF-8 文本: {0}".format(path)) from exc


@contextmanager
def _open_output(path: str) -> Iterator[TextIO]:
    if path == "-":
        yield sys.stdout
        return
    try:
        handle = open(path, "w", encoding="utf-8", newline="")
    except PermissionError as exc:
        raise InputError("没有写入权限: {0}".format(path)) from exc
    except OSError as exc:
        raise InputError(
            "写入失败: {0} ({1})".format(path, exc.strerror or exc)
        ) from exc
    with handle:
        yield handle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jsonlcsv",
        description="JSONL 与 CSV 双向流式转换，适合大文件与管道处理。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    to_csv = subparsers.add_parser("to-csv", help="JSONL 转 CSV")
    to_csv.add_argument("-i", "--input", default="-", metavar="FILE", help="输入文件，默认标准输入")
    to_csv.add_argument("-o", "--output", default="-", metavar="FILE", help="输出文件，默认标准输出")
    to_csv.add_argument(
        "--columns", metavar="A,B", help="指定列顺序，默认使用第一行的字段顺序"
    )
    to_csv.add_argument("--delimiter", default=",", metavar="CHAR", help="CSV 分隔符，默认逗号")
    to_csv.add_argument(
        "--drop-extra", action="store_true", help="忽略未声明的字段，默认报错"
    )

    to_jsonl = subparsers.add_parser("to-jsonl", help="CSV 转 JSONL")
    to_jsonl.add_argument("-i", "--input", default="-", metavar="FILE", help="输入文件，默认标准输入")
    to_jsonl.add_argument("-o", "--output", default="-", metavar="FILE", help="输出文件，默认标准输出")
    to_jsonl.add_argument(
        "--infer-types", action="store_true",
        help="把整数、浮点数、true/false、null 推断为对应 JSON 类型",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "to-csv":
            columns: Optional[List[str]] = None
            if args.columns is not None:
                columns = [item.strip() for item in args.columns.split(",")]
                if not all(columns):
                    parser.error("--columns 中存在空列名")
            with _open_input(args.input) as source, _open_output(args.output) as destination:
                count = jsonl_to_csv(
                    source,
                    destination,
                    columns=columns,
                    delimiter=args.delimiter,
                    drop_extra=args.drop_extra,
                )
            print("已写入 {0} 行 CSV".format(count), file=sys.stderr)
        else:
            with _open_input(args.input) as source, _open_output(args.output) as destination:
                count = csv_to_jsonl(source, destination, infer_types=args.infer_types)
            print("已写入 {0} 行 JSONL".format(count), file=sys.stderr)
    except (InputError, ConversionError) as exc:
        print("错误: {0}".format(exc), file=sys.stderr)
        return 2

    return 0
