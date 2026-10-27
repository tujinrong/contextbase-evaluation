"""Filesystem guards for final build files and method-local temporary work."""
from pathlib import Path
import json
import os


def ensure_directory(directory: Path) -> None:
    directory = directory.absolute()
    for part in [*reversed(directory.parents), directory]:
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise RuntimeError(f'Linked output directory refused: {part}')
        if part.exists():
            if not part.is_dir() or str(part.resolve()).casefold() != str(part).casefold():
                raise RuntimeError(f'Redirected output directory refused: {part}')
        else:
            part.mkdir()


def regular_destination(target: Path) -> None:
    ensure_directory(target.parent)
    if target.is_symlink() or getattr(target, 'is_junction', lambda: False)() or (target.exists() and not target.is_file()):
        raise RuntimeError(f'Regular output file required: {target}')


def staging_file(scratch: Path, name: str) -> Path:
    ensure_directory(scratch)
    target = scratch / name
    regular_destination(target)
    if target.exists():
        target.unlink()  # Remove this directory entry; never truncate a linked file.
    return target  # Caller must use exclusive create (x), never write-through (w).


def write_latest(target: Path, text: str, scratch: Path) -> None:
    regular_destination(target)
    temporary = staging_file(scratch, target.name + '.pending')
    with temporary.open('x', encoding='utf-8') as stream:
        stream.write(text)
    os.replace(temporary, target)


def write_json_latest(target: Path, value: object, scratch: Path) -> None:
    write_latest(target, json.dumps(value, ensure_ascii=False, indent=2) + '\n', scratch)
