class LocalReport():
    def local(self, msg, reporter, path='results.txt'):
        open(path, "a").write(msg + "\n")
        self.log(f"{reporter}: There was a problem reporting, local save is preformed at results.txt")
