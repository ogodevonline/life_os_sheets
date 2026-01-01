class StrategySheet:
    def __init__(self, sh):
        self.sh = sh

    def create(self):
        strat_ws = self.sh.add_worksheet(title="🎯 Стратегия", rows=50, cols=5)
        strat_data = [
            ["Горизонт", "Цель", "Зачем это мне?", "Приоритет", "Статус"],
            ["1 год (2026)", "Выучить Golang до уровня Middle", "Рост зп", "Высокий", "В процессе"],
            ["3 года", "Своя квартира / Релокация", "Комфорт", "Критично", "Идея"],
            ["5 лет", "", "", "", ""],
            ["10 лет", "", "", "", ""],
            ["20 лет", "Капитал и пассивный доход", "Свобода", "Макс", "План"]
        ]
        strat_ws.update('A1', strat_data)
        return strat_ws