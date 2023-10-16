"""init mate"""
import dotenv
from pathlib import Path as Pathy
from json import load
import string
import os

print(__name__)

dotenv.load_dotenv()

INDEV = bool(os.getenv("DEV"))
SYSLOG = str(os.getenv("SYSLOG"))
DATE_FORMAT = str(os.getenv("DATE_FORMAT"))

# Better safe under the limit than over
MESS_SIZE = int(os.getenv("MAX_LOG_SIZE_MB")) * 1_000_000 - 5000
"In bytes, maximum size of message files"


changelog_file = "changelog.json"
cwd = Pathy(__file__).parent
found = False


def find_cl(file: Pathy):
    if "changelog" in file.name:
        return file
    else:
        return False


for file in cwd.iterdir():
    if changelog_file := find_cl(file):
        found = True
        break

if not found:
    for file in cwd.parent.iterdir():
        if changelog_file := find_cl(file):
            found = True
            break

major_file = changelog_file.stem

major = ""

for char in major_file:
    if char in string.digits:
        major = char
    else:
        major = "0"

file = Pathy().parent.joinpath(changelog_file)
if file.exists():
    file: dict = load(file.open())
    subver = list(file.keys())[0]
    if len(subver) == 0:
        subver = "0.0"
    else:
        minor, point = subver.split(".", 1)
    __version__ = f"{major}.{minor}.{point}"
    __version_tuple__ = (int(major), int(minor), int(point))
else:
    __version__ = "unknown"
    __version_tuple__ = (0, 0, 0)

print(__version__)


# MIT APasz
