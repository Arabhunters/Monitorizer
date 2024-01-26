import os
import re

class ScanParser(object):

    def check(self, inputs, url_mode=False):
        valid = []
        inputs = set(inputs)

        if url_mode:
            # Regex for validating full URLs
            regex = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
        else:
            # Original domain validation regex
            regex = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9](\.?))$"

        valid.extend(input_item for input_item in inputs if re.search(regex, input_item))
        return valid

    def puredns(self, data):
        domains = [line.split()[0] for line in data if line.strip()]
        return self.check(domains)

    def subfinder(self, data):
        domains = [line.strip() for line in data if line[0] != '.']
        return self.check(domains)

    def waymore(self, data):
        urls = [line.strip() for line in data]
        # Use the check function with url_mode set to True
        return self.check(urls, url_mode=True)

    def gau(self, data):
        urls = [line.strip() for line in data]
        # Use the check function with url_mode set to True
        return self.check(urls, url_mode=True)

    def default(self, data):
        domains = [line.strip() for line in data]
        return self.check(domains)

    def parse(self, scan_file):
        if not os.path.isfile(scan_file):
            return []

        data = open(scan_file, 'r').readlines()
        target, tool = os.path.basename(scan_file).split("_")

        if 'subfinder' in tool:
            return {'subfinder': self.subfinder(data)}
        elif 'puredns' in tool:
            return {'puredns': self.puredns(data)}
        elif 'waymore' in tool:
            return {'waymore': self.waymore(data)}
        elif 'gau' in tool:
            return {'gau': self.gau(data)}
        else:
            return {tool.strip(): self.default(data)}