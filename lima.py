import argparse
import asyncio
import json
import logging
import math
import os
from typing import List, Dict, Any, Union

import pandas as pd
from dotenv import load_dotenv

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

from langchain.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

print("✅ Импорты загружены")

# Используем HTTP прокси (который конвертирует в SOCKS5)
http_proxy = "http://127.0.0.1:8888"

os.environ["HTTP_PROXY"] = http_proxy
os.environ["HTTPS_PROXY"] = http_proxy
os.environ["http_proxy"] = http_proxy
os.environ["https_proxy"] = http_proxy

print(f"🌐 Используется HTTP прокси (конвертирует SOCKS5): {http_proxy}")

# Очистка старых прокси переменных
for key in ['ALL_PROXY', 'all_proxy', 'GROQ_PROXY']:
    os.environ.pop(key, None)

# Инициализация LangChain модели
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    llm = ChatGoogleGenerativeAI(
        google_api_key=gemini_api_key,
        model="gemini-3-flash-preview",
        temperature=0.3,
        max_retries=1,
        request_timeout=60,
    )

    try:
        print("🔄 Отправка запроса через HTTP→SOCKS5 прокси...")
        res = llm.invoke([HumanMessage(content="Test")])
        print("✅ TEST RESULT:", res.content)
        ai_available = True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        ai_available = False
else:
    print("⚠️ GEMINI_API_KEY not found, skipping AI analysis")
    ai_available = False

def calculate_only_deposits():
    # начальные данные
    salary_save = 100000
    start_sum = 150000
    months = 12
    rate = 0.16  # текущая ставка
    
    # Стартовый капитал (150к) — считаем его уже лежащим на вкладе
    deposits = [[start_sum, 0, 5, 0.16]] 
    
    history = []
    total_profit = 0
    total_invested = start_sum # Начинаем со 150к

    for m in range(months):
        # 1. Добавляем ежемесячное пополнение 100к (теперь с первого месяца m=0)
        deposits.append([salary_save, m, 3, rate])
        total_invested += salary_save
        
        # 2. Проверяем, какие вклады закрылись в этом месяце
        active_deposits = []
        monthly_profit = 0
        
        for d in deposits:
            sum_val, start_m, duration, d_rate = d
            # Проверка закрытия
            if m == start_m + duration:
                profit = sum_val * (d_rate * duration / 12)
                monthly_profit += profit
                # Реинвестируем тело + проценты на новый срок (3 мес)
                active_deposits.append([sum_val + profit, m, 3, rate])
            else:
                active_deposits.append(d)
        
        deposits = active_deposits
        total_profit += monthly_profit
        current_total = total_invested + total_profit
        
        history.append({
            "месяц": m + 1,
            "вложено своих": total_invested,
            "капитал на вкладах": round(current_total, 2),
            "прибыль (выплаты)": round(monthly_profit, 2),
            "текущая ставка": f"{round(rate*100, 1)}%"
        })
        
        # Плавное снижение ставки ЦБ на 0.3%
        rate -= 0.003

    return pd.DataFrame(history)


def summarize_strategy(df: pd.DataFrame, invested_col: str, capital_col: str, profit_col: str, months: int):
    """Возвращает словарь с ключевыми метриками по стратегии."""
    invested = float(df.iloc[-1][invested_col])
    ending = float(df.iloc[-1][capital_col])
    # profit column may be either per-period or cumulative; try to detect
    try:
        total_profit = float(df[profit_col].iloc[-1])
    except Exception:
        total_profit = float(df[profit_col].sum())

    roi = (ending - invested) / invested if invested != 0 else float('nan')
    years = months / 12.0
    try:
        cagr = (ending / invested) ** (1 / years) - 1 if invested > 0 and years > 0 else float('nan')
    except Exception:
        cagr = float('nan')

    return {
        "invested": invested,
        "ending_capital": ending,
        "total_profit": total_profit,
        "roi": roi,
        "cagr": cagr,
        "months": months,
    }

def calculate_fixed_threshold_strategy():
    start_sum = 150000
    monthly_save = 100000
    months = 12
    rate_vklad = 0.16
    
    # Стартовый Сбер (150к) уже в списке
    vklads = [[start_sum, 0, 5, 0.16]] 
    iis_balance = 0
    total_invested = start_sum # Начинаем со 150к базовых
    total_profit_cash = 0
    
    history = []
    
    for m in range(months):
        # 1. Пополнение происходит КАЖДЫЙ месяц (начиная с m=0)
        total_invested += monthly_save
        
        # Чередуем: месяц вклад, месяц ИИС
        if m % 2 == 0:
            # В 1-й месяц (m=0) докладываем 100к во вклады
            vklads.append([monthly_save, m, 3, rate_vklad])
        else:
            # Во 2-й месяц (m=1) отправляем 100к на ИИС
            iis_balance += monthly_save
        
        # 2. Обслуживание вкладов (проверка закрытия и реинвест)
        new_vklads = []
        monthly_profit_vklad = 0
        for v in vklads:
            v_sum, v_start, v_dur, v_rate = v
            if m == v_start + v_dur:
                p = v_sum * (v_rate * v_dur / 12)
                monthly_profit_vklad += p
                # Реинвестируем тело + проценты
                new_vklads.append([v_sum + p, m, 3, rate_vklad])
            else:
                new_vklads.append(v)
        vklads = new_vklads
        total_profit_cash += monthly_profit_vklad
        
        # 3. Купоны по ОФЗ (начисляются на текущий баланс ИИС)
        monthly_coupon = iis_balance * (0.15 / 12)
        total_profit_cash += monthly_coupon
        
        # 4. Расчет итогов месяца
        current_vklad_total = sum(v[0] for v in vklads)
        
        # Рост тела ОФЗ (+8%) и вычет (52к) в конце года (декабрь, m=11)
        current_iis_value = iis_balance
        if m == 11:
            current_iis_value += iis_balance * 0.08
            total_profit_cash += 52000 # Налоговый вычет
        
        history.append({
            "Месяц": m + 1,
            "Вложено своих": total_invested,
            "На вкладах": round(current_vklad_total, 0),
            "На ИИС (ОФЗ)": round(current_iis_value, 0),
            "Общий капитал": round(current_vklad_total + current_iis_value, 0),
            "Накопленная прибыль": round(total_profit_cash, 0)
        })
        
        # Плавное снижение ставки
        rate_vklad -= 0.003

    return pd.DataFrame(history)
df1 = calculate_only_deposits()
print("СТРАТЕГИЯ 1: ТОЛЬКО ВКЛАДЫ")
print(df1.to_string(index=False))

df_fixed = calculate_fixed_threshold_strategy()
print("\nСТРАТЕГИЯ 2: ВКЛАДЫ + ИИС С ВЫЧЕТОМ")
print(df_fixed.to_string(index=False))

# Итоги
print("\n📊 ИТОГИ:")
print(f"Стратегия 1: Вложено {df1.iloc[-1]['вложено своих']}, Капитал {df1.iloc[-1]['капитал на вкладах']}, Общая прибыль {df1['прибыль (выплаты)'].sum()}")
print(f"Стратегия 2: Вложено {df_fixed.iloc[-1]['Вложено своих']}, Капитал {df_fixed.iloc[-1]['Общий капитал']}, Общая прибыль {df_fixed.iloc[-1]['Накопленная прибыль']}")

# Генерация отчета в Markdown
df1_md = df1.copy()
df1_md = df1_md.round(2)
df1_md['капитал на вкладах'] = df1_md['капитал на вкладах'].apply(lambda x: f"{x:.2f}")
df1_md['прибыль (выплаты)'] = df1_md['прибыль (выплаты)'].apply(lambda x: f"{x:.2f}")

df_fixed_md = df_fixed.copy()
df_fixed_md = df_fixed_md.round(0)
df_fixed_md['Вложено своих'] = df_fixed_md['Вложено своих'].apply(lambda x: f"{x:.0f}")
df_fixed_md['На вкладах'] = df_fixed_md['На вкладах'].apply(lambda x: f"{x:.0f}")
df_fixed_md['На ИИС (ОФЗ)'] = df_fixed_md['На ИИС (ОФЗ)'].apply(lambda x: f"{x:.0f}")
df_fixed_md['Общий капитал'] = df_fixed_md['Общий капитал'].apply(lambda x: f"{x:.0f}")
df_fixed_md['Накопленная прибыль'] = df_fixed_md['Накопленная прибыль'].apply(lambda x: f"{x:.0f}")

with open("report.md", "w", encoding="utf-8") as f:
    f.write("# Инвестиционный отчет: Сравнение стратегий\n\n")
    f.write("Дата генерации: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
    
    f.write("## Стратегия 1: Только вклады\n\n")
    f.write(df1_md.to_markdown(index=False) + "\n\n")
    
    f.write("## Стратегия 2: Вклады + ИИС с налоговым вычетом\n\n")
    f.write(df_fixed_md.to_markdown(index=False) + "\n\n")
    
    f.write("## Итоги\n\n")
    f.write(f"- **Стратегия 1**: Вложено {df1.iloc[-1]['вложено своих']}, Капитал {df1.iloc[-1]['капитал на вкладах']:.2f}, Общая прибыль {df1['прибыль (выплаты)'].sum():.2f}\n")
    f.write(f"- **Стратегия 2**: Вложено {df_fixed.iloc[-1]['Вложено своих']:.0f}, Капитал {df_fixed.iloc[-1]['Общий капитал']:.0f}, Общая прибыль {df_fixed.iloc[-1]['Накопленная прибыль']:.0f}\n\n")

# Агентная система для анализа
# Сохранение CSV и вычисление сводки до запроса к AI
df1.to_csv("strategy_deposits.csv", index=False, encoding="utf-8")
df_fixed.to_csv("strategy_fixed_iis.csv", index=False, encoding="utf-8")

# Вычисляем метрики для краткой сводки
months = len(df1)
try:
    summary1 = summarize_strategy(df1, invested_col='вложено своих', capital_col='капитал на вкладах', profit_col='прибыль (выплаты)', months=months)
except Exception:
    summary1 = None

try:
    summary2 = summarize_strategy(df_fixed, invested_col='Вложено своих', capital_col='Общий капитал', profit_col='Накопленная прибыль', months=months)
except Exception:
    summary2 = None

# Попытка создать график сравнения капитала во времени
if HAS_MATPLOTLIB:
    try:
        # График капитала
        plt.figure(figsize=(10, 6))
        plt.plot(df1['месяц'], df1['капитал на вкладах'], label='Только вклады', marker='o', linewidth=2)
        plt.plot(df_fixed['Месяц'], df_fixed['Общий капитал'], label='Вклады + ИИС', marker='s', linewidth=2)
        plt.xlabel('Месяц')
        plt.ylabel('Капитал (руб.)')
        plt.title('Сравнение роста капитала по месяцам')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig('capital_comparison.png', dpi=150)
        plt.close()
        print('📈 График капитала сохранён: capital_comparison.png')

        # График прибыли (накопленной)
        plt.figure(figsize=(10, 6))
        cumulative_profit1 = df1['прибыль (выплаты)'].cumsum()
        cumulative_profit2 = df_fixed['Накопленная прибыль']
        plt.plot(df1['месяц'], cumulative_profit1, label='Только вклады', marker='o', linewidth=2)
        plt.plot(df_fixed['Месяц'], cumulative_profit2, label='Вклады + ИИС', marker='s', linewidth=2)
        plt.xlabel('Месяц')
        plt.ylabel('Накопленная прибыль (руб.)')
        plt.title('Сравнение роста прибыли по месяцам')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig('profit_comparison.png', dpi=150)
        plt.close()
        print('📈 График прибыли сохранён: profit_comparison.png')

    except Exception as e:
        print('⚠️ Не удалось создать графики:', e)
else:
    print('ℹ️ matplotlib не найден — графики пропущены')

# Добавляем дополнительные файлы и графики в report.md
with open("report.md", "a", encoding="utf-8") as f:
    f.write("## Дополнительные файлы\n\n")
    f.write("- CSV: strategy_deposits.csv\n")
    f.write("- CSV: strategy_fixed_iis.csv\n")
    if HAS_MATPLOTLIB:
        f.write("- График капитала: capital_comparison.png\n")
        f.write("- График прибыли: profit_comparison.png\n")
    else:
        f.write("- Графики: matplotlib недоступен, пропущено\n")

    f.write("## Графики\n\n")
    if HAS_MATPLOTLIB:
        f.write("### Сравнение капитала\n\n")
        f.write("![Сравнение капитала](capital_comparison.png)\n\n")
        f.write("### Сравнение прибыли\n\n")
        f.write("![Сравнение прибыли](profit_comparison.png)\n\n")
    else:
        f.write("Графики недоступны (matplotlib не установлен).\n\n")

# Добавляем краткую сводку в report.md
with open("report.md", "a", encoding="utf-8") as f:
    f.write("\n## Краткая сводка по стратегиям\n\n")
    if summary1:
        f.write(f"- **Стратегия 1 (Только вклады)**: вложено {summary1['invested']:.0f}, итоговый капитал {summary1['ending_capital']:.2f}, прибыль {summary1['total_profit']:.2f}, ROI {summary1['roi']:.2%}, CAGR {summary1['cagr']:.2%}\n")
    else:
        f.write("- **Стратегия 1 (Только вклады)**: не удалось вычислить сводку\n")
    if summary2:
        f.write(f"- **Стратегия 2 (Вклады + ИИС)**: вложено {summary2['invested']:.0f}, итоговый капитал {summary2['ending_capital']:.0f}, прибыль {summary2['total_profit']:.0f}, ROI {summary2['roi']:.2%}, CAGR {summary2['cagr']:.2%}\n")
    else:
        f.write("- **Стратегия 2 (Вклады + ИИС)**: не удалось вычислить сводку\n")
    f.write("\n")

# Конец подготовки данных

if ai_available:
    parts: List[str] = []
    parts.append("Проанализируй две инвестиционные стратегии и дай чёткие, практичные выводы.")
    parts.append("\n\nКраткая сводка по стратегиям:\n")
    if summary1:
        parts.append(f"Стратегия 1 (Только вклады): вложено {summary1['invested']:.0f}, итог {summary1['ending_capital']:.2f}, ROI {summary1['roi']:.2%}, CAGR {summary1['cagr']:.2%}.\n")
    else:
        parts.append("Стратегия 1: сводка недоступна.\n")
    if summary2:
        parts.append(f"Стратегия 2 (Вклады + ИИС): вложено {summary2['invested']:.0f}, итог {summary2['ending_capital']:.0f}, ROI {summary2['roi']:.2%}, CAGR {summary2['cagr']:.2%}.\n\n")
    else:
        parts.append("Стратегия 2: сводка недоступна.\n\n")
    parts.append("Полные таблицы сохранены в файлах: strategy_deposits.csv и strategy_fixed_iis.csv. Отчёт в report.md.")
    parts.append("\n\nВопросы для анализа (отвечай по пунктам):\n")
    parts.append("1) Какая стратегия предпочтительнее по итоговому капиталу и почему?\n")
    parts.append("2) Насколько велика абсолютная и относительная разница в прибыли между стратегиями?\n")
    parts.append("3) Какие ключевые риски для каждой стратегии (ликвидность, процентный риск, налоговые/регуляторные)?\n")
    parts.append("4) Какие улучшения/альтернативы вы бы рекомендовали (короткий список действий)?\n")
    parts.append("5) Дай итоговую рекомендацию для инвестора, ориентированного на капитализацию через год.")

    prompt = "".join(parts)

    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n🤖 АНАЛИЗ ОТ AI:")
    # Обработка ответа Gemini (может быть списком)
    if isinstance(response.content, list) and response.content:
        ai_text = response.content[0].get('text', str(response.content))
    else:
        ai_text = str(response.content)
    print(ai_text)
    
    # Добавить анализ в markdown
    with open("report.md", "a", encoding="utf-8") as f:
        f.write("## Анализ от AI\n\n")
        f.write(ai_text + "\n")
else:
    print("\n🤖 AI анализ недоступен (нет API ключа)")
    with open("report.md", "a", encoding="utf-8") as f:
        f.write("## Анализ от AI\n\n")
        f.write("AI анализ недоступен (нет API ключа)\n")

print("\n📄 Отчет сохранен в report.md")