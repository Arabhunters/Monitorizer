from monitorizer.ui.cli import Console
from modules.resolvers.dns import DNS
from modules.report.all import Report
from modules.portscan.scanner import masscan
import concurrent.futures
from monitorizer.core import flags
from modules.server import bot
import time
from threading import Thread

class Events(Report, Console, DNS):
    def exit(self):
        pass

    def scan_start(self, target):
        self.timeings = {target: time.monotonic()}
        self.info(f"Started full scan on {target}")


    def scan_finish(self,target):
        scan_time = round((time.monotonic() - self.timeings[target]) / 60, 3)
        self.info(f"Finished scanning {target}, full scan took: {scan_time} minute(s)")

    def start_monitor(self):
        # await bot.bot.start(self.discord_token) #! IDLE problem
        Thread(target=bot.bot.run, args=(self.discord_token,)).start() # start commands bot   
        Thread(target=self.start_reporter_thread, args=()).start() # start reporter bot   
        self.info("Commands Bot & reporter bot Started")

    def discover(self, new_domains, report_name):
        new_domains_filtered = {
            domain: foundby
            for domain, foundby in new_domains.items()
            if not self.nxdomain(domain) or domain.strip() == ''
        }

        if not new_domains_filtered:
            return

        msg = f"MonitorXYZ Report ::: {report_name}\n```\n"

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            future_to_domain = {
                executor.submit(
                    self.perform_scans, domain, new_domains_filtered[domain]
                ): domain
                for domain in new_domains_filtered
            }

            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    scan_result = future.result()
                    msg += scan_result + "\n"
                except Exception as exc:
                    print(f'{domain} generated an exception: {exc}')

        msg += "```"
        self.send_discord_report(msg)

    def perform_scans(self, domain, foundby):
        if flags.acunetix:
            self.acunetix(domain)

        ports = masscan(domain)  # Assuming masscan returns a string of ports
        ports_count = len(ports.split(','))  # Count the ports

        if ports_count > 10:
            return f"{domain} by: {', '.join(foundby)} - [Annoying - maybe WAF]"
        else:
            return f"{domain} by: {', '.join(foundby)} ports: {ports}"