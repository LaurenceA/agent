from pathlib import Path

from treesitter import summarize as treesitter_summarize

def codeblock_exists(ts, parts):
    if len(parts) == 0:
        return True
    elif parts[0] in ts.children:
        return codeblock_exists(ts.children[parts[0]], parts[1:])
    else:
        return False

def codeblock_index(ts, parts):
    if len(parts) == 0:
        return ts
    else:
        return codeblock_index(ts.children[parts[0]], parts[1:])

class FullPath():
    def __init__(self, path, *parts):
        assert isinstance(path, Path)
        assert path.is_absolute()

        self.path = path
        self.parts = parts

    def binary(self, sample_size=1024):
        """
        A heuristic to determine whether a file is binary (and hence should be ignored).
        """
        assert self.path.is_file()

        with self.path.open('rb') as file:
            sample = file.read(sample_size)
        
        # Check for null bytes
        if b'\x00' in sample:
            return True

        # Check if the sample contains mostly printable ASCII characters
        printable_chars = sum(32 <= byte <= 126 for byte in sample)
        return printable_chars / len(sample) < 0.7  # Adjust threshold as needed

    def treesitter_summary(self):
        assert self.path.is_file()
        assert not self.binary()
        return treesitter_summarize(self.path)

    def exists(self):
        if not self.path.exists():
            #Path doesn't exist
            return False
        elif 0 == len(self.parts):
            #Path exists, and there aren't any parts
            return True
        elif self.binary() or self.path.is_dir():
            #Path exists, refers to a binary file or directory, and there are parts.
            return False
        else:
            ts = self.treesitter_summary()
            return codeblock_exists(ts, self.parts)

    def is_filedir(self):
        return not self.is_codeblock()

    def is_codeblock(self):
        return 0 < len(parts)

    def read_path(self):
        with self.path.open() as f:
           return f.read()

    def read(self):
        assert self.exists()
        assert self.path.is_file()
        assert not self.binary()

        ts = self.treesitter_summary()
        return codeblock_index(ts, self.parts)

    def __hash__(self):
        return hash((self.path, self.parts))
    
    def __eq__(self, other):
        if isinstance(other, FullPath):
            return (self.path == other.path) and (self.parts == other.parts)
        return False

    def append_path(self, name):
        return FullPath(path / name, *self.parts)

    def append_part(self, name):
        return FullPath(path, *self.parts, part)


def full_path(path):
    """
    Converts a text path, of the form:
    relative/path/to/file#class_name#method_name
    to a FullPath object.

    Shouldn't be used in real code, but useful for testing.
    """
    path, *parts = path.split('#')
    return FullPath(Path(path).resolve(), *parts)
