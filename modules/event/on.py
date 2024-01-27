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
        self.info(f"Commands Bot & reporter bot Started")

    def discover(self, new_domains, report_name):

        new_domains_filtered = {
            domain: foundby
            for domain, foundby in new_domains.items()
            if not self.nxdomain(domain) or domain.strip() == ''
        }

        if not new_domains_filtered:
            return

        msg = f"MonitorXYZ Report ::: {report_name}\n"

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_domain = {
                executor.submit(self.masscan_and_report, domain, foundby): domain 
                for domain, foundby in new_domains_filtered.items()
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_domain):
                try:
                    results.append(future.result())
                except Exception as exc:
                    print(f'{future_to_domain[future]} generated an exception: {exc}')

            msg += '```\n' + '\n'.join(results) + '\n```'
            self.send_discord_report(msg)
    def discover(self, new_domains, report_name):
        new_domains_filtered = {
            domain: foundby
            for domain, foundby in new_domains.items()
            if not self.nxdomain(domain) or domain.strip() == ''
        }
        if not new_domains_filtered:
            return

        msg = f"MonitorXYZ Report ::: {report_name}\n"
        msg += "```\n"
        for domain, foundby in new_domains.items():
            if flags.acunetix:
                self.acunetix(domain)
            ports = masscan(domain)
            ports_count = len(ports.split(','))  # Splitting the ports string and counting

            if ports_count > 10:
                template = f"{domain} by: {', '.join(foundby)} - [Annoying - maybe WAF]"
            else:
                template = f"{domain}  by: {', '.join(foundby)} ports: {ports}"
            template = f"{domain}  by: {', '.join(foundby)} ports: {ports}"
            self.done(f"Discoverd: {template}")
            msg += template + "\n"
        msg += "```"
        self.send_discord_report(msg)