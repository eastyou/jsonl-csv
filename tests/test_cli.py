"""jsonlcsv 命令行的单元测试。"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from jsonlcsv.cli import main


class CliTests(unittest.TestCase):
    def _run(self, argv, stdin_text=None):
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_stdin = sys.stdin
        if stdin_text is not None:
            sys.stdin = io.StringIO(stdin_text)
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(argv)
        finally:
            sys.stdin = old_stdin
        return code, stdout.getvalue(), stderr.getvalue()

    def _write(self, directory, name, content):
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def test_jsonl_to_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(tmp, "in.jsonl", '{"a":1,"b":2}\n{"a":3,"b":4}\n')
            output = os.path.join(tmp, "out.csv")
            code, _, err = self._run(["to-csv", "-i", source, "-o", output])
            with open(output, "r", encoding="utf-8") as handle:
                content = handle.read()
        self.assertEqual(code, 0)
        self.assertEqual(content, "a,b\n1,2\n3,4\n")
        self.assertIn("已写入 2 行", err)

    def test_stdin_to_stdout(self):
        code, out, _ = self._run(["to-csv"], stdin_text='{"a":1}\n')
        self.assertEqual(code, 0)
        self.assertEqual(out, "a\n1\n")

    def test_csv_to_jsonl_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._write(tmp, "in.csv", "a,b\n1,2\n")
            output = os.path.join(tmp, "out.jsonl")
            code, _, _ = self._run(["to-jsonl", "-i", source, "-o", output])
            with open(output, "r", encoding="utf-8") as handle:
                content = handle.read()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(content), {"a": "1", "b": "2"})

    def test_infer_types(self):
        code, out, _ = self._run(["to-jsonl", "--infer-types"], stdin_text="a\n1\n")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"a": 1})

    def test_columns_option(self):
        code, out, _ = self._run(
            ["to-csv", "--columns", "b,a"], stdin_text='{"a":1,"b":2}\n'
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "b,a\n2,1\n")

    def test_missing_input_file(self):
        code, _, err = self._run(["to-csv", "-i", "/definitely/not/here.jsonl"])
        self.assertEqual(code, 2)
        self.assertIn("文件不存在", err)

    def test_invalid_json_reports_line(self):
        code, _, err = self._run(["to-csv"], stdin_text='{"a":1}\nbroken\n')
        self.assertEqual(code, 2)
        self.assertIn("第 2 行", err)

    def test_empty_columns_option_is_rejected(self):
        with self.assertRaises(SystemExit):
            self._run(["to-csv", "--columns", "a,,b"], stdin_text='{"a":1}\n')


if __name__ == "__main__":
    unittest.main()
