from modules.report.all import Report
from monitorizer.core.main import Monitorizer
from modules.server.utils import reload_watchlist
from monitorizer.ui.cli import Console
from modules.nuclei_fuzzing.templates import *
from datetime import datetime
from colorama import Fore
import threading, subprocess, glob, os, time

class NucleiFuzzing(Report, Monitorizer, Console):
    def __init__(self):
        super().__init__()

    def same(self, line1, line2):
        return line1.split("] ", 1)[-1] == line2.split("] ", 1)[-1] if line1 and line2 and ']' in line1 and ']' in line2 else False

    def compare(self, old_report, new_report):
        return [line for line in new_report if line.strip() and all(not self.same(old_line, line) for old_line in old_report)]

    def write_to_file(self, filepath, content):
        with open(filepath, 'w') as file:
            file.write(content)

    def scan(self):
        self.log("Started new Nuclei-Fuzzing scanning thread")
        watchlist = reload_watchlist()
        # subdomains = {sub for target in watchlist for sub in self.merge_reports(target)}
        
        report_name = datetime.now().strftime("%Y%m%d_%s")
        self.ensure_dir_exists('output', 'reports')
        combined_waymore_output_for_nuclei_fuzzing = f"output/nuclei_fuzzing_input_{report_name}"
        cmd = f'find output/ -name "*_gau" -exec cat {{}} \; | anew output/nuclei_fuzzing_input_all > {combined_waymore_output_for_nuclei_fuzzing}'
        # run this command using subprocess.Popen()
        subprocess.check_output(cmd, shell=True)
        nuclei_fuzzing_output = f"reports/nuclei_fuzzing_{report_name}"
        #? self.combine_files('output/*_waymore', combined_waymore_output_for_nuclei_fuzzing)
    

        
        #? self.write_to_file(combined_waymore_output_for_nuclei_fuzzing, "\n".join(subdomains))
        

        cmd = f"./thirdparty/nuclei/nuclei -l {combined_waymore_output_for_nuclei_fuzzing} -no-color -silent -t ./modules/nuclei_fuzzing/fuzzing-templates/ -o {nuclei_fuzzing_output} {self.nuclei_fuzzing_options}"
        subprocess.check_output(cmd, shell=True)

        old_report = self.merge_reports("nuclei_fuzzing", exclude=[report_name])
        new_report = self.read_file(nuclei_fuzzing_output)
        result = '\n'.join(self.compare(old_report, new_report))

        if new_report and result.strip():
            self.send_discord_report(report_template.format(scan_result=result))

        self.log("Nuclei-Fuzzing scanning thread finished")

    def ensure_dir_exists(self, *dirs):
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

    def combine_files(self, pattern, output_file):
        with open(output_file, 'w') as outfile:
            for fname in glob.glob(pattern):
                with open(fname) as infile:
                    outfile.write(infile.read())

    def read_file(self, filepath):
        with open(filepath, 'r') as file:
            return file.read().split("\n")
    

    def start_continuous_scanner(self):
        def _continuous():
            while 1:
                self.scan()

                if self.nuclei_fuzzing_interval is None:
                    self.nuclei_fuzzing_interval = 24*60*60

                self.log(f"Nuclei-Fuzzing scanning thread is sleeping for {self.nuclei_fuzzing_interval / 60 / 60} hour(s)")
                time.sleep(self.nuclei_fuzzing_interval)

        if self.nuclei_enable == True:
            self.info(f"Continuous scanner is {Fore.GREEN}Enabled")
            thread = threading.Thread(target=_continuous)
            thread.name = "ScannerThread"
            thread.start()
        else:
            self.info(f"Continuous scanner is {Fore.RED}Disabled")