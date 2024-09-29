import re
import os
import hashlib
from pathlib import Path
from typing import Dict, List

from treesitter import treesitter_ast, TreeSitterAST

"""
Valid Path must exist, and we must have read access.
They can be directories or UTF-8 encoded text files.

A valid FullPath is the same, but it could also be a part of a UTF-8 encoded text file.
"""

def exists_accessible(path: Path):
    assert isinstance(path, Path)
    return os.access(path, os.R_OK) and path.exists()

def is_valid_code(path: Path):
    assert isinstance(path, Path)
    return exists_accessible(path) and path.is_file() and is_utf8(path)

def is_valid_dir(path: Path):
    assert isinstance(path, Path)
    return exists_accessible(path) and path.is_dir()

def is_valid_path(path: Path):
    assert isinstance(path, Path)
    return is_valid_dir(path) or is_valid_code(path)

def iterdir_all(path):
    assert is_valid_dir(path)
    return [*path.iterdir()]

def iterdir_valid(path: Path):
    """
    Lists all directories and non-binary files that are valid.
    """
    assert is_valid_dir(path)
    return [p for p in iterdir_all(path) if is_valid_path(p)]

def iterdir_tracked(path: Path):
    """
    Lists all directories and non-binary files that are tracked (i.e. valid, and non hidden (i.e. with a . at the start).
    """
    assert is_valid_dir(path)
    return [p for p in iterdir_valid(path) if tracked(path.name)]

def tracked(filename):
    excluded_patterns = [r'^\.', r'^\.']
    for pattern in excluded_patterns:
        if re.search(pattern, filename):
            return False
    return True

"""
There are several slow operations, including doing a treesitter parse
of a file, and checking whether it is binary.  We cache these, using
the file path, modification time and size as a key.
"""

def file_key(path):
    return (str(path), path.stat().st_mtime, path.stat().st_size)



#### Cache doing the treesitter parsing.
treesitter_cache = {}
def treesitter_file_ast(path):
    assert is_valid_code(path)

    key = file_key(path)
    if key not in treesitter_cache:
        treesitter_cache[key] = treesitter_ast(path)
    return treesitter_cache[key]


#### Cache doing the binary vs not binary judgement, as that requires reading whole file.
def _is_utf8(path:Path):
    #Checks for a UTF-8 BOM in the first 3 chars
    with path.open('rb') as file:
        if file.read(3) == b'\xef\xbb\xbf':
            return True

    #Else, get a sample of 1024 bytes from the file.
    with path.open('rb') as file:
        sample = file.read(1024)

    # Check for null bytes, which don't appear in utf-8
    if b'\x00' in sample:
        return False

    # For a utf-8 file, either bytes sequence of 1001, 1002, 1003 or 1004 must be decodable
    # as utf-8 has sequences up to 4 bytes long
    sample_decodable = False
    for offset in range(4):
        try:
            sample[:(len(sample)-offset)].decode('utf-8')
            sample_decodable = True
            break
        except UnicodeDecodeError:
            pass

    #Try decoding full file.
    with path.open('rb') as file:
        full_file = file.read()

    try:
        sample.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

cache_is_utf8 = {}
def is_utf8(path):
    assert exists_accessible(path) and path.is_file()

    key = file_key(path)
    if key not in treesitter_cache:
        cache_is_utf8[key] = _is_utf8(path)
    return cache_is_utf8[key]



class FullPath():
    def __init__(self, path, *parts):
        assert isinstance(path, Path)
        assert path.is_absolute()

        self.path = path
        self.parts = parts

    def is_valid_dir(self):
        return is_valid_dir(self.path) and (len(self.parts) == 0)

    def is_valid_code(self):
        if not is_valid_code(self.path):
            #Not a valid code file.
            return False
        elif len(self.parts) == 0:
            #We are in a valid code file, and there are no parts
            return True
        else:
            #We are in a valid code file, and there are parts
            ts = treesitter_file_ast(self.path)
            return codeblock_exists(ts, self.parts)

    def is_valid(self):
        return self.is_valid_code() or self.is_valid_dir()

    def name(self):
        if 0 < len(self.parts):
            return self.parts[-1]
        else:
            return self.path.name

    def treesitter_ast(self):
        return treesitter_file_ast(self.path).index(self.parts)

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
            return self.treesitter_ast().signature

    def read_path(self):
        assert is_valid_code(self.path)
        with self.path.open() as f:
           return f.read()

    def read(self):
        return self.treesitter_ast().code

    def iter_tracked(self):
        """
        For a directory, lists directories and non-binary files that aren't hidden (i.e. don't start with a '.').
        For a file / code block, lists child code blocks.
        """
        assert self.is_valid()
        if self.is_valid_dir():
            return [FullPath(p) for p in iterdir_tracked(self.path)]
        else:
            ts = self.treesitter_ast()
            return [self.append_part(part) for part in ts.children.keys()]

    def getsize(self):
        assert self.is_valid()

        if self.is_valid_dir():
            return sum(FullPath(p).getsize() for p in iterdir_tracked(self.path))
        else: 
            return len(self.read())

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

    def listdir_all(self) -> List[str]:
        assert self.is_valid_dir()
        return [p.name for p in iterdir_all(self.path)]

    def __str__(self):
        parts = '#'.join(self.parts)
        if 0 < len(self.parts):
            parts = '#' + parts
        return f"{self.path}{parts}"

    def __repr__(self):
        return f"FullPath({self.__str__()})"


def full_path(path):
    """
    Converts a text path, of the form:
    relative/path/to/file#class_name#method_name
    to a FullPath object.

    Shouldn't be used in real code, but useful for testing.
    """
    path, *parts = path.split('#')
    return FullPath(Path(path).resolve(), *parts)
