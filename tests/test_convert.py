"""转换核心逻辑的单元测试。"""

import io
import json
import unittest

from jsonlcsv.convert import ConversionError, csv_to_jsonl, jsonl_to_csv, read_jsonl


def convert_jsonl(text, **kwargs):
    destination = io.StringIO()
    count = jsonl_to_csv(io.StringIO(text), destination, **kwargs)
    return count, destination.getvalue()


def convert_csv(text, **kwargs):
    destination = io.StringIO()
    count = csv_to_jsonl(io.StringIO(text), destination, **kwargs)
    return count, destination.getvalue()


class JsonlToCsvTests(unittest.TestCase):
    def test_basic(self):
        count, output = convert_jsonl('{"name":"张三","age":18}\n{"name":"李四","age":20}\n')
        self.assertEqual(count, 2)
        self.assertEqual(output, "name,age\n张三,18\n李四,20\n")

    def test_missing_field_becomes_empty(self):
        count, output = convert_jsonl('{"name":"张三","age":18}\n{"name":"李四"}\n')
        self.assertEqual(count, 2)
        self.assertEqual(output, "name,age\n张三,18\n李四,\n")

    def test_nested_and_null_values(self):
        line = json.dumps(
            {"name": "张三", "tags": ["new", "vip"], "note": None, "ok": True},
            ensure_ascii=False,
        )
        _, output = convert_jsonl(line + "\n")
        self.assertEqual(
            output, 'name,tags,note,ok\n张三,"[""new"",""vip""]",,true\n'
        )

    def test_nested_value_is_compact_json(self):
        line = json.dumps({"tags": ["b", "a"]}) + "\n"
        _, output = convert_jsonl(line)
        self.assertEqual(output, 'tags\n"[""b"",""a""]"\n')

    def test_custom_columns_order(self):
        _, output = convert_jsonl('{"a":1,"b":2}\n', columns=["b", "a"])
        self.assertEqual(output, "b,a\n2,1\n")

    def test_extra_field_raises(self):
        with self.assertRaises(ConversionError) as context:
            convert_jsonl('{"a":1}\n{"a":2,"b":3}\n')
        self.assertIn("第 2 行", str(context.exception))

    def test_drop_extra(self):
        count, output = convert_jsonl('{"a":1}\n{"a":2,"b":3}\n', drop_extra=True)
        self.assertEqual(count, 2)
        self.assertEqual(output, "a\n1\n2\n")

    def test_invalid_json(self):
        with self.assertRaises(ConversionError) as context:
            convert_jsonl('{"a":1}\nnot-json\n')
        self.assertIn("第 2 行", str(context.exception))

    def test_non_object_line(self):
        with self.assertRaises(ConversionError):
            convert_jsonl("[1,2,3]\n")

    def test_empty_input(self):
        count, output = convert_jsonl("")
        self.assertEqual(count, 0)
        self.assertEqual(output, "")

    def test_empty_input_with_columns_writes_header(self):
        count, output = convert_jsonl("", columns=["a", "b"])
        self.assertEqual(count, 0)
        self.assertEqual(output, "a,b\n")

    def test_invalid_arguments(self):
        with self.assertRaises(ConversionError):
            convert_jsonl("", columns=[])
        with self.assertRaises(ConversionError):
            convert_jsonl("", columns=["a", "a"])
        with self.assertRaises(ConversionError):
            convert_jsonl("", delimiter=",,")

    def test_blank_lines_are_skipped(self):
        count, output = convert_jsonl('\n{"a":1}\n\n')
        self.assertEqual(count, 1)
        self.assertEqual(output, "a\n1\n")


class CsvToJsonlTests(unittest.TestCase):
    def test_basic(self):
        count, output = convert_csv("name,age\n张三,18\n")
        self.assertEqual(count, 1)
        self.assertEqual(json.loads(output), {"name": "张三", "age": "18"})

    def test_infer_types(self):
        _, output = convert_csv('a,b,c,d,e\n1,1.5,true,false,null\n', infer_types=True)
        self.assertEqual(
            json.loads(output), {"a": 1, "b": 1.5, "c": True, "d": False, "e": None}
        )

    def test_without_infer_types(self):
        _, output = convert_csv("a,b\n1,true\n")
        self.assertEqual(json.loads(output), {"a": "1", "b": "true"})

    def test_quoted_values(self):
        _, output = convert_csv('name,note\n张三,"你好, 世界"\n')
        self.assertEqual(json.loads(output)["note"], "你好, 世界")

    def test_empty_csv(self):
        count, output = convert_csv("")
        self.assertEqual(count, 0)
        self.assertEqual(output, "")

    def test_extra_columns_raise(self):
        with self.assertRaises(ConversionError):
            convert_csv("a,b\n1,2,3\n")

    def test_missing_values_become_empty(self):
        _, output = convert_csv("a,b\n1,\n")
        self.assertEqual(json.loads(output), {"a": "1", "b": ""})


class RoundtripTests(unittest.TestCase):
    def test_roundtrip_keeps_scalars(self):
        rows = [
            {"name": "张三", "score": 98, "pass": True},
            {"name": "李 四", "score": 87, "pass": False},
        ]
        source = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        _, csv_text = convert_jsonl(source)
        _, jsonl_text = convert_csv(csv_text, infer_types=True)
        parsed = [json.loads(line) for line in jsonl_text.splitlines()]
        self.assertEqual(parsed, rows)


if __name__ == "__main__":
    unittest.main()
