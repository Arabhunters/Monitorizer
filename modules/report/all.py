from monitorizer.core.config import Config
from modules.report.acunetix import AcunetixReport
from modules.report.local import LocalReport
from modules.report.discord_reporter import DiscordReport
from monitorizer.ui.cli import Console


class Report(Config, Console, LocalReport, DiscordReport, AcunetixReport):
    def __init__(self):
        """
        Initializes the Report class.
        """
        super().__init__()