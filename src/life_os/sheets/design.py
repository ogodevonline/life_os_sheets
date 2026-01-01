class Design:
    def __init__(self, sh, worksheets):
        self.sh = sh
        self.worksheets = worksheets

    def apply(self):
        fin_ws = self.worksheets['finances']
        study_ws = self.worksheets['study_tracker']
        strat_ws = self.worksheets['strategy']
        wish_ws = self.worksheets['wishlist']

        requests = [
            # Флажки для учебы и вишлиста
            {"setDataValidation": {"range": {"sheetId": study_ws.id, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 6, "endColumnIndex": 8}, "rule": {"condition": {"type": "BOOLEAN"}}}},
            {"setDataValidation": {"range": {"sheetId": wish_ws.id, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 4, "endColumnIndex": 5}, "rule": {"condition": {"type": "BOOLEAN"}}}},
            
            # Закрепление шапок
            {"updateSheetProperties": {"properties": {"sheetId": fin_ws.id, "gridProperties": {"frozenRowCount": 3}}, "fields": "gridProperties.frozenRowCount"}},
            {"updateSheetProperties": {"properties": {"sheetId": strat_ws.id, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            
            # Цвета для стратегии
            {"repeatCell": {"range": {"sheetId": strat_ws.id, "startRowIndex": 0, "endRowIndex": 1}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.2, "green": 0.3, "blue": 0.4}, "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}}
        ]

        self.sh.batch_update({"requests": requests})