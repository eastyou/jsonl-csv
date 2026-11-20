"""支持 ``python -m jsonlcsv`` 运行。"""

import sys

from jsonlcsv.cli import main

if __name__ == "__main__":
    sys.exit(main())
