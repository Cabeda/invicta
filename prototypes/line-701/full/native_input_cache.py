"""Share immutable, byte-identical native networks without changing run paths."""
import os
import errno
from pathlib import Path
from prepare import digest


def intern_network(path, pool=None):
    path = Path(path)
    pool = Path(pool) if pool is not None else Path(__file__).resolve().parents[3] / '.cache/native-input-pool'
    pool.mkdir(parents=True, exist_ok=True)
    signature = digest(path)
    stored = pool / (signature + '.net.xml')
    try:
        os.link(path, stored)
    except FileExistsError:
        if digest(stored) != signature:
            raise ValueError('Content-addressed native network cache is corrupted')
    except OSError as error:
        if error.errno in {errno.EXDEV, errno.EPERM, errno.EACCES, errno.EROFS, errno.ENOTSUP}:
            return signature  # Storage optimisation must not change execution availability.
        raise
    stored.chmod(0o444)
    if not os.path.samefile(path, stored):
        temporary = path.with_name(path.name + '.link.tmp')
        try:
            os.link(stored, temporary)
            os.replace(temporary, path)
        except OSError as error:
            if error.errno not in {errno.EXDEV, errno.EPERM, errno.EACCES, errno.EROFS, errno.ENOTSUP}:
                raise
        finally:
            temporary.unlink(missing_ok=True)
    return signature
