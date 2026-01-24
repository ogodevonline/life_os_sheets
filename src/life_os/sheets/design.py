from .constants import EXPENSE_CATEGORIES, CATEGORY_COLORS

class Design:
    def __init__(self, sh, worksheets):
        self.sh = sh
        self.worksheets = worksheets

    def apply(self):
        fin_ws = self.worksheets['finances']
        study_ws = self.worksheets['study_tracker']
        strat_ws = self.worksheets['strategy']
        wish_ws = self.worksheets['wishlist']

        categories = EXPENSE_CATEGORIES
        category_colors = CATEGORY_COLORS

        requests = [
            # Флажки для учебы и вишлиста
            {"setDataValidation": {"range": {"sheetId": study_ws.id, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 6, "endColumnIndex": 8}, "rule": {"condition": {"type": "BOOLEAN"}}}},
            {"setDataValidation": {"range": {"sheetId": wish_ws.id, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 4, "endColumnIndex": 5}, "rule": {"condition": {"type": "BOOLEAN"}}}},
            
            # Закрепление шапок (финансы теперь имеют заголовок в строке 4)
            {"updateSheetProperties": {"properties": {"sheetId": fin_ws.id, "gridProperties": {"frozenRowCount": 4}}, "fields": "gridProperties.frozenRowCount"}},
            {"updateSheetProperties": {"properties": {"sheetId": strat_ws.id, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            
            # Цвета для стратегии
            {"repeatCell": {"range": {"sheetId": strat_ws.id, "startRowIndex": 0, "endRowIndex": 1}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.2, "green": 0.3, "blue": 0.4}, "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},

            # Выпадающее меню для категорий в финансах (удлинённый диапазон на год)
            {"setDataValidation": {"range": {"sheetId": fin_ws.id, "startRowIndex": 4, "endRowIndex": 370, "startColumnIndex": 1, "endColumnIndex": 2}, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": cat} for cat in categories]}}}},

            # Заголовок: светлый фон и жирный шрифт
            {"repeatCell": {"range": {"sheetId": fin_ws.id, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}, "textFormat": {"bold": True}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},

            # Полосы (banding) для данных
            {"addBanding": {"bandedRange": {"range": {"sheetId": fin_ws.id, "startRowIndex": 4, "endRowIndex": 370, "startColumnIndex": 0, "endColumnIndex": 6}, "rowProperties": {"firstBandColor": {"red": 1, "green": 1, "blue": 1}, "secondBandColor": {"red": 0.98, "green": 0.98, "blue": 0.98}}}}},

            # Формат валюты для столбцов Доход/Расход (D и E)
            {"repeatCell": {"range": {"sheetId": fin_ws.id, "startRowIndex": 4, "endRowIndex": 370, "startColumnIndex": 3, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "¤#,##0.00"}}}, "fields": "userEnteredFormat(numberFormat)"}},

            # Ширины столбцов: A-F
            {"updateDimensionProperties": {"range": {"sheetId": fin_ws.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 6}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}},

            # Conditional formatting: доходы (колонка D) — зелёный фон если > 0
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": fin_ws.id, "startRowIndex": 4, "endRowIndex": 370, "startColumnIndex": 3, "endColumnIndex": 4}], "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]}, "format": {"backgroundColor": {"red": 0.88, "green": 0.96, "blue": 0.88}}}}, "index": 0}},


            # Conditional formatting: расходы (колонка E) — светло-красный фон если > 0
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": fin_ws.id, "startRowIndex": 4, "endRowIndex": 370, "startColumnIndex": 4, "endColumnIndex": 5}], "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]}, "format": {"backgroundColor": {"red": 0.98, "green": 0.88, "blue": 0.88}}}}, "index": 0},}
        ]

        for cat, color in category_colors.items():
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": fin_ws.id, "startRowIndex": 4, "endRowIndex": 370, "startColumnIndex": 1, "endColumnIndex": 2}],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": cat}]},
                            "format": {"backgroundColor": color}
                        }
                    },
                    "index": 0
                }
            })

        self.sh.batch_update({"requests": requests})