import os
from helpers import Helper, work_dir

PID = os.getpid()
print("main", PID)


def main():
    """Set things up and start the bot"""
    print(f"\n*** Starting *** {PID=}")

    syslog = Helper.setup_syslog()
    ok, satisfied = Helper.check_packages()

    # check if any packages are missing, if so write out which
    if not ok:
        problem = work_dir.joinpath("problem_packages.txt")
        Helper.write_txt(data=satisfied, file=problem)

    # uvloop only works on UNIX-like
    if os.name != "nt":
        syslog.info("Linux Host, installing uvloop")
        import uvloop

        uvloop.install()

    # import and run the bot
    def run_bot():
        """Actually run the bot"""
        from kiroku.bot import KBot

        bot = KBot()

        syslog.info("KBot Engage!")
        return bot.run()

    run_bot()
    syslog.info("*** Terminated ***")


if __name__ == "__main__":
    main()

# MIT APasz
