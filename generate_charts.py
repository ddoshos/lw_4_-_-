# -*- coding: utf-8 -*-
"""
Дополнительные графики для лабораторной работы
Запускать из той же директории, что и main_full_v2.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch, FancyBboxPatch
import os

# ============================================================
# Настройки
# ============================================================
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# Палитра
COLORS = {
    'blue': '#2563eb',
    'red': '#dc2626',
    'green': '#16a34a',
    'orange': '#ea580c',
    'purple': '#9333ea',
    'gray': '#6b7280',
    'light_blue': '#93c5fd',
    'light_red': '#fca5a5',
    'light_green': '#86efac',
}

# ============================================================
# Загрузка данных
# ============================================================
def fix_bad_line(line):
    if len(line) > 9:
        return line[:9]
    return line

df_cgm = pd.read_csv('Device_Readings/PT-001_CGM данные непрерывного мониторинга глюкозы/glucose_readings_2024_03.csv',
                      usecols=lambda c: not c.startswith('Unnamed'))
df_cgm['timestamp'] = pd.to_datetime(df_cgm['timestamp'])

df_bp = pd.read_csv('Device_Readings/PT-002_BP - данные домашнего мониторинга АД (нерегулярные замеры)/home_bp_readings.csv')
df_bp['date_time'] = pd.to_datetime(df_bp['date_time'])

df_steps = pd.read_csv('Device_Readings/PT-003_Activity - данные шагомера (ежедневная активность)/daily_steps_2024_03.csv')
df_steps['date'] = pd.to_datetime(df_steps['date'])

df_sleep = pd.read_csv('Device_Readings/PT-003_Activity - данные шагомера (ежедневная активность)/sleep_data_2024_03.csv')
df_sleep['date'] = pd.to_datetime(df_sleep['date'])

df_bio = pd.read_csv('RESEARCH_DATA/Biomarkers_Research.csv')
df_labs = pd.read_csv('RESEARCH_DATA/Lab_Results_All.csv', on_bad_lines=fix_bad_line, engine='python')
df_ehr1 = pd.read_csv('RESEARCH_DATA/EHR_System_1.csv')
df_pharm = pd.read_csv('RESEARCH_DATA/Pharmacy_Database.csv')

print("Данные загружены. Строим графики...")

# ============================================================
# ГРАФИК 1. AGP — Ambulatory Glucose Profile (PT-001)
# Стандартный клинический отчёт CGM: percentiles по часам суток
# ============================================================
print("  1/5: AGP профиль глюкозы (PT-001)...")

df_cgm['hour'] = df_cgm['timestamp'].dt.hour + df_cgm['timestamp'].dt.minute / 60
glucose_col = 'glucose_mg_dl' if 'glucose_mg_dl' in df_cgm.columns else 'glucose_mg_dl'

# Группируем по часу
hourly = df_cgm.groupby('hour')[glucose_col]
p10 = hourly.apply(lambda x: np.percentile(x, 10))
p25 = hourly.apply(lambda x: np.percentile(x, 25))
p50 = hourly.apply(lambda x: np.percentile(x, 50))
p75 = hourly.apply(lambda x: np.percentile(x, 75))
p90 = hourly.apply(lambda x: np.percentile(x, 90))

fig, ax = plt.subplots(figsize=(12, 6))

# Заливка: 10-90 перцентиль (самый светлый)
ax.fill_between(p10.index, p10.values, p90.values, alpha=0.15, color=COLORS['blue'], label='10–90 перцентиль')
# 25-75 перцентиль
ax.fill_between(p25.index, p25.values, p75.values, alpha=0.30, color=COLORS['blue'], label='25–75 перцентиль (IQR)')
# Медиана
ax.plot(p50.index, p50.values, color=COLORS['blue'], linewidth=2.5, label='Медиана')

# Целевой диапазон 70-180
ax.axhspan(70, 180, alpha=0.08, color=COLORS['green'], zorder=0)
ax.axhline(70, color=COLORS['red'], linestyle='--', linewidth=1, alpha=0.7, label='Гипогликемия (<70)')
ax.axhline(180, color=COLORS['orange'], linestyle='--', linewidth=1, alpha=0.7, label='Гипергликемия (>180)')

ax.set_xlim(0, 24)
ax.set_xticks(range(0, 25, 2))
ax.set_xlabel('Часы суток', fontsize=11)
ax.set_ylabel('Глюкоза, мг/дл', fontsize=11)
ax.set_title('Ambulatory Glucose Profile (AGP)\nPT-001, непрерывный мониторинг глюкозы', fontsize=13, fontweight='bold')
ax.legend(loc='upper right', fontsize=8, framealpha=0.9)

plt.tight_layout()
plt.savefig('AGP_Profile_Patient1.png')
plt.close()
print("     -> AGP_Profile_Patient1.png")

# ============================================================
# ГРАФИК 2. Суточный профиль АД (PT-002)
# Систола + диастола + ЧСС, с выделением времени суток
# ============================================================
print("  2/5: Суточный профиль АД (PT-002)...")

fig, ax1 = plt.subplots(figsize=(12, 6))

# Сортируем по времени
df_bp_sorted = df_bp.sort_values('date_time').reset_index(drop=True)

# Цвета точек по времени суток
def time_color(hour):
    if 7 <= hour < 9:
        return COLORS['orange']  # утро
    elif 18 <= hour < 21:
        return COLORS['purple']  # вечер
    else:
        return COLORS['gray']    # прочее

colors_bp = [time_color(h) for h in df_bp_sorted['date_time'].dt.hour]

# Систолическое
ax1.scatter(df_bp_sorted['date_time'], df_bp_sorted['systolic'], 
            c=colors_bp, s=40, zorder=5, edgecolors='white', linewidth=0.5)
ax1.plot(df_bp_sorted['date_time'], df_bp_sorted['systolic'], 
         color=COLORS['red'], alpha=0.5, linewidth=1.5, label='Систолическое')

# Диастолическое
ax1.scatter(df_bp_sorted['date_time'], df_bp_sorted['diastolic'], 
            c=colors_bp, s=30, zorder=5, marker='s', edgecolors='white', linewidth=0.5)
ax1.plot(df_bp_sorted['date_time'], df_bp_sorted['diastolic'], 
         color=COLORS['blue'], alpha=0.5, linewidth=1.5, label='Диастолическое')

# Линии норм
ax1.axhline(140, color=COLORS['red'], linestyle='--', linewidth=1, alpha=0.4)
ax1.axhline(90, color=COLORS['blue'], linestyle='--', linewidth=1, alpha=0.4)
ax1.text(df_bp_sorted['date_time'].iloc[-1], 141, '140 мм рт.ст.', fontsize=7, color=COLORS['red'], ha='right')
ax1.text(df_bp_sorted['date_time'].iloc[-1], 91, '90 мм рт.ст.', fontsize=7, color=COLORS['blue'], ha='right')

# ЧСС на второй оси
ax2 = ax1.twinx()
ax2.plot(df_bp_sorted['date_time'], df_bp_sorted['heart_rate'], 
         color=COLORS['green'], alpha=0.4, linewidth=1, linestyle=':', label='ЧСС')
ax2.set_ylabel('ЧСС, уд/мин', fontsize=10, color=COLORS['green'])
ax2.tick_params(axis='y', labelcolor=COLORS['green'])
ax2.set_ylim(50, 100)

ax1.set_xlabel('Дата и время', fontsize=11)
ax1.set_ylabel('АД, мм рт.ст.', fontsize=11)
ax1.set_title('Суточный профиль артериального давления\nPT-002, домашний мониторинг', fontsize=13, fontweight='bold')

# Легенда
legend_elements = [
    Patch(facecolor=COLORS['red'], label='Систолическое'),
    Patch(facecolor=COLORS['blue'], label='Диастолическое'),
    Patch(facecolor=COLORS['orange'], label='Утренние замеры (7-9)'),
    Patch(facecolor=COLORS['purple'], label='Вечерние замеры (18-21)'),
]
ax1.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9)

ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=3))

plt.tight_layout()
plt.savefig('BP_Profile_Patient2.png')
plt.close()
print("     -> BP_Profile_Patient2.png")

# ============================================================
# ГРАФИК 3. Активность + Сон (PT-003) — dual-axis
# Шаги и качество сна по дням
# ============================================================
print("  3/5: Активность и сон (PT-003)...")

fig, ax1 = plt.subplots(figsize=(12, 6))

# Шаги — столбцы
ax1.bar(df_steps['date'], df_steps['steps'], color=COLORS['blue'], alpha=0.6, width=0.7, label='Шаги')
ax1.axhline(7000, color=COLORS['green'], linestyle='--', linewidth=1, alpha=0.6)
ax1.axhline(10000, color=COLORS['orange'], linestyle='--', linewidth=1, alpha=0.6)
ax1.text(df_steps['date'].iloc[-1], 7100, 'Норма 7000', fontsize=7, color=COLORS['green'], ha='right')
ax1.text(df_steps['date'].iloc[-1], 10100, 'Цель 10000', fontsize=7, color=COLORS['orange'], ha='right')

ax1.set_ylabel('Шаги в день', fontsize=11, color=COLORS['blue'])
ax1.tick_params(axis='y', labelcolor=COLORS['blue'])
ax1.set_ylim(0, 14000)

# Сон — линия на второй оси
ax2 = ax1.twinx()
ax2.plot(df_sleep['date'], df_sleep['sleep_score'], color=COLORS['purple'], linewidth=2.5, marker='o', 
         markersize=5, label='Качество сна')
ax2.fill_between(df_sleep['date'], 0, df_sleep['sleep_score'], alpha=0.08, color=COLORS['purple'])
ax2.set_ylabel('Sleep Score', fontsize=11, color=COLORS['purple'])
ax2.tick_params(axis='y', labelcolor=COLORS['purple'])
ax2.set_ylim(0, 100)

# Стресс — точки
stress_map = {'low': 1, 'medium': 2, 'moderate': 2, 'high': 3}
if 'stress_level' in df_steps.columns:
    stress_num = df_steps['stress_level'].astype(str).str.lower().map(stress_map)
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    ax3.scatter(df_steps['date'], stress_num, color=COLORS['red'], s=30, zorder=5, label='Стресс')
    ax3.set_ylabel('Уровень стресса', fontsize=10, color=COLORS['red'])
    ax3.tick_params(axis='y', labelcolor=COLORS['red'])
    ax3.set_yticks([1, 2, 3])
    ax3.set_yticklabels(['low', 'medium', 'high'])
    ax3.set_ylim(0.5, 3.5)

ax1.set_xlabel('Дата', fontsize=11)
ax1.set_title('Физическая активность, качество сна и стресс\nPT-003, март 2024', fontsize=13, fontweight='bold')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=3))

# Легенда
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8, framealpha=0.9)

plt.tight_layout()
plt.savefig('Activity_Sleep_Patient3.png')
plt.close()
print("     -> Activity_Sleep_Patient3.png")

# ============================================================
# ГРАФИК 4. Радарная диаграмма биомаркеров (все 3 пациента)
# ============================================================
print("  4/5: Радарная диаграмма биомаркеров...")

# Нормализуем биомаркеры (относительно максимума)
bio_cols = ['CRP_mg_L', 'Leptin_ng_mL', 'Adiponectin_ug_mL', 'IL6_pg_mL']
bio_labels = ['CRP\n(мг/л)', 'Лептин\n(нг/мл)', 'Адипонектин\n(мкг/мл)', 'IL-6\n(пг/мл)']
bio_normalized = df_bio[bio_cols].div(df_bio[bio_cols].max(), axis=1)

# Добавим HbA1c из лаборатории
hba1c_vals = []
for pid in df_bio['PatientID']:
    hba1c_row = df_labs[(df_labs['PatientID'] == pid) & (df_labs['TestCode'] == 'HBA1C')]
    if len(hba1c_row) > 0:
        hba1c_vals.append(float(hba1c_row['Value'].iloc[0]))
    else:
        hba1c_vals.append(0)

hba1c_norm = np.array(hba1c_vals) / max(hba1c_vals) if max(hba1c_vals) > 0 else np.array([0, 0, 0])

# Полные данные для радара
radar_cols = bio_normalized.values.tolist()
for i in range(3):
    radar_cols[i].append(hba1c_norm[i])

categories = bio_labels + ['HbA1c\n(%)']
N = len(categories)

angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

patient_names = ['PT-001 (Иванов)', 'PT-002 (Петров)', 'PT-003 (Сидорова)']
radar_colors = [COLORS['blue'], COLORS['red'], COLORS['green']]

for i in range(3):
    values = radar_cols[i] + [radar_cols[i][0]]
    ax.plot(angles, values, 'o-', linewidth=2.5, color=radar_colors[i], label=patient_names[i], markersize=6)
    ax.fill(angles, values, alpha=0.12, color=radar_colors[i])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 1.1)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=8)
ax.set_title('Сравнение биомаркеров пациентов\n(нормализованные значения)', fontsize=13, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

plt.tight_layout()
plt.savefig('Biomarkers_Radar.png')
plt.close()
print("     -> Biomarkers_Radar.png")

# ============================================================
# ГРАФИК 5. Интегрированная временная шкала (все пациенты)
# События из EHR, Labs, Pharmacy, Biomarkers
# ============================================================
print("  5/5: Интегрированная временная шкала...")

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)

patients = ['PT-001', 'PT-002', 'PT-003']
patient_full = ['PT-001 (Иванов И.И.)', 'PT-002 (Петров П.П.)', 'PT-003 (Сидорова С.С.)']
event_colors = {
    'Лаборатория': COLORS['blue'],
    'Визит': COLORS['purple'],
    'Аптека': COLORS['green'],
    'Биомаркеры': COLORS['orange'],
}

for idx, pid in enumerate(patients):
    ax = axes[idx]
    events = []

    # EHR
    ehr_rows = df_ehr1[df_ehr1['PID'] == pid]
    for _, row in ehr_rows.iterrows():
        date = pd.to_datetime(row['VisitDate'], format='%d.%m.%Y')
        events.append((date, 'Визит', f"Диагноз: {row['Diagnosis']}\nТерапия: {row['Therapy']}"))

    # Pharmacy
    pharm_rows = df_pharm[df_pharm['PatientID'] == pid]
    for _, row in pharm_rows.iterrows():
        date = pd.to_datetime(row['DispenseDate'], format='%d.%m.%Y')
        events.append((date, 'Аптека', f"{row['DrugName']} {row['Dose']} мг"))

    # Labs
    lab_rows = df_labs[df_labs['PatientID'] == pid]
    for _, row in lab_rows.iterrows():
        try:
            date = pd.to_datetime(row['Date'], format='%d.%m.%Y')
        except:
            date = pd.to_datetime(row['Date'])
        events.append((date, 'Лаборатория', f"{row['TestCode']}: {row['Value']} {row['Unit']}"))

    # Biomarkers
    bio_rows = df_bio[df_bio['PatientID'] == pid]
    for _, row in bio_rows.iterrows():
        date = pd.to_datetime(row['VisitDate'], format='%d.%m.%Y')
        events.append((date, 'Биомаркеры', f"CRP={row['CRP_mg_L']}, Leptin={row['Leptin_ng_mL']}"))

    # Сортируем
    events.sort(key=lambda x: x[0])

    # Рисуем
    for i, (date, etype, label) in enumerate(events):
        color = event_colors.get(etype, COLORS['gray'])
        ax.scatter(date, 1, color=color, s=100, zorder=5, edgecolors='white', linewidth=1)
        # Подпись с переносом
        y_offset = 1 + 0.15 + (i % 3) * 0.25
        ax.annotate(label, (date, 1), xytext=(date, y_offset),
                     fontsize=6, ha='center', va='bottom',
                     arrowprops=dict(arrowstyle='-', color=color, alpha=0.5),
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.8))

    # Линия времени
    if events:
        min_date = min(e[0] for e in events) - pd.Timedelta(days=30)
        max_date = max(e[0] for e in events) + pd.Timedelta(days=30)
        ax.hlines(1, min_date, max_date, colors=COLORS['gray'], linewidth=2, alpha=0.5)
        ax.set_xlim(min_date, max_date)

    ax.set_ylim(0.5, 2.5)
    ax.set_yticks([])
    ax.set_title(patient_full[idx], fontsize=11, fontweight='bold', loc='left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.tick_params(axis='x', rotation=30, labelsize=8)

# Общая легенда
legend_patches = [Patch(facecolor=c, label=k) for k, c in event_colors.items()]
fig.legend(handles=legend_patches, loc='upper right', fontsize=9, framealpha=0.9,
           bbox_to_anchor=(0.98, 0.98))

fig.suptitle('Интегрированная временная шкала пациентов\nСобытия из EHR, лаборатории, аптеки и биомаркеров', 
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('Integrated_Timeline.png')
plt.close()
print("     -> Integrated_Timeline.png")

print("\n Все 5 графиков созданы:")
print("  1. AGP_Profile_Patient1.png       — профиль глюкозы (AGP)")
print("  2. BP_Profile_Patient2.png        — суточный профиль АД")
print("  3. Activity_Sleep_Patient3.png    — активность, сон, стресс")
print("  4. Biomarkers_Radar.png           — радарная диаграмма биомаркеров")
print("  5. Integrated_Timeline.png       — интегрированная временная шкала")
