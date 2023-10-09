import logging
import json as JSON
import math
from pathlib import Path as Pathy

from .. import SYSLOG

print(__name__)

syslog = logging.getLogger(SYSLOG)


class Paths:
    """Central location of all useful paths as path objects"""

    project = Pathy(__file__).absolute().parent.parent
    "Where bot should be"
    syslog.debug("Folder: project=%s", project)
    work = project.parent
    "Should be top level folder"
    syslog.debug("Folder: work=%s", work)
    exts = project.joinpath("extensions")
    exts.mkdir(exist_ok=True)
    logs = project.joinpath("logs")
    logs.mkdir(exist_ok=True)
    data = project.joinpath("data")
    data.mkdir(exist_ok=True)
    util = project.joinpath("util")
    util.mkdir(exist_ok=True)
    dump = work.joinpath("dump")

    file_bot = project.joinpath("bot.py")
    file_cache_json = dump.joinpath("cache.json")


class Read_Write:
    """For your reading and writing needs"""

    cache_json = {}

    @classmethod
    def check_ext(cls, filename: Pathy | str, ext: str) -> Pathy:
        """Check if the filename has extension, adds if not"""
        if isinstance(filename, str):
            syslog.warning("File was not Pathy object: %s", filename)
            filename = Pathy(filename)

        filename = filename.with_suffix(ext).absolute()
        return filename

    @classmethod
    def write_json(cls, data: dict, file: Pathy, sort=False) -> bool:
        """Create a JSON file containing data."""
        syslog.debug("write file=%s", file)

        file = cls.check_ext(filename=file, ext=".json")

        if not isinstance(data, dict):
            raise TypeError

        if file.exists():
            syslog.debug("Exists: file=%s", file)

        file.parent.mkdir(exist_ok=True, parents=True)

        mode = "w"

        with open(file, mode, encoding="UTF-8") as f:
            try:
                JSON.dump(
                    obj=data,
                    fp=f,
                    indent=4,
                    separators=(", ", ": "),
                    sort_keys=sort,
                )
            except Exception:
                syslog.exception("write_json")
                return False
            return True

    @classmethod
    def write_cache(cls) -> bool:
        """Dump the current cache_json to file"""
        syslog.warning("Dumping cache_json")
        return cls.write_json(data=cls.cache_json, file=Paths.file_cache_json)

    @classmethod
    def _read(cls, fp: Pathy) -> dict | bool:
        """Read file as JSON"""
        try:
            with open(fp, "r") as f:
                return JSON.load(f)
        except Exception:
            syslog.exception("_read")
            return False

    @classmethod
    def _cache_add(cls, file_rel: Pathy, mod_time: int, data: dict):
        """Add data to cache"""
        meta = {"mod_time": mod_time, "content": data}
        cls.cache_json[file_rel] = meta

    @classmethod
    def _cache_check(cls, file: Pathy, mod_time: int):
        """Check if file in cache, return data if so"""
        new_mod_time = int(file.stat().st_mtime)
        file_relative = file.absolute().relative_to(Paths.work)
        if file_relative in cls.cache_json:
            old_mod_time = cls.cache_json[file_relative]["mod_time"]
            if old_mod_time == new_mod_time:
                return cls.cache_json[file_relative]["content"]
        return False

    @classmethod
    def read_json(
        cls, file: Pathy, cache: bool = True, create: bool = False
    ) -> dict | bool:
        """Read JSON file."""
        syslog.debug("read file=%s", file)

        file = cls.check_ext(filename=file)

        file_relative = file.absolute().relative_to(Paths.work)
        if not file.exists():
            syslog.warning("File not Found %s", file_relative)
            if create:
                syslog.warning("Creating")
                Read_Write.write_json(data={}, file=file)
            else:
                return False

        if not cache:
            return cls._read(fp=file)

        new_mod_time = int(file.stat().st_mtime)
        if data := cls._cache_check(file=file_relative, mod_time=new_mod_time):
            pass
        else:
            data = cls._read(fp=file)
            cls._cache_add(file_rel=file_relative, mod_time=new_mod_time, data=data)
        return data

    @classmethod
    def write_txt(cls, data: str, file: Pathy, mode: str = "w"):
        """Create a TXT file containing data."""
        syslog.debug("write file=%s", file)

        file = cls.check_ext(filename=file, ext=".txt")

        if not isinstance(data, str):
            raise TypeError

        if file.exists():
            syslog.debug("Exists: file=%s", file)

        file.parent.mkdir(exist_ok=True, parents=True)

        with open(file, mode, encoding="UTF-8") as f:
            try:
                f.write(data)
            except Exception:
                syslog.exception("write_txt")
                return False
            return True


def bytes_magnitude(byte_num: int, magnitude: str, bi: bool) -> float:
    """Turns an int into a more friendly magnitude
    magnitude=['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']"""
    if bi:
        bi = 1024
    else:
        bi = 1000
    ratios = {"K": 1, "M": 2, "G": 3, "T": 4, "P": 5, "E": 6, "Z": 7, "Y": 8}
    try:
        return round(byte_num / math.pow(bi, ratios[magnitude.upper()]), 3)
    except Exception:
        # syslog.exception("BytesMag")
        return False


def bytes_auto(byte_num: int | str) -> str:
    """Determine the magnitude for a given number of bytes"""
    print(byte_num)
    x = int(len(str(byte_num)))
    if x <= 3:
        return ""
    elif x <= 6:
        return "K"
    elif x <= 9:
        return "M"
    elif x <= 12:
        return "G"
    elif x <= 15:
        return "T"
    elif x <= 18:
        return "P"
    elif x <= 21:
        return "E"
    elif x <= 24:
        return "Z"
    else:
        return "Y"


def bytes_to_human(
    byte_num: int, magnitude: str = "AUTO", bi: bool = True, bit: bool = False
) -> str:
    """Turns an int into a friendly notation, eg 2.5MiB.
    magnitude= ['AUTO', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'].
    bi= power of 10 or power of 2"""
    if not isinstance(byte_num, int):
        try:
            byte_num = int(byte_num)
        except Exception:
            # syslog.exception("Not convertable to int")
            return False

    if byte_num <= 1024:
        return f"{byte_num}{'b' if bit else 'B'}"

    magnitude = magnitude.upper()
    nota = ["AUTO", "K", "M", "G", "T", "P", "E", "Z", "Y"]

    if magnitude == "AUTO":
        magnitude = bytes_auto(byte_num=byte_num)
    elif magnitude not in nota:
        # syslog.error("BytesHuman, Not MAG")
        return False

    size = bytes_magnitude(byte_num=byte_num, magnitude=magnitude, bi=bi)
    return f"{size}{magnitude}{'i' if bi else ''}{'b' if bit else 'B'}"


# MIT APasz
