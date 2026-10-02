"""Bounded USTAR validation before extraction into a new private directory.

Only ordinary files/directories are supported. Package assembly owns omission of
specific optional npm links; receiving an archive never grants a link exception.
"""
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


@dataclass(frozen=True)
class ArchiveLimits:
    transport_bytes: int = 128 * 1024 * 1024
    entries: int = 16384
    expanded_bytes: int = 96 * 1024 * 1024
    path_bytes: int = 240

    def __post_init__(self):
        if any(type(value) is not int or value < 1 for value in vars(self).values()):
            raise ValueError('Archive limits must be positive controller-owned integers')


def unpack_archive(stream, destination, limits=ArchiveLimits()):
    """Validate a bounded binary stream completely, then create destination.

    The caller supervises the stream's lifetime/deadline. No file is extracted
    until all headers, contents and trailer have passed validation. A failed
    attempt never touches a preexisting destination or publishes partial files.
    """
    destination = Path(destination).absolute()
    if os.path.lexists(destination) or any(p.is_symlink() for p in destination.parents):
        raise ValueError('Artifact destination must be new and have no link ancestors')
    destination.parent.mkdir(parents=True, exist_ok=True)
    seen, ancestors, records = {}, set(), []
    transported = expanded = 0
    with tempfile.TemporaryFile(dir=destination.parent) as spool:
        def read(size, *, eof=False):
            nonlocal transported
            data = bytearray()
            while len(data) < size:
                # Read one byte beyond the cap only to detect excess transport.
                chunk = stream.read(min(size - len(data), limits.transport_bytes - transported + 1))
                if not chunk:
                    if eof:
                        break
                    raise ValueError('Truncated environment archive')
                transported += len(chunk)
                if transported > limits.transport_bytes:
                    raise ValueError('Environment archive transport limit exceeded')
                data.extend(chunk)
                spool.write(chunk)
            return bytes(data)

        while True:
            header = read(512)
            if header == bytes(512):
                if read(512) != bytes(512):
                    raise ValueError('Environment archive needs two zero trailer blocks')
                while True:
                    padding = read(4096, eof=True)
                    if any(padding):
                        raise ValueError('Data after environment archive trailer')
                    if not padding:
                        break
                break
            if len(records) >= limits.entries:
                raise ValueError('Environment archive entry limit exceeded')
            if header[257:265] != b'ustar\x0000':
                raise ValueError('Only ordinary USTAR environment archives are supported')
            try:
                member = tarfile.TarInfo.frombuf(header, 'utf-8', 'strict')
            except (tarfile.HeaderError, UnicodeError, ValueError) as error:
                raise ValueError('Invalid environment archive header') from error
            if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
                raise ValueError('Environment archive links, extensions and special files are forbidden')
            directory = member.type == tarfile.DIRTYPE
            name = member.name.rstrip('/') if directory else member.name
            path = PurePosixPath(name)
            if (not name or path.is_absolute() or '..' in path.parts or
                    str(path) != name or '\\' in name or
                    len(name.encode()) > limits.path_bytes):
                raise ValueError('Noncanonical environment archive path')
            if name in seen:
                raise ValueError('Duplicate environment archive path')
            parents = [str(parent) for parent in path.parents if str(parent) != '.']
            if any(seen.get(parent) == 'file' for parent in parents) or (not directory and name in ancestors):
                raise ValueError('Environment archive file/ancestor conflict')
            if member.size < 0 or (directory and member.size):
                raise ValueError('Invalid environment archive entry size')
            expanded += member.size
            if expanded > limits.expanded_bytes:
                raise ValueError('Environment archive expanded-byte limit exceeded')
            seen[name] = 'directory' if directory else 'file'
            ancestors.update(parents)
            records.append((name, directory, spool.tell(), member.size, bool(member.mode & 0o111)))
            remaining = member.size
            while remaining:
                chunk = read(min(65536, remaining))
                remaining -= len(chunk)
            padding = (-member.size) % 512
            if padding and any(read(padding)):
                raise ValueError('Nonzero environment archive entry padding')

        # The whole stream is now validated. All paths below are fresh, with no
        # links or untrusted writers between this validation and extraction.
        destination.mkdir(mode=0o700)
        try:
            for name, directory, offset, size, executable in records:
                target = destination / name
                if directory:
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                spool.seek(offset)
                with target.open('xb') as output:
                    remaining = size
                    while remaining:
                        chunk = spool.read(min(65536, remaining))
                        output.write(chunk)
                        remaining -= len(chunk)
                    output.flush()
                    os.fsync(output.fileno())
                target.chmod(0o555 if executable else 0o444)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return destination
