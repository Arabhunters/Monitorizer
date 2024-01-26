import subprocess
import tempfile
import socket
import re

def _masscan_scan_reader(path):
    try:
        with open(path, 'r') as scan_file:
            ports = [x.strip() for x in re.findall(r'portid="(.*?)"', scan_file.read()) if x.strip()]

        return ','.join(ports) if ports else "no open ports"
    except Exception:
        return "can't find scan file"

def masscan(target):
    with tempfile.NamedTemporaryFile() as tempf:
        output = tempf.name
        try:
            subprocess.check_call(
                "./thirdparty/masscan/masscan {target} -p0-65535 --rate=10000 --open -oX {output}".format(
                    output=output,
                    target=socket.gethostbyname(target)),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True
            )
            return _masscan_scan_reader(output)
        except Exception:
            return "error"
