from datetime import datetime, timedelta
from gspread.utils import ValidationConditionType
from .constants import EXPENSE_CATEGORIES

class FinancesSheet:
    def __init__(self, sh):
        self.sh = sh

    def create(self):
        # Создаем лист категорий
        try:
            cat_ws = self.sh.worksheet("Категории")
        except:
            cat_ws = self.sh.add_worksheet(title="Категории", rows=100, cols=2)
        
        cat_ws.update('A1', [['Категории']], value_input_option='USER_ENTERED')
        cat_ws.update('A2', [[cat] for cat in EXPENSE_CATEGORIES], value_input_option='USER_ENTERED')

        # Основной лист финансов
        fin_ws = self.sh.get_worksheet(0)
        fin_ws.update_title("💰 Финансы")
        # Верхние сводные строки: кошелек, кредиты и общие итоги
        fin_summary = [
            ["КОШЕЛЕК", "=SUM(D5:D)-SUMIF(B5:B; \"Кредиты\"; E5:E)", "КРЕДИТЫ", "=SUMIF(B5:B; \"Кредиты\"; E5:E)"],
            ["ВСЕГО ДОХОД", "=SUM(D5:D)", "ВСЕГО РАСХОД", "=SUM(E5:E)"],
            ["", "", "", ""],
            ["Дата", "Категория", "Описание", "Доход (+)", "Расход (-)"]
        ]
        fin_ws.update('A1', fin_summary, value_input_option='USER_ENTERED')
        # Убираем колонку "Счет" (6-я), если она есть, чтобы не оставлять лишние столбцы
        try:
            if fin_ws.col_count >= 6:
                fin_ws.delete_columns(6)
        except Exception:
            pass

        # Заполняем даты на весь текущий год (1 января - 31 декабря)
        year = datetime.now().year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        days = (end_date - start_date).days + 1
        date_rows = [[(start_date + timedelta(days=i)).date().isoformat()] for i in range(days)]
        fin_ws.update(f'A5:A{5 + days - 1}', date_rows, value_input_option='USER_ENTERED')

        # Добавляем data validation для столбца Категория (B5:B<end>)
        # Получаем актуальные категории из листа (если пользователь добавил новые вручную)
        cats = [c for c in cat_ws.col_values(1)[1:] if c]
        if not cats:
            cats = EXPENSE_CATEGORIES

        fin_ws.add_validation(
            f"B5:B{5 + days - 1}",
            ValidationConditionType.one_of_list,
            cats,
            inputMessage="Выберите категорию",
            strict=False,
            showCustomUi=True,
        )

        # Форматирование и удобство: закрепить заголовок, сделать его ярким и настроить форматы столбцов
        try:
            fin_ws.format('A4:E4', {"backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}, "textFormat": {"bold": True}})
            fin_ws.freeze(rows=4)
            fin_ws.format(f'A5:A{5 + days - 1}', {'numberFormat': {'type': 'DATE', 'pattern': 'dd.MM.yyyy'}})
            fin_ws.format(f'D5:E{5 + days - 1}', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
        except Exception:
            # Если форматирование недоступно в окружении, пропускаем — основная функциональность не зависима от этого
            pass

        # Убираем старый подсчет по категориям внизу, вместо этого создаем лист сводки
        try:
            summary_ws = self.sh.worksheet("Сводка расходов")
        except:
            summary_ws = self.sh.add_worksheet(title="Сводка расходов", rows=50, cols=2)
        
        summary_ws.update('A1', [['Категория', 'Сумма']], value_input_option='USER_ENTERED')
        cats_for_summary = cats if cats else EXPENSE_CATEGORIES
        for i, cat in enumerate(cats_for_summary):
            row = i + 2
            summary_ws.update(f'A{row}:B{row}', [[cat, f"=SUMIF('💰 Финансы'!B5:B{5 + days - 1}; \"{cat}\"; '💰 Финансы'!E5:E{5 + days - 1})"]], value_input_option='USER_ENTERED')
        # Добавим итог по суммам
        last_row = len(cats_for_summary) + 2
        summary_ws.update(f'A{last_row}:B{last_row}', [['ИТОГО', f"=SUM(B2:B{last_row - 1})"]], value_input_option='USER_ENTERED')

        return fin_ws