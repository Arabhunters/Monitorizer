from modules.report.all import Report
from monitorizer.core.main import Monitorizer
from modules.server.utils import reload_watchlist
from monitorizer.ui.cli import Console
from modules.fuzzing.templates import *
from datetime import datetime
from colorama import Fore
import threading
import concurrent.futures
import subprocess
import requests
import os
import time

class Fuzzing(Report, Monitorizer, Console):
    def __init__(self):
        super().__init__()

    def resolve(self, host):
        for scheme in ['https', 'http']:
            try:
                url = f"{scheme}://{host}"
                requests.get(url, verify=False, timeout=30)
                return url
            except requests.RequestException:
                continue
        return None

    def same(self, line1, line2):
        if "]" not in line1 or "]" not in line2:
            return False

        line1 = line1.split("] ", 1)[1]
        line2 = line2.split("] ", 1)[1]

        return line1 == line2

    def compare(self, old_report, new_report):
        new = []
        for new_line in new_report:
            for old_line in old_report:
                if self.same(old_line, new_line):
                    break
            else:
                if new_line.strip():
                    new.append(new_line)
        return new

    def scan(self):
        self.log("started new dirsearch scanning thread")

        watchlist = reload_watchlist()
        subdomains = [sub for target in watchlist for sub in self.merge_reports(target)]
        output_dir = 'output'
        reports_dir = 'reports'
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        report_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        dirsearch_input = f"{output_dir}/dirsearch_input_{report_name}.txt"
        dirsearch_output = f"{reports_dir}/dirsearch_output_{report_name}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            resolved_subs = {executor.submit(self.resolve, sub).result() for sub in subdomains}
            resolved_subs.discard(None)

        with open(dirsearch_input, 'w') as f:
            f.writelines(f"{url}\n" for url in resolved_subs if url)

        dirsearch_command = f"./thirdparty/dirsearch/dirsearch.py -l {dirsearch_input} -o {dirsearch_output} {self.dirsearch_options}"
        if os.path.getsize(dirsearch_input) > 0:
            subprocess.run(dirsearch_command, shell=True, check=True)
        else:
            self.log("dirsearch_input file is empty, skipping dirsearch command execution")
        # Read the content of the dirsearch output file
        if os.path.isfile(dirsearch_output):
            with open(dirsearch_output, 'r') as f:
                dirsearch_content = f.read()

            if dirsearch_content.strip():
                # Send the results to Discord
                self.send_discord_report(report_template.format(scan_result=dirsearch_content))
        old_report = self.merge_reports("dirsearch", exclude=[report_name])
        new_report = []
        result     = None
        
        if os.path.isfile(dirsearch_output):
            new_report = open(dirsearch_output, 'r').read().split("\n")
            result     = '\n'.join( self.compare(old_report, new_report) )

        if new_report and result.strip():
            self.send_discord_report(report_template.format(scan_result=result))
        self.log("Dirsearch scanning thread finished")

    def start_continuous_scanner(self):
        def _continuous():
            while True:
                self.scan()

                if self.dirsearch_interval is None:
                    self.dirsearch_interval = 24 * 60 * 60

                self.log(
                    f"Fuzzing Dirsearch - Scanning thread is sleeping for {self.dirsearch_interval / 60 / 60} hour(s)")
                time.sleep(self.dirsearch_interval)

        if self.dirsearch_enable:
            self.info(f"Fuzzing Dirsearch - Continuous scanner is {Fore.GREEN}Enabled")
            thread = threading.Thread(target=_continuous)
            thread.name = "ScannerThread"
            thread.start()
        else:
            self.info(f"Fuzzing Dirsearch - Continuous scanner is {Fore.RED}Disabled")