class StudyTrackerSheet:
    def __init__(self, sh):
        self.sh = sh

    def create(self):
        study_ws = self.sh.add_worksheet(title="🎓 Учеба и Трекер", rows=200, cols=8)
        study_header = [["Предмет", "Тема / Ссылка", "Дата изучения", "Сложность (1-5)", "След. повтор", "СТАТУС", "Python/Go/Eng", "Gym"]]
        study_ws.update('A1', study_header)

        # Логика повторения
        study_logic = []
        for i in range(2, 100):
            next_date = f"=IF(ISBLANK(C{i}); \"\"; C{i} + POWER(2; 6-D{i}))"
            status = f"=IF(ISBLANK(E{i}); \"\"; IF(E{i}<=TODAY(); \"🔥 ПОВТОРИТЬ\"; \"✅\"))"
            study_logic.append([next_date, status])
        study_ws.update('E2:F100', study_logic, value_input_option='USER_ENTERED')
        return study_ws