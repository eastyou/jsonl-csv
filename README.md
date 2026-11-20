# jsonl-csv

[![CI](https://github.com/eastyou/jsonl-csv/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/jsonl-csv/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

JSONL 与 CSV 双向转换的命令行工具，流式处理，适合大文件和管道。

日志、模型输出、数据导出经常是 JSONL 格式，而 Excel / 数据库更习惯 CSV。`jsonlcsv` 不把文件读进内存，几 GB 的文件也能稳定转换，并且会严格报告第几行出了什么问题。

## 特性

- **流式处理**：边读边写，内存占用与文件大小无关
- **双向转换**：`to-csv` 与 `to-jsonl` 两条命令
- **类型推断**：可选把 `1`、`1.5`、`true`、`null` 还原成 JSON 类型
- **嵌套字段**：数组/对象会序列化成紧凑 JSON 放进单元格
- **严格校验**：错误信息带行号；未知字段默认报错，可用 `--drop-extra` 忽略
- **管道友好**：默认读写标准输入输出
- **零依赖**：只使用 Python 标准库，Python 3.9+

## 安装

```bash
pip install "git+https://github.com/eastyou/jsonl-csv.git"
```

本地使用：

```bash
git clone https://github.com/eastyou/jsonl-csv.git
cd jsonl-csv
python3 -m pip install -e .
```

不安装也能运行：`python3 -m jsonlcsv to-csv -i data.jsonl`

## 使用

```console
$ cat users.jsonl
{"name":"张三","age":18,"vip":true}
{"name":"李四","age":20,"vip":false}

$ jsonlcsv to-csv -i users.jsonl
name,age,vip
张三,18,true
李四,20,false
```

```bash
# 指定列顺序（也用于约束输出结构）
jsonlcsv to-csv -i users.jsonl --columns name,vip,age

# 大文件管道处理
cat events.jsonl | jsonlcsv to-csv > events.csv

# CSV 转 JSONL，并推断数字与布尔类型
jsonlcsv to-jsonl -i events.csv --infer-types

# 使用分号分隔
jsonlcsv to-csv -i users.jsonl --delimiter ";"

# 忽略第一行之外的额外字段
jsonlcsv to-csv -i mixed.jsonl --drop-extra
```

### 参数

`jsonlcsv to-csv`

| 参数 | 说明 |
| --- | --- |
| `-i, --input FILE` | 输入文件，默认标准输入 |
| `-o, --output FILE` | 输出文件，默认标准输出 |
| `--columns A,B` | 指定列顺序，默认使用第一行的字段 |
| `--delimiter CHAR` | 分隔符，默认 `,` |
| `--drop-extra` | 忽略未声明的字段，默认报错 |

`jsonlcsv to-jsonl`

| 参数 | 说明 |
| --- | --- |
| `-i, --input FILE` | 输入文件，默认标准输入 |
| `-o, --output FILE` | 输出文件，默认标准输出 |
| `--infer-types` | 推断整数、浮点数、布尔值和 null |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 转换成功 |
| `2` | 参数错误、文件读写失败或数据格式错误 |

## 转换规则

| JSON 值 | CSV 单元格 |
| --- | --- |
| `null` | 空字符串 |
| `true` / `false` | `true` / `false` |
| 数字 | 原样输出 |
| 字符串 | 原样输出（含逗号、引号、换行时由 CSV 规则转义） |
| 数组 / 对象 | 紧凑 JSON，例如 `{"a":1}` |

- 表头默认取自第一条记录，之后出现的字段若不匹配会报错并提示行号
- 需要稳定列结构时，请显式传入 `--columns`
- `to-jsonl` 只有在 `--infer-types` 时才会把文本转成数字/布尔；否则全部按字符串输出

## 作为库使用

```python
import io
from jsonlcsv import jsonl_to_csv

source = io.StringIO('{"a":1,"b":2}\n')
destination = io.StringIO()
count = jsonl_to_csv(source, destination)
print(count, destination.getvalue())
```

## 开发与测试

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE) © 2026 eastyou
