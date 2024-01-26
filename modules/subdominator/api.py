import contextlib
from modules.report.all import Report
from monitorizer.core.main import Monitorizer
from modules.server.utils import reload_watchlist
from monitorizer.ui.cli import Console
from modules.subdominator.templates import *
from datetime import datetime
from colorama import Fore
import threading

import subprocess
import needle
import requests
import os
import time



class Subdominator(Report, Monitorizer, Console):
    def __init__(self):
        super().__init__()
    
    def resolve(self, host):
        try:
            return self._extracted_from_resolve_3('https://', host)
        except Exception:
            with contextlib.suppress(Exception):
                return self._extracted_from_resolve_3('http://', host)
        return None

    # TODO Rename this here and in `resolve`
    def _extracted_from_resolve_3(self, arg0, host):
        url = f"{arg0}{host}"
        requests.get(url, verify=False, timeout=30)
        return url

    def same(self, line1, line2):
        if line1 == '' or line2 == '':
            return False

        if ']' not in line1 or ']' not in line2:
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
        self.log("Started new subdominator scanning thread")

        watchlist  = reload_watchlist()
        subdomains = []

        for target in watchlist:
            subdomains += list( self.merge_reports(target) )

        report_name   = str(datetime.now().strftime("%Y%m%d_%s"))
        # Ensure the output directory exists
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        reports_dir = 'reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        subdominator_input = f"output/subdominator_input_{report_name}"
        subdominator_output = f"reports/subdominator_{report_name}"

        resolved_subs = set([])

        for cp in needle.GroupWorkers(kernel='threadpoolexecutor', target=self.resolve, arguments=[[sub] for sub in subdomains], concurrent=50):
            if cp._return is None or cp._return == "RUNTIME_ERROR":
                continue
            resolved_subs.add(cp._return)

        open(subdominator_input, 'w').write("\n".join(resolved_subs))


        cmd = f"./thirdparty/subdominator/subdominator -l {subdominator_input} -o {subdominator_output} {self.subdominator_options}"
        subprocess.check_output(cmd, shell=True)


        old_report = self.merge_reports("subdominator", exclude=[report_name])
        new_report = []
        result     = None
        
        if os.path.isfile(subdominator_output):
            new_report = open(subdominator_output, 'r').read().split("\n")
            result     = '\n'.join( self.compare(old_report, new_report) )

        if new_report and result.strip():
            self.send_discord_report(report_template.format(scan_result=result))

        self.log("subdominator scanning thread finished")
    

    def start_continuous_scanner(self):
        def _continuous():
            while 1:
                self.scan()

                if self.subdominator_interval is None:
                    self.subdominator_interval = 24*60*60

                self.log(f"Subdominator scanning thread is sleeping for {self.subdominator_interval / 60 / 60} hour(s)")
                time.sleep(self.subdominator_interval)

        if self.subdominator_enable == True:
            self.info(f"Continuous scanner is {Fore.GREEN}Enabled")
            thread = threading.Thread(target=_continuous)
            thread.name = "ScannerThread"
            thread.start()
        else:
            self.info(f"Continuous scanner is {Fore.RED}Disabled")