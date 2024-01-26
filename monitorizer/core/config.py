from monitorizer.ui.arguments import args
import yaml


class Config():
    def __get_or_none(self,path):
        result = self.config.copy()
        for root in path.split("."):
            try:
                result = result[root]
            except Exception as e:
                return None
        
        if isinstance(result, str):
            result = result.strip()

        return result 

    def __init__(self):
        self.config = yaml.safe_load(open(args.config))

        self.discord_channel  = self.__get_or_none("report.discord.channel")
        self.discord_token    = self.__get_or_none("report.discord.token")

        self.discord_reporter_channel  = self.__get_or_none("report.discord_reporter.channel")
        self.discord_reporter_token    = self.__get_or_none("report.discord_reporter.token")

        self.acunetix_token = self.__get_or_none("report.acunetix.token")
        self.acunetix_host  = self.__get_or_none("report.acunetix.host")
        self.acunetix_port  = self.__get_or_none("report.acunetix.port")


        self.nuclei_interval = self.__get_or_none("settings.nuclei.interval")
        self.nuclei_enable   = self.__get_or_none("settings.nuclei.enable")
        self.nuclei_options  = self.__get_or_none("settings.nuclei.options")
        
        self.nuclei_fuzzing_interval = self.__get_or_none("settings.nuclei_fuzzing.interval")
        self.nuclei_fuzzing_enable   = self.__get_or_none("settings.nuclei_fuzzing.enable")
        self.nuclei_fuzzing_options  = self.__get_or_none("settings.nuclei_fuzzing.options")
        
        self.subdominator_interval = self.__get_or_none("settings.subdominator.interval")
        self.subdominator_enable   = self.__get_or_none("settings.subdominator.enable")
        self.subdominator_options  = self.__get_or_none("settings.subdominator.options")
        
        self.dirsearch_interval = self.__get_or_none("settings.dirsearch.interval")
        self.dirsearch_enable   = self.__get_or_none("settings.dirsearch.enable")
        self.dirsearch_options  = self.__get_or_none("settings.dirsearch.options")
