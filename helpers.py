from pathlib import Path as Pathy
import logging
from logging import handlers
import subprocess
import sys
from collections.abc import Iterable

work_dir = Pathy(__file__).parent.absolute()
syslog: logging.Logger = None
"loggering"


class Helper:
    """Functions for initialisation"""

    def setup_syslog():
        """Create system log object"""
        from kiroku import SYSLOG

        syslog_file = work_dir.joinpath("logs", SYSLOG)
        syslog_file.parent.mkdir(exist_ok=True)

        logging.addLevelName(logging.DEBUG, "DBUG")
        global syslog
        syslog = logging.getLogger(SYSLOG)
        syslog.setLevel("DEBUG")

        handle_file = handlers.TimedRotatingFileHandler(
            filename=syslog_file,
            when="W6",
            utc=True,
            encoding="utf-8",
        )
        handle_file.setFormatter(
            logging.Formatter(
                "%(asctime)s|%(created).3f || %(levelname).4s %(module)8s.%(funcName)-20s|| %(message)s",
                "%Y-%m-%d:%H:%M:%S",
            )
        )
        syslog.addHandler(handle_file)

        return syslog

    def check_packages() -> tuple[bool, list]:
        """Check if the packages listed in the requirements file are present"""
        global syslog
        syslog.debug("check_packages")

        # system packages
        packages = subprocess.check_output([sys.executable, "-m", "pip", "list"])
        packages_list = [r.decode().split("==")[0] for r in packages.split()]

        # check if file present
        reqs_file = work_dir.joinpath("requirements.txt")
        if not reqs_file.exists():
            return (False, {})

        # check if modules exist
        ok = True
        satisfied = []
        req_list = reqs_file.read_text().splitlines()
        friendly = {True: "Good", False: "Fail"}
        for req in req_list:
            req = req.split("[")[0]
            for char in ("<=", ">=", "~=", "=="):
                if char in req:
                    req = req.split(char)[0]
            present = req in packages_list
            satisfied.append(f"{friendly[present]} == {req}")
            if not present:
                ok = False
                syslog.error("%s; %s", req, present)

        syslog.info("%s Packages, %s", len(satisfied), friendly[ok])
        return (ok, satisfied.sort())

    def write_txt(data: str | Iterable, file: Pathy) -> bool:
        """Write simple text file containing data"""
        global syslog
        syslog.debug("write_txt")

        if isinstance(data, Iterable):
            data = "\n".join(data)

        try:
            with open(file=file, mode="w", encoding="UTF-8") as f:
                f.write(data)
        except Exception:
            syslog.exception("Write txt file")
