"""Run from the repository root: python -m specgen generate."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from .common import stable_json
from .engine import config, inventory, projects, run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="inputのソースから機能別Markdown仕様書を生成（入力ソースは実行しません）")
    parser.add_argument("command", choices=["generate", "scan"])
    parser.add_argument("--root", default=".", help="リポジトリルート")
    parser.add_argument("--config", default="specgen.toml", help="rootからの設定ファイル相対パス")
    parser.add_argument("--force", action="store_true", help="全件再解析・生成先の編集も上書き（inputは変更しません）")
    parser.add_argument("--strict", action="store_true", help="限定解析・警告・ソースなしでも終了コード1")
    parser.add_argument("--clean", action="store_true", help="所有台帳にある不要な生成物のみ削除。手修正済みは保護")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        cfg = config(root, args.config)
        if args.command == "scan":
            result = [{"project": p["name"], "files": inventory(root, p, cfg)} for p in projects(root, cfg)]
            print(stable_json(result))
            return 0
        result = run(root, cfg, force=args.force, strict=args.strict, clean=args.clean)
        print(stable_json(result))
        return result["exit_code"]
    except KeyboardInterrupt:
        print("中断しました。保存済みの解析キャッシュは次回再利用します。", file=sys.stderr)
        return 130
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"specgen: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
