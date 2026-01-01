from datetime import datetime, timedelta

class FinancesSheet:
    def __init__(self, sh):
        self.sh = sh

    def create(self):
        fin_ws = self.sh.get_worksheet(0)
        fin_ws.update_title("💰 Финансы")
        fin_summary = [
            ["КОШЕЛЕК", "=SUM(D4:D1000)-SUM(E4:E1000)", "КРЕДИТЫ", "=SUMIF(B4:B1000; 'Кредиты'; E4:E1000)"],
            ["", "", "", ""],
            ["Дата", "Категория", "Описание", "Доход (+)", "Расход (-)", "Счет"]
        ]
        fin_ws.update('A1', fin_summary, value_input_option='USER_ENTERED')

        # Заполняем даты на 100 дней вперед
        start_date = datetime.now()
        date_rows = [[(start_date + timedelta(days=i)).strftime('%d.%m.%Y')] for i in range(100)]
        fin_ws.update('A4:A103', date_rows)
        return fin_ws