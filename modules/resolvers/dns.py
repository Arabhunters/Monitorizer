import dns.resolver

class DNS(object):
    def nxdomain(self,host):
        try:
            dns.resolver.query(host)
            return 0
        except Exception:
            return 1