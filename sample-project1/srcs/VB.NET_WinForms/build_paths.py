"""Method-local output guard. Inputs must never be reached through output redirects."""
from pathlib import Path
import os
import shutil
import stat


class OutputPaths:
    def __init__(self, root):
        self.root = self.lexical(root)
        self.regular(self.root)
        if not self.root.is_dir():
            raise ValueError('The method root must be a regular directory')
        self.roots = (self.root / 'build', self.root / '.tmp')

    @staticmethod
    def lexical(path):
        return Path(os.path.abspath(os.fspath(path)))

    @staticmethod
    def redirected(path):
        info = path.lstat()
        return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)

    def regular(self, path):
        """Validate all existing ancestors without accepting a resolved alias."""
        path = self.lexical(path)
        for item in [*reversed(path.parents), path]:
            if os.path.lexists(item):
                if self.redirected(item):
                    raise ValueError('Redirected path is forbidden: ' + str(item))
                if item != path and not item.is_dir():
                    raise ValueError('Output ancestor must be a regular directory: ' + str(item))
                if not item.is_dir() and not item.is_file():
                    raise ValueError('Only regular files/directories are allowed: ' + str(item))
            if os.path.normcase(os.path.realpath(item)) != os.path.normcase(str(item)):
                raise ValueError('Real path differs from lexical path: ' + str(item))
        return path

    def output(self, path, tree=False):
        path = self.lexical(path)
        if not any(path == root or path.is_relative_to(root) for root in self.roots):
            raise ValueError('Writes are limited to this method build/ and .tmp/: ' + str(path))
        self.regular(path)
        if tree and path.is_dir():
            pending = [path]
            while pending:
                directory = pending.pop()
                with os.scandir(directory) as entries:
                    for entry in entries:
                        child = Path(entry.path)
                        # Each parent has already been validated while descending this tree.
                        # scandir supplies lexical child names, so no resolved aliases are accepted.
                        if self.redirected(child):
                            raise ValueError('Redirected output descendant is forbidden: ' + str(child))
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(child)
                        elif not entry.is_file(follow_symlinks=False):
                            raise ValueError('Only regular output descendants are allowed: ' + str(child))
        return path

    def preflight(self):
        # External compilers/package managers also write descendants unknown to this helper.
        for root in self.roots:
            self.output(root)
        for relative in ['.tmp/build','.tmp/test-results','.tmp/runtime','.tmp/nuget',
                         '.tmp/dotnet','.tmp/dotnet-home','.tmp/frontend',
                         'build/app','build/publish','build/test-results','build/database']:
            self.output(self.root / relative, tree=True)

    def mkdir(self, path):
        path = self.output(path)
        path.mkdir(parents=True, exist_ok=True)
        return self.output(path)

    def write(self, path, text, encoding='utf8'):
        path = self.output(path)
        self.mkdir(path.parent)
        path.write_text(text, encoding=encoding)

    def copyfile(self, source, target):
        source = self.regular(source)
        target = self.output(target)
        self.mkdir(target.parent)
        shutil.copyfile(source, target)

    def remove(self, path):
        path = self.output(path, tree=True)
        if path.exists():
            shutil.rmtree(path) if path.is_dir() else path.unlink()

    def replace_tree(self, source, target):
        source = self.output(source, tree=True)
        target = self.output(target, tree=True)
        self.mkdir(target.parent)
        self.remove(target)
        shutil.copytree(source, target)
        return self.output(target, tree=True)

    def frontend_link(self):
        """The sole source-tree exception is this exact dependency junction/symlink."""
        link = self.root / 'frontend/node_modules'
        target = self.output(self.root / '.tmp/frontend/node_modules', tree=True)
        self.regular(link.parent)
        if os.path.lexists(link):
            if not self.redirected(link):
                raise ValueError('frontend/node_modules must be the dedicated temporary dependency link')
            if os.path.normcase(os.path.realpath(link)) != os.path.normcase(str(target)):
                raise ValueError('Unexpected frontend/node_modules redirect: ' + str(link))
        return link, target
