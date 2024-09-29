import hashlib
from pathlib import Path

def hash_file(path, algorithm='sha256'):
    path = Path(path)
    assert path.is_file()
    hash_object = hashlib.new(algorithm)
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            hash_object.update(chunk)
    return hash_object.hexdigest()

