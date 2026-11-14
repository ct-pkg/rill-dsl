"""端到端真脚本的进程侧：从 stdin 读 JSON，把 port 写到 stdout。"""

import json
import sys


def main():
    config = json.load(sys.stdin)
    sys.stdout.write(str(config["port"]))


if __name__ == "__main__":
    main()
