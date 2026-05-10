"""Virtual Filesystem - In-memory file and directory management."""
import os
import time
from datetime import datetime
from pathlib import PurePosixPath


class FileEntry:
    """Represents a file or directory in the virtual filesystem."""

    def __init__(self, name, is_dir=False, parent=None, content="", permissions="rw-r--r--"):
        self.name = name
        self.is_dir = is_dir
        self.parent = parent
        self.content = content if not is_dir else ""
        self.permissions = permissions
        now = time.time()
        self.created = now
        self.modified = now
        self.accessed = now
        self.children = {} if is_dir else None

    @property
    def size(self):
        if self.is_dir:
            return sum(c.size for c in self.children.values()) if self.children else 0
        return len(self.content.encode('utf-8'))

    @property
    def path(self):
        if self.parent is None:
            return "/"
        parts = []
        node = self
        while node is not None:
            parts.append(node.name)
            node = node.parent
        if len(parts) == 1:
            return "/"
        return "/" + "/".join(reversed(parts[:-1]))

    def to_dict(self):
        return {
            "name": self.name,
            "is_dir": self.is_dir,
            "size": self.size,
            "permissions": self.permissions,
            "modified": datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M:%S"),
            "created": datetime.fromtimestamp(self.created).strftime("%Y-%m-%d %H:%M:%S"),
        }


class VirtualFS:
    """In-memory virtual filesystem."""

    def __init__(self):
        self.root = FileEntry("", is_dir=True)
        self._cwd = "/home/user"
        self._init_structure()

    def _init_structure(self):
        """Create default directory structure."""
        dirs = [
            "/home", "/home/user", "/home/user/Desktop", "/home/user/Documents",
            "/home/user/Downloads", "/home/user/Pictures", "/home/user/Music",
            "/etc", "/var", "/var/log", "/tmp", "/bin", "/usr", "/usr/bin",
            "/usr/lib", "/opt", "/mnt", "/media", "/root", "/sys", "/proc",
        ]
        for d in dirs:
            self.mkdir(d, parents=True)

        # Create some default files
        self.create_file("/etc/hostname", "virtual-os\n")
        self.create_file("/etc/os-release", 'NAME="VirtualOS"\nVERSION="1.0"\nID=virtualos\n')
        self.create_file("/etc/resolv.conf", "nameserver 8.8.8.8\nnameserver 8.8.4.4\n")
        self.create_file("/home/user/.bashrc", "# VirtualOS bashrc\nexport PATH=/usr/bin:/bin\n")
        self.create_file("/home/user/.profile", "# VirtualOS profile\n")
        self.create_file("/var/log/syslog", "[INFO] System initialized\n")
        self.create_file("/home/user/Documents/readme.txt", "Welcome to VirtualOS!\n")

    def _normalize(self, path):
        """Normalize path using POSIX semantics (forward slashes)."""
        # Split, remove empty parts, handle . and ..
        parts = []
        for part in path.split('/'):
            if part == '' or part == '.':
                continue
            elif part == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return '/' + '/'.join(parts) if parts else '/'

    def _resolve_path(self, path):
        """Resolve a path to a FileEntry."""
        if not path:
            path = self._cwd
        if path.startswith("~"):
            path = "/home/user" + path[1:]
        if not path.startswith("/"):
            path = self._cwd.rstrip("/") + "/" + path
        path = self._normalize(path)
        if path == "/":
            return self.root

        parts = [p for p in path.split("/") if p]
        node = self.root
        for part in parts:
            if node is None or not node.is_dir or part not in node.children:
                return None
            node = node.children[part]
        return node

    def _resolve_parent(self, path):
        """Get parent path and name."""
        path = self._normalize(path)
        if path == "/":
            return "/", ""
        parts = path.rsplit("/", 1)
        parent_path = parts[0] or "/"
        name = parts[1]
        return parent_path, name

    def get_cwd(self):
        return self._cwd

    def cd(self, path):
        """Change current working directory."""
        entry = self._resolve_path(path)
        if entry is None:
            return False, f"cd: no such directory: {path}"
        if not entry.is_dir:
            return False, f"cd: not a directory: {path}"
        self._cwd = entry.path if entry.path != "" else "/"
        return True, ""

    def ls(self, path=None, long_format=False):
        """List directory contents."""
        entry = self._resolve_path(path or self._cwd)
        if entry is None:
            return False, [], f"ls: cannot access '{path or self._cwd}': No such file or directory"
        if not entry.is_dir:
            return False, [], f"ls: not a directory: {path or self._cwd}"
        items = sorted(entry.children.values(), key=lambda x: (not x.is_dir, x.name))
        if long_format:
            return True, [i.to_dict() for i in items], ""
        return True, [i.name for i in items], ""

    def mkdir(self, path, parents=False):
        """Create a directory."""
        path = self._normalize(path)
        if parents:
            parts = [p for p in path.split("/") if p]
            current = self.root
            for part in parts:
                if part not in current.children:
                    current.children[part] = FileEntry(part, is_dir=True, parent=current)
                current = current.children[part]
            return True, ""
        parent_path, name = self._resolve_parent(path)
        parent = self._resolve_path(parent_path)
        if parent is None:
            return False, f"mkdir: cannot create directory '{path}': No such file or directory"
        if not parent.is_dir:
            return False, f"mkdir: cannot create directory '{path}': Not a directory"
        if name in parent.children:
            return False, f"mkdir: cannot create directory '{path}': File exists"
        parent.children[name] = FileEntry(name, is_dir=True, parent=parent)
        parent.modified = time.time()
        return True, ""

    def create_file(self, path, content=""):
        """Create a file with optional content."""
        parent_path, name = self._resolve_parent(path)
        parent = self._resolve_path(parent_path)
        if parent is None:
            return False, f"touch: cannot create '{path}': No such file or directory"
        if not parent.is_dir:
            return False, f"touch: cannot create '{path}': Not a directory"
        if name in parent.children:
            parent.children[name].modified = time.time()
            return True, ""
        parent.children[name] = FileEntry(name, is_dir=False, parent=parent, content=content)
        parent.modified = time.time()
        return True, ""

    def read_file(self, path):
        """Read file content."""
        entry = self._resolve_path(path)
        if entry is None:
            return False, "", f"cat: {path}: No such file or directory"
        if entry.is_dir:
            return False, "", f"cat: {path}: Is a directory"
        entry.accessed = time.time()
        return True, entry.content, ""

    def write_file(self, path, content, append=False):
        """Write content to file."""
        parent_path, name = self._resolve_parent(path)
        parent = self._resolve_path(parent_path)
        if parent is None:
            return False, f"cannot write to '{path}': No such file or directory"
        if name in parent.children:
            entry = parent.children[name]
            if entry.is_dir:
                return False, f"cannot write to '{path}': Is a directory"
            if append:
                entry.content += content
            else:
                entry.content = content
            entry.modified = time.time()
        else:
            parent.children[name] = FileEntry(name, is_dir=False, parent=parent, content=content)
            parent.modified = time.time()
        return True, ""

    def rm(self, path, recursive=False):
        """Remove a file or directory."""
        entry = self._resolve_path(path)
        if entry is None:
            return False, f"rm: cannot remove '{path}': No such file or directory"
        if entry.is_dir and entry.children and not recursive:
            return False, f"rm: cannot remove '{path}': Is a directory"
        if entry.parent is None:
            return False, "rm: cannot remove root directory"
        parent = entry.parent
        del parent.children[entry.name]
        parent.modified = time.time()
        return True, ""

    def cp(self, src_path, dest_path, recursive=False):
        """Copy file or directory."""
        src = self._resolve_path(src_path)
        if src is None:
            return False, f"cp: cannot stat '{src_path}': No such file or directory"
        if src.is_dir and not recursive:
            return False, f"cp: -r not specified; omitting directory '{src_path}'"
        dest = self._resolve_path(dest_path)
        if dest and dest.is_dir:
            dest_path = dest_path.rstrip("/") + "/" + src.name
        parent_path, name = self._resolve_parent(dest_path)
        parent = self._resolve_path(parent_path)
        if parent is None:
            return False, f"cp: cannot create '{dest_path}': No such file or directory"
        self._copy_tree(src, parent, name)
        return True, ""

    def _copy_tree(self, src, dest_parent, name):
        """Recursively copy a tree."""
        if src.is_dir:
            new_dir = FileEntry(name, is_dir=True, parent=dest_parent)
            for child in src.children.values():
                self._copy_tree(child, new_dir, child.name)
            dest_parent.children[name] = new_dir
        else:
            dest_parent.children[name] = FileEntry(name, is_dir=False, parent=dest_parent, content=src.content)

    def mv(self, src_path, dest_path):
        """Move/rename file or directory."""
        src = self._resolve_path(src_path)
        if src is None:
            return False, f"mv: cannot stat '{src_path}': No such file or directory"
        dest = self._resolve_path(dest_path)
        if dest and dest.is_dir:
            dest_path = dest_path.rstrip("/") + "/" + src.name
        parent_path, name = self._resolve_parent(dest_path)
        parent = self._resolve_path(parent_path)
        if parent is None:
            return False, f"mv: cannot move to '{dest_path}': No such file or directory"
        src.parent.children.pop(src.name)
        src.name = name
        src.parent = parent
        parent.children[name] = src
        parent.modified = time.time()
        return True, ""

    def find(self, path, name=None, type_=None):
        """Find files/directories."""
        entry = self._resolve_path(path)
        if entry is None:
            return False, [], f"find: '{path}': No such file or directory"
        results = []
        self._search(entry, entry.path, name, type_, results)
        return True, results, ""

    def _search(self, node, base_path, name_filter, type_filter, results):
        current_path = base_path.rstrip("/") + "/" + node.name if base_path != "/" else "/" + node.name
        if node.name == "" and base_path == "/":
            current_path = "/"
        if name_filter and node.name != name_filter and name_filter not in node.name:
            pass
        elif type_filter == "d" and not node.is_dir:
            pass
        elif type_filter == "f" and node.is_dir:
            pass
        else:
            results.append(current_path)
        if node.is_dir and node.children:
            for child in node.children.values():
                self._search(child, current_path, name_filter, type_filter, results)

    def tree(self, path, prefix="", is_last=True):
        """Generate tree view."""
        entry = self._resolve_path(path)
        if entry is None:
            return False, [], f"tree: '{path}': No such file or directory"
        lines = [prefix + ("└── " if is_last else "├── ") + (entry.name or "/")]
        if entry.is_dir and entry.children:
            children = sorted(entry.children.values(), key=lambda x: (not x.is_dir, x.name))
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                extension = "    " if is_last_child else "│   "
                lines.append(prefix + extension + ("└── " if is_last_child else "├── ") + child.name)
                if child.is_dir and child.children:
                    lines.extend(self._tree_recursive(child, prefix + extension, is_last_child))
        return True, lines, ""

    def _tree_recursive(self, node, prefix, is_last):
        lines = []
        if node.is_dir and node.children:
            children = sorted(node.children.values(), key=lambda x: (not x.is_dir, x.name))
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                extension = "    " if is_last_child else "│   "
                lines.append(prefix + extension + ("└── " if is_last_child else "├── ") + child.name)
                if child.is_dir and child.children:
                    lines.extend(self._tree_recursive(child, prefix + extension, is_last_child))
        return lines

    def exists(self, path):
        return self._resolve_path(path) is not None

    def is_dir(self, path):
        entry = self._resolve_path(path)
        return entry.is_dir if entry else False

    def is_file(self, path):
        entry = self._resolve_path(path)
        return entry and not entry.is_dir

    def get_entry(self, path):
        return self._resolve_path(path)

    def get_size(self, path):
        """Get human-readable size."""
        entry = self._resolve_path(path)
        if entry is None:
            return "0"
        size = entry.size
        for unit in ['B', 'K', 'M', 'G']:
            if size < 1024:
                return f"{size}{unit}"
            size /= 1024
        return f"{size:.1f}T"

    def du(self, path):
        """Disk usage."""
        entry = self._resolve_path(path)
        if entry is None:
            return False, [], f"du: '{path}': No such file or directory"
        results = []
        self._du_recursive(entry, results)
        return True, results, ""

    def _du_recursive(self, node, results):
        size = node.size
        path = node.path
        results.append((path, size))
        if node.is_dir and node.children:
            for child in node.children.values():
                self._du_recursive(child, results)
