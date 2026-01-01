import os
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# --- НАСТРОЙКИ ---
load_dotenv()
START_DATE = date(2025, 1, 1)  # Начало симуляции
START_CAPITAL = 150000         # Стартовый капитал
SALARY_SAVE = 100000           # Ежемесячное пополнение
MONTHS_TO_SIMULATE = 12        # Горизонт планирования
BASE_RATE = 0.16               # Начальная ставка (16%)
RATE_DROP_STEP = 0.003         # Шаг снижения ставки в месяц

# 2. АГРЕССИВНАЯ ОЧИСТКА: Удаляем все старые настройки прокси,
# которые могли прилететь из .env или системы.
# Это удалит тот самый "socks://127.0.0.1:12334", который вызывает ошибку.
for key in list(os.environ.keys()):
    if "proxy" in key.lower():
        del os.environ[key]

# 3. Настраиваем подключение ТОЛЬКО через твой локальный HTTP-мост
# Твой мост: http://127.0.0.1:8888 -> socks5://127.0.0.1:12334
http_proxy = "http://127.0.0.1:8888"

os.environ["HTTP_PROXY"] = http_proxy
os.environ["HTTPS_PROXY"] = http_proxy
os.environ["http_proxy"] = http_proxy
os.environ["https_proxy"] = http_proxy

print(f"🌐 Прокси жестко переопределен на мост: {http_proxy}")

import argparse
parser = argparse.ArgumentParser(description="Investment strategy simulator")
parser.add_argument('--llm', choices=['groq', 'gemini'], help="Choose LLM: groq or gemini")
args = parser.parse_args()

# Попытка импорта AI (опционально)
try:
    from langchain.messages import HumanMessage
    from langchain_groq import ChatGroq
    from langchain_google_genai import ChatGoogleGenerativeAI
    groq_api_key = os.getenv("GROQ_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    HAS_AI = bool(groq_api_key or gemini_api_key)
except ImportError:
    HAS_AI = False

print("✅ Скрипт запущен. Расчет по точным датам...")

def get_rate(month_idx):
    """Возвращает ставку, снижающуюся каждый месяц"""
    r = BASE_RATE - (month_idx * RATE_DROP_STEP)
    return max(0.01, r)

def simulate_strategy_deposits_only():
    """
    Стратегия 1: Все деньги только на вклады.
    Старт: 150к на 5 месяцев.
    Далее: 100к каждый месяц (начиная с 1 февраля).
    """
    current_date = START_DATE
    # Список активных вкладов: {'amount': float, 'end_date': date, 'rate': float}
    active_deposits = []
    
    # История операций для таблицы
    history = []
    
    # Накопительные переменные
    total_invested_own = 0
    accumulated_profit_cash = 0 # Выплаченные проценты, которые лежат на счете/реинвестируются
    
    # 1. СТАРТ (01.01)
    # Вкладываем 150к на 5 месяцев
    active_deposits.append({
        'amount': START_CAPITAL,
        'end_date': current_date + relativedelta(months=5),
        'rate': BASE_RATE,
        'name': 'Стартовый'
    })
    total_invested_own += START_CAPITAL
    
    # Цикл по месяцам (0..11)
    for m in range(MONTHS_TO_SIMULATE + 1): # +1 чтобы захватить итог на начало следующего года
        current_date = START_DATE + relativedelta(months=m)
        events_log = []
        
        # А) Проверка закрытия вкладов (утро месяца)
        profit_this_month = 0
        liquidity_pool = 0 # Деньги от закрытых вкладов + прибыль
        
        still_active = []
        for dep in active_deposits:
            if dep['end_date'] <= current_date:
                # Вклад закрылся
                term_months = (dep['end_date'].year - (dep['end_date'] - relativedelta(months=5)).year) * 12 + dep['end_date'].month - (dep['end_date'] - relativedelta(months=5)).month 
                # Упрощенно берем срок из свойств или вычисляем разницу, здесь для точности:
                # Считаем доход: Сумма * Ставка * (Срок/12)
                # Важно: тут мы знаем срок. Для стартового 5 мес, для остальных 3 мес.
                # Чтобы не усложнять, пересчитаем срок по факту разницы дат, но для простоты кода используем фиксированные типы 5 и 3.
                
                duration = 5 if dep['name'] == 'Стартовый' else 3
                profit = dep['amount'] * (dep['rate'] * duration / 12)
                
                profit_this_month += profit
                liquidity_pool += (dep['amount'] + profit)
                events_log.append(f"💰 Закрыт вклад ({dep['name']}): +{int(profit)} руб.")
            else:
                still_active.append(dep)
        
        active_deposits = still_active
        accumulated_profit_cash += profit_this_month
        
        # Б) Пополнение зарплатой (только если это не 0-й месяц)
        salary_added = 0
        if m > 0 and m < 12: # Зарплата приходит с февраля по декабрь
            salary_added = SALARY_SAVE
            liquidity_pool += salary_added
            total_invested_own += salary_added
            events_log.append(f"📥 Зарплата: +{salary_added}")

        # В) Реинвестирование (открытие новых вкладов)
        # Если есть деньги в пуле (от закрытия или зарплаты), открываем новый вклад на 3 мес
        if liquidity_pool > 0 and m < 12:
            new_rate = get_rate(m)
            active_deposits.append({
                'amount': liquidity_pool,
                'end_date': current_date + relativedelta(months=3),
                'rate': new_rate,
                'name': f"От {current_date.strftime('%b')}"
            })
            events_log.append(f"🆕 Новый вклад: {int(liquidity_pool)} руб. под {new_rate*100:.1f}% на 3 мес.")
            liquidity_pool = 0 # Все вложили

        # Расчет итогов на текущую дату
        total_in_deposits = sum(d['amount'] for d in active_deposits)
        total_capital = total_in_deposits + liquidity_pool # liquidity_pool должен быть 0, если все вложили
        
        history.append({
            "Дата": current_date.strftime("%d.%m.%Y"),
            "Своих вложено": total_invested_own,
            "Капитал": round(total_capital, 0),
            "Прибыль (накопл.)": round(accumulated_profit_cash, 0),
            "События": "; ".join(events_log) if events_log else "—"
        })

    return pd.DataFrame(history)

def simulate_strategy_mixed():
    """
    Стратегия 2: Вклады + ИИС.
    Старт (01.01): 150к во Вклад (5 мес).
    Далее чередуем:
      - Февраль (ЗП #1): Вклад (чтобы поддержать ликвидность)
      - Март (ЗП #2): ИИС (ОФЗ)
      - Апрель (ЗП #3): Вклад
      ...
    """
    current_date = START_DATE
    vklads = [] # List of dicts
    iis_balance = 0
    
    total_invested_own = 0
    accumulated_profit = 0
    
    history = []
    
    # 1. СТАРТ (01.01)
    vklads.append({
        'amount': START_CAPITAL,
        'end_date': current_date + relativedelta(months=5),
        'rate': BASE_RATE,
        'name': 'Стартовый'
    })
    total_invested_own += START_CAPITAL
    
    salary_counter = 0 # Счетчик зарплат для чередования
    
    for m in range(MONTHS_TO_SIMULATE + 1):
        current_date = START_DATE + relativedelta(months=m)
        events_log = []
        current_rate = get_rate(m)
        
        # --- 1. Обработка Вкладов (закрытие) ---
        liquid_cash = 0
        new_vklads = []
        monthly_profit_vklad = 0
        
        for v in vklads:
            if v['end_date'] <= current_date:
                duration = 5 if v['name'] == 'Стартовый' else 3
                prof = v['amount'] * (v['rate'] * duration / 12)
                monthly_profit_vklad += prof
                liquid_cash += (v['amount'] + prof)
                events_log.append(f"💰 Вклад закрыт: +{int(prof)}")
            else:
                new_vklads.append(v)
        vklads = new_vklads
        accumulated_profit += monthly_profit_vklad
        
        # --- 2. Купоны по ИИС (каждый месяц упрощенно капает 15% годовых / 12) ---
        # Считаем, что купоны реинвестируются обратно в ИИС или падают на счет.
        # Для чистоты сравнения: купоны падают на ИИС и увеличивают базу.
        iis_income = iis_balance * (0.15 / 12)
        if iis_balance > 0:
            iis_balance += iis_income
            accumulated_profit += iis_income
            # events_log.append(f"📈 Купон ИИС: {int(iis_income)}") # Слишком много спама, скрываем
            
        # --- 3. Зарплата и Распределение ---
        if m > 0 and m < 12:
            salary_counter += 1
            total_invested_own += SALARY_SAVE
            
            # Логика чередования: Нечетные (1-я, 3-я зп) -> Вклад, Четные -> ИИС
            # 1 фев (ЗП1) -> Вклад
            # 1 мар (ЗП2) -> ИИС
            if salary_counter % 2 != 0:
                # Добавляем во Вклад
                amount_to_dep = SALARY_SAVE
                # Если были закрытые вклады (liquid_cash), добавляем их тоже сюда
                amount_to_dep += liquid_cash
                liquid_cash = 0 
                
                vklads.append({
                    'amount': amount_to_dep,
                    'end_date': current_date + relativedelta(months=3),
                    'rate': current_rate,
                    'name': f"Вкл-{current_date.month}"
                })
                events_log.append(f"🏦 Вклад (+ЗП): {int(amount_to_dep)}")
            else:
                # Добавляем на ИИС
                iis_balance += SALARY_SAVE
                events_log.append(f"🏛️ ИИС (+ЗП): {SALARY_SAVE}")
                
                # А что делать с закрывшимися вкладами (liquid_cash)? 
                # Стратегия: Держим на коротких вкладах, не переводим на ИИС (чтобы можно было снять)
                if liquid_cash > 0:
                    vklads.append({
                        'amount': liquid_cash,
                        'end_date': current_date + relativedelta(months=3),
                        'rate': current_rate,
                        'name': f"Реинвест-{current_date.month}"
                    })
                    events_log.append(f"🔄 Реинвест вклада: {int(liquid_cash)}")
                    liquid_cash = 0
        
        # Если это 0-й месяц или 13-й, но есть liquid_cash (например, реинвест стартового)
        if liquid_cash > 0 and m < 12:
             vklads.append({
                'amount': liquid_cash,
                'end_date': current_date + relativedelta(months=3),
                'rate': current_rate,
                'name': f"Реинвест-{current_date.month}"
            })
             events_log.append(f"🔄 Реинвест: {int(liquid_cash)}")

        # --- 4. Финиш года (Налоговый вычет и переоценка тела облигаций) ---
        # Допустим, 1 января следующего года мы получаем право на вычет и тело облигаций выросло
        if m == 12: 
            # Налоговый вычет (макс 52к или 13% от взносов). Взносы примерно 500-600к
            tax_deduction = min(52000, (iis_balance * 0.13)) # Грубая оценка от баланса
            # Рост тела облигаций (допустим 8% годовых, но они лежали не весь год).
            # Упростим: единоразовая переоценка в конце + вычет
            accumulated_profit += tax_deduction
            events_log.append(f"✅ Налоговый вычет: +{int(tax_deduction)}")
            # (Тело прибавляем к "Капиталу", но в "Прибыль" идет только дельта)
            
            # Прибавляем вычет к капиталу (как будто получили кэш)
            # В таблице покажем это увеличением общего капитала
            # Для корректности добавим к accumulated_profit
            pass

        vklad_sum = sum(v['amount'] for v in vklads)
        total_capital = vklad_sum + iis_balance + (52000 if m == 12 else 0) # Добавляем вычет вручную в капитал в конце

        history.append({
            "Дата": current_date.strftime("%d.%m.%Y"),
            "Своих вложено": total_invested_own,
            "На вкладах": int(vklad_sum),
            "На ИИС": int(iis_balance),
            "Капитал": int(total_capital),
            "События": "; ".join(events_log) if events_log else "—"
        })
        
    return pd.DataFrame(history)

# --- ЗАПУСК ---

print(f"\n🗓 ПАРАМЕТРЫ:")
print(f"Старт: {START_DATE}, Сумма: {START_CAPITAL}, ЗП: {SALARY_SAVE} (с 1 февраля)")
print("-" * 60)

df1 = simulate_strategy_deposits_only()
df2 = simulate_strategy_mixed()

# Вывод таблиц
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("\n🔵 СТРАТЕГИЯ 1: ТОЛЬКО ВКЛАДЫ")
print(df1[['Дата', 'Своих вложено', 'Капитал', 'Прибыль (накопл.)', 'События']].to_string(index=False))

print("\n🟠 СТРАТЕГИЯ 2: СМЕШАННАЯ (Вклады + ИИС)")
print(df2[['Дата', 'Своих вложено', 'На вкладах', 'На ИИС', 'Капитал', 'События']].to_string(index=False))

# Сохранение в файл
with open("detailed_report.md", "w", encoding="utf-8") as f:
    f.write("# Детальный расчет инвестиций\n\n")
    f.write("## Стратегия 1: Каскад вкладов\n")
    f.write(df1.to_markdown(index=False))
    f.write("\n\n## Стратегия 2: Вклады + ИИС\n")
    f.write(df2.to_markdown(index=False))

print(f"\n💾 Полный отчет сохранен в detailed_report.md")

# AI Анализ (если доступен ключ)
if HAS_AI:
    print("\n🧠 Запрос к AI для выводов...")
    chosen_llm = args.llm
    if chosen_llm == 'groq':
        if groq_api_key:
            llm = ChatGroq(api_key=groq_api_key, model="qwen/qwen3-32b")
        else:
            print("GROQ_API_KEY not set, skipping AI")
            HAS_AI = False
    elif chosen_llm == 'gemini':
        if gemini_api_key:
            llm = ChatGoogleGenerativeAI(google_api_key=gemini_api_key, model="gemini-3-flash-preview")
        else:
            print("GEMINI_API_KEY not set, skipping AI")
            HAS_AI = False
    else:
        # default: try groq first, then gemini
        if groq_api_key:
            llm = ChatGroq(api_key=groq_api_key, model="qwen/qwen3-32b")
        elif gemini_api_key:
            llm = ChatGoogleGenerativeAI(google_api_key=gemini_api_key, model="gemini-3-flash-preview")
        else:
            HAS_AI = False
    
    # Подготовка промпта с новыми данными
    final_s1 = df1.iloc[-1]
    final_s2 = df2.iloc[-1]
    
    prompt = f"""
    Сравни две стратегии накопления на 1 год (2025).
    
    Входные данные:
    - Старт 150 000 руб (январь).
    - Зарплата 100 000 руб (ежемесячно с февраля).
    
    Результаты расчетов:
    
    Стратегия 1 (Только вклады, реинвест каждые 3 мес):
    - Вложено своих: {final_s1['Своих вложено']}
    - Итоговый капитал: {final_s1['Капитал']}
    - Чистая прибыль: {final_s1['Прибыль (накопл.)']}
    
    Стратегия 2 (Микс Вклады + ИИС ОФЗ с вычетом):
    - Вложено своих: {final_s2['Своих вложено']}
    - Итоговый капитал: {final_s2['Капитал']} (включая вычет 52к в конце)
    
    Дай короткое резюме: 
    1. Какая стратегия выгоднее математически и на сколько?
    2. Какие плюсы у "Только вклады" (ликвидность)?
    3. Стоит ли заморачиваться с ИИС ради этой разницы на горизонте 1 год?
    """
    
    res = llm.invoke([HumanMessage(content=prompt)])
    print("\n📝 ОТВЕТ AI:\n")
    
    # --- ИСПРАВЛЕНИЕ ОБРАБОТКИ ОТВЕТА ---
    ai_text = ""
    
    # Проверяем, вернулся ли список (структура [{'type': 'text', 'text': '...'}])
    if isinstance(res.content, list):
        for part in res.content:
            if isinstance(part, dict) and 'text' in part:
                ai_text += part['text']
            elif isinstance(part, str):
                ai_text += part
    else:
        # Если вернулась обычная строка
        ai_text = str(res.content)
        
    print(ai_text)
    
    # Записываем уже обработанный текст (строку)
    with open("detailed_report.md", "a", encoding="utf-8") as f:
        f.write("\n\n## Анализ AI\n")
        f.write(ai_text)