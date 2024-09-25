from pathlib import Path
import hashlib
from typing import Dict, List

from treesitter import summarize as treesitter_summarize

def codeblock_exists(ts, parts: List[str]):
    if len(parts) == 0:
        return True
    elif parts[0] in ts.children:
        return codeblock_exists(ts.children[parts[0]], parts[1:])
    else:
        return False

def codeblock_index(ts, parts: List[str]):
    if len(parts) == 0:
        return ts
    else:
        return codeblock_index(ts.children[parts[0]], parts[1:])

def is_binary(path:Path, sample_size=1024):
    """
    A heuristic to determine whether a file is binary (and hence should be ignored).
    """
    assert path.is_file()

    if path.stat().st_size < 100:
        #If file is super short, assume it isn't binary.
        return False

    with path.open('rb') as file:
        sample = file.read(sample_size)
    
    # Check for null bytes
    if b'\x00' in sample:
        return True

    # Check if the sample contains mostly printable ASCII characters
    printable_chars = sum(32 <= byte <= 126 for byte in sample)
    return printable_chars / len(sample) < 0.7  # Adjust threshold as needed

def is_valid_text_file(path: Path):
    return path.exists() and path.is_file() and (not is_binary(path))

#maps path to path to treesitter.  Uses a cache based on the file hash.
treesitter_cache = {}
def treesitter_file_summary(path):
    assert is_valid_text_file(path)

    h = hash_file(path)
    if h not in treesitter_cache:
        treesitter_cache[h] = treesitter_summarize(path)
    return treesitter_cache[h]

def hash_file(path, algorithm='sha256'):
    hash_object = hashlib.new(algorithm)
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            hash_object.update(chunk)
    return hash_object.hexdigest()


class FullPath():
    def __init__(self, path, *parts):
        assert isinstance(path, Path)
        assert path.is_absolute()

        self.path = path
        self.parts = parts

    def name(self):
        if 0 < len(self.parts):
            return self.parts[-1]
        else:
            return self.path.name

    def treesitter_summary(self):
        assert self.exists()
        ts = treesitter_file_summary(self.path)
        return codeblock_index(ts, self.parts)

    def exists(self):
        if not self.path.exists():
            #Path doesn't exist
            return False
        elif 0 == len(self.parts):
            #Path exists, and there aren't any parts
            return True
        elif not is_valid_text_file(self.path):
            #Path exists, there are parts, but not a valid text file.  So it can't have any parts.
            return False
        else:
            #Path exists, there are parts, but is a valid text file.
            ts = treesitter_file_summary(self.path)
            return codeblock_exists(ts, self.parts)

    def is_in(self, directory):
        """
        Check if a self is within a specific "directory".
        Deals with parts correctly.
        """
        assert isinstance(directory, FullPath)
        if not self.path.is_relative_to(directory.path):
            return False
        elif len(self.parts) < len(directory.parts):
            #If directory has (strictly) more parts, you can't be in directory.
            return False
        else:
            return all(x == y for (x, y) in zip(directory.parts, self.parts[:len(directory.parts)]))

    def signature(self):
        if len(self.parts) == 0:
            return ""
        else:
            return self.treesitter_summary().signature

    #def is_file(self):
    #    return self.path.is_file() and len(self.parts) == 0

    def is_dir(self):
        return self.path.is_dir() and len(self.parts) == 0

    #def is_file_or_dir(self):
    #    return self.is_file() or self.is_dir()

    def has_no_parts(self):
        return len(self.parts) == 0

    def iterdir(self):
        assert self.is_dir()
        return [FullPath(path) for path in self.path.iterdir()]

    def read_path(self):
        assert is_valid_text_file(self.path)
        with self.path.open() as f:
           return f.read()

    def read(self):
        return self.treesitter_summary().code

    def iterdir_tracked(self):
        """
        Lists directories and non-binary files that aren't hidden (i.e. don't start with a '.').
        """
        assert self.is_dir()

        result = []
        for child_path in self.iterdir():
            if ('.' != child_path.path.name[0]) and is_valid_text_file(child_path.path):
                result.append(child_path)
        return result

    def iter_tracked(self):
        """
        For a directory, lists directories and non-binary files that aren't hidden (i.e. don't start with a '.').
        For a file / code block, lists child code blocks.
        """
        if self.is_dir():
            return self.iterdir_tracked()
        else:
            ts = self.treesitter_summary()
            return [self.append_part(part) for part in ts.children.keys()]

    def getsize(self):
        if self.is_dir():
            return sum(child_path.getsize() for child_path in self.iterdir_tracked())
        else: 
            return len(self.read().encode('utf-8'))

    def __hash__(self):
        return hash((self.path, self.parts))
    
    def __eq__(self, other):
        if isinstance(other, FullPath):
            return (self.path == other.path) and (self.parts == other.parts)
        return False

    def append_path(self, name):
        return FullPath(self.path / name, *self.parts)

    def append_part(self, part):
        return FullPath(self.path, *self.parts, part)

    def listdir(self):
        assert self.is_dir()
        return [x.path.name for x in self.iterdir()]

    def __repr__(self):
        parts = '#'.join(self.parts)
        if 0 < len(self.parts):
            parts = '#' + parts
        return f"FullPath({self.path}{parts})"


def full_path(path):
    """
    Converts a text path, of the form:
    relative/path/to/file#class_name#method_name
    to a FullPath object.

    Shouldn't be used in real code, but useful for testing.
    """
    path, *parts = path.split('#')
    return FullPath(Path(path).resolve(), *parts)
