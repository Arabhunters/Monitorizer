from monitorizer.core.main import Monitorizer
from monitorizer.ui.arguments import args
from monitorizer.core import flags
from modules.event.on import Events
from modules.nuclei.api import Nuclei
from modules.nuclei_fuzzing.api import NucleiFuzzing
from modules.subdominator.api import Subdominator
from modules.fuzzing.api import Fuzzing
import os
import subprocess
import signal
from datetime import datetime
from time import sleep


scanners = (
    "subfinder",
    "puredns"
)
monitorizer = Monitorizer()
signal.signal(signal.SIGINT, monitorizer.on_kill)

if not args.debug:
    monitorizer.clear()

monitorizer.banner()
events = Events()
nuclei = Nuclei()
nuclei_fuzzing = NucleiFuzzing()
fuzzing = Fuzzing()
subdominator = Subdominator()
os.makedirs("./config", exist_ok=True)
os.makedirs("./config/thirdparty", exist_ok=True)
# subprocess.Popen("python3 ./install.py",shell=False)
subprocess.run(["python3", "./install.py"], check=True)
subprocess.run(["git", "submodule", "update", "--init", "--recursive"], check=True)

if os.path.isfile(args.watch):
    with open(args.watch, "r") as f:
        _watch_list = {t.strip() for t in f.readlines()}
    monitorizer.log(f"reading targets from file: {args.watch}")
else:
    _watch_list = set()
    monitorizer.error(f"unable to read {args.watch} is the file on the disk?")
    monitorizer.exit()

monitorizer.set_config(args.config)
monitorizer.initialize()
monitorizer.self_check(scanners)
nuclei.start_continuous_scanner()
# nuclei_fuzzing.start_continuous_scanner()
subdominator.start_continuous_scanner()
fuzzing.start_continuous_scanner()
events.start_monitor()
def pull_updates():
    os.system('cd ./thirdparty/Fresh-Resolvers/ && git pull >/dev/null 2>&1')

def continuous_scan():
    while True:
        pull_updates()
        for target in _watch_list:
            if not target:
                continue

            flags.status = "running"
            flags.current_target = target
            report_name = datetime.now().strftime("%Y%m%d_%s")
            flags.report_name = report_name
            monitorizer.log(f"Created new report target={target} name={report_name}")

            events.scan_start(target)
            current_scan = monitorizer.mutliscan(scanners, target)
            events.scan_finish(target)
            monitorizer.generate_report(target, current_scan, report_name)

            new_domains = monitorizer.merge_scans(current_scan)
            old_domains = monitorizer.merge_reports(target, exclude=[report_name])

            new_domains.difference_update(old_domains)
            if new_domains_filtered := {
                domain: [
                    tool
                    for tool, subs in current_scan.items()
                    if domain in subs
                ]
                for domain in new_domains
                if domain
            }:
                events.discover(new_domains_filtered, report_name)

        flags.status = "idle"
        monitorizer.info(f"All targets scanned, sleeping for {flags.sleep_time} hour(s)")
        sleep(60 * 60 * flags.sleep_time)

if __name__ == "__main__":
    try:
        continuous_scan()
    except KeyboardInterrupt:
        Monitorizer.on_kill()