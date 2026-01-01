from .auth import GoogleAuth
from ..sheets.finances import FinancesSheet
from ..sheets.study_tracker import StudyTrackerSheet
from ..sheets.strategy import StrategySheet
from ..sheets.wishlist import WishlistSheet
from ..sheets.design import Design

class LifeOS:
    def __init__(self):
        self.auth = GoogleAuth()
        self.gc = self.auth.authenticate()
        self.sh = None
        self.worksheets = {}

    def create_spreadsheet(self, title="Life OS v3.0: Ultimate Strategy"):
        self.sh = self.gc.create(title)
        return self.sh

    def build_sheets(self):
        if not self.sh:
            raise ValueError("Spreadsheet not created. Call create_spreadsheet first.")

        # Создание вкладок
        finances = FinancesSheet(self.sh)
        self.worksheets['finances'] = finances.create()

        study_tracker = StudyTrackerSheet(self.sh)
        self.worksheets['study_tracker'] = study_tracker.create()

        strategy = StrategySheet(self.sh)
        self.worksheets['strategy'] = strategy.create()

        wishlist = WishlistSheet(self.sh)
        self.worksheets['wishlist'] = wishlist.create()

        # Применение дизайна
        design = Design(self.sh, self.worksheets)
        design.apply()

    def get_url(self):
        return self.sh.url if self.sh else None