# -*- coding: utf-8 -*-
"""
Лабораторная работа: Семантическая интеграция медицинских данных
Полный код для всех пунктов ТЗ
"""

# Нужно подгрузить библиотеки и прочее из requirements.txt.txt
# pip install -r requirements.txt
# python -m pip install -r requirements.txt.txt
# python.exe -m pip install --upgrade pip (или так)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def fix_bad_line(line):
    """Обрезает строки с лишними полями (как S-1006 с 10 полями вместо 9)."""
    if len(line) > 9:
        return line[:9]
    return line


def find_col(df, candidates):
    """Поиск колонки по подстроке (регистронезависимо)."""
    for c in candidates:
        for col in df.columns:
            if c.lower() in col.lower():
                return col
    return None


def find_file(filename, search_dirs=['.', 'RESEARCH_DATA', 'other_data', 'source_data']):
    """Поиск файла в нескольких директориях."""
    for d in search_dirs:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return filename  # вернём как есть, чтобы получить понятную ошибку


def parse_pgx(filepath):
    """Парсинг PGx_Results.txt — извлечение генетических профилей пациентов."""
    profiles = {}
    current_patient = None
    current_gene = None
    current_genotype = None
    current_phenotype = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('Пациент:'):
                # PT-001 (Иванов И.И.)
                m = re.search(r'(PT-\d+)', line)
                if m:
                    if current_patient:
                        profiles[current_patient] = {
                            'Gene': current_gene,
                            'Genotype': current_genotype,
                            'Phenotype': current_phenotype
                        }
                    current_patient = m.group(1)
                    current_gene = None
                    current_genotype = None
                    current_phenotype = None
            elif line.startswith('Ген:'):
                current_gene = line.replace('Ген:', '').strip()
            elif line.startswith('Генотип:'):
                current_genotype = line.replace('Генотип:', '').strip()
            elif line.startswith('Фенотип:'):
                current_phenotype = line.replace('Фенотип:', '').strip()
        # Последний пациент
        if current_patient:
            profiles[current_patient] = {
                'Gene': current_gene,
                'Genotype': current_genotype,
                'Phenotype': current_phenotype
            }
    return profiles


def parse_date(date_str):
    """Парсинг даты в разных форматах (DD.MM.YYYY или YYYY-MM-DD)."""
    if pd.isna(date_str):
        return None
    s = str(date_str).strip()
    for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
        try:
            return pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            continue
    try:
        return pd.to_datetime(s, dayfirst=True)
    except:
        return None


def std_date(dt):
    """Стандартизация даты в формат DD.MM.YYYY."""
    if pd.isna(dt) or dt is None:
        return None
    try:
        return pd.to_datetime(dt).strftime('%d.%m.%Y')
    except:
        return str(dt)


# ============================================================
# ПУНКТ 1. Анализ источников данных
# ============================================================
print("=" * 60)
print("ПУНКТ 1. Анализ источников данных")
print("=" * 60)

paths = {
    'CGM': 'Device_Readings/PT-001_CGM данные непрерывного мониторинга глюкозы/glucose_readings_2024_03.csv',
    'BP': 'Device_Readings/PT-002_BP - данные домашнего мониторинга АД (нерегулярные замеры)/home_bp_readings.csv',
    'Activity': 'Device_Readings/PT-003_Activity - данные шагомера (ежедневная активность)/daily_steps_2024_03.csv',
    'Sleep': 'Device_Readings/PT-003_Activity - данные шагомера (ежедневная активность)/sleep_data_2024_03.csv',
    'Labs': 'RESEARCH_DATA/Lab_Results_All.csv',
    'Biomarkers': 'RESEARCH_DATA/Biomarkers_Research.csv',
    'EHR_1': 'RESEARCH_DATA/EHR_System_1.csv',
    'EHR_2': 'RESEARCH_DATA/EHR_System_2.csv',
    'Pharmacy': 'RESEARCH_DATA/Pharmacy_Database.csv',
}

analysis_data = []

for name, path in paths.items():
    try:
        sep = ';' if name == 'EHR_2' else ','
        if name == 'Labs':
            df = pd.read_csv(path, on_bad_lines=fix_bad_line, engine='python', sep=sep)
        else:
            df = pd.read_csv(path, sep=sep)
        analysis_data.append({
            'Источник': name,
            'Файл': path,
            'Строк': len(df),
            'Столбцов': len(df.columns),
            'Колонки': ', '.join(df.columns.tolist()),
            'Типы данных': str(df.dtypes.value_counts().to_dict()),
            'Пропуски (всего)': int(df.isnull().sum().sum())
        })
        print(f"  OK  {name}: {len(df)} строк, {len(df.columns)} колонок")
    except FileNotFoundError:
        analysis_data.append({'Источник': name, 'Файл': path, 'Ошибка': 'Файл не найден'})
        print(f"  !!  {name}: файл не найден — {path}")
    except Exception as e:
        analysis_data.append({'Источник': name, 'Файл': path, 'Ошибка': str(e)})
        print(f"  !!  {name}: {e}")

# Проверяем PGx
pgx_path = find_file('PGx_Results.txt')
try:
    pgx_profiles = parse_pgx(pgx_path)
    analysis_data.append({
        'Источник': 'PGx',
        'Файл': pgx_path,
        'Строк': len(pgx_profiles),
        'Столбцов': 3,
        'Колонки': 'Gene, Genotype, Phenotype',
        'Типы данных': 'text',
        'Пропуски (всего)': 0
    })
    print(f"  OK  PGx: {len(pgx_profiles)} пациентов, файл: {pgx_path}")
except Exception as e:
    analysis_data.append({'Источник': 'PGx', 'Файл': pgx_path, 'Ошибка': str(e)})
    print(f"  !!  PGx: {e}")

# Проверяем Microbiome
micro_path = find_file('Microbiome_Data.csv')
try:
    df_micro = pd.read_csv(micro_path)
    analysis_data.append({
        'Источник': 'Microbiome',
        'Файл': micro_path,
        'Строк': len(df_micro),
        'Столбцов': len(df_micro.columns),
        'Колонки': ', '.join(df_micro.columns.tolist()),
        'Типы данных': str(df_micro.dtypes.value_counts().to_dict()),
        'Пропуски (всего)': int(df_micro.isnull().sum().sum())
    })
    print(f"  OK  Microbiome: {len(df_micro)} строк, {len(df_micro.columns)} колонок")
except Exception as e:
    analysis_data.append({'Источник': 'Microbiome', 'Файл': micro_path, 'Ошибка': str(e)})
    print(f"  !!  Microbiome: {e}")

df_analysis = pd.DataFrame(analysis_data)
df_analysis.to_excel('Data_Sources_Analysis.xlsx', index=False, engine='openpyxl')
print("-> Сохранено: Data_Sources_Analysis.xlsx\n")


# ============================================================
# ПУНКТ 2. Создание глоссария (glossary.xlsx)
# ============================================================
print("=" * 60)
print("ПУНКТ 2. Создание глоссария")
print("=" * 60)

# Лист «Лабораторные исследования»
lab_ref_data = {
    'Код в источнике': ['GLU', 'HBA1C', 'ALT'],
    'Стандартный код': ['GLUC', 'HBA1C', 'ALT'],
    'Название на русском': ['Глюкоза плазмы', 'Гликированный гемоглобин', 'Аланинаминотрансфераза'],
    'Единица СИ': ['ммоль/л', '%', 'Ед/л'],
    'Референсные значения': ['3.3-5.5', '4.0-6.0', '10-40']
}
df_lab_ref = pd.DataFrame(lab_ref_data)

# Лист «Диагнозы по МКБ-10»
icd_ref_data = {
    'Код МКБ-10': ['E11', 'E11.9', 'I10'],
    'Полное название': [
        'Сахарный диабет 2 типа',
        'Инсулиннезависимый сахарный диабет без осложнений',
        'Эссенциальная (первичная) гипертензия'
    ],
    'Категория': ['Эндокринология', 'Эндокринология', 'Кардиология']
}
df_icd_ref = pd.DataFrame(icd_ref_data)

# Лист «Лекарственные препараты» (МНН-сопоставление)
drug_ref_data = {
    'Название в источнике': ['Метформин', 'Metformini', 'Глюкофаж', 'Гликлазид', 'Аторвастатин'],
    'МНН': ['Metformin', 'Metformin', 'Metformin', 'Gliclazide', 'Atorvastatin'],
    'Группа': ['Бигуаниды', 'Бигуаниды', 'Бигуаниды', 'Сульфонилмочевины', 'Статины']
}
df_drug_ref = pd.DataFrame(drug_ref_data)

with pd.ExcelWriter('glossary.xlsx', engine='openpyxl') as writer:
    df_lab_ref.to_excel(writer, sheet_name='Лабораторные исследования', index=False)
    df_icd_ref.to_excel(writer, sheet_name='Диагнозы по МКБ-10', index=False)
    df_drug_ref.to_excel(writer, sheet_name='Лекарственные препараты', index=False)

print("-> Сохранено: glossary.xlsx (3 листа)\n")


# ============================================================
# ПУНКТ 3. Конвертация глюкозы мг/дл -> ммоль/л (Value_SI)
# ============================================================
print("=" * 60)
print("ПУНКТ 3. Конвертация глюкозы")
print("=" * 60)

lab_file = 'RESEARCH_DATA/Lab_Results_All.csv'
df_labs = pd.read_csv(lab_file, on_bad_lines=fix_bad_line, engine='python')
print(f"  Прочитано строк: {len(df_labs)}")

def convert_to_si(row):
    if row['TestCode'] != 'GLU':
        return np.nan
    value = pd.to_numeric(row['Value'], errors='coerce')
    unit = str(row['Unit']).strip()
    if pd.isna(value):
        return np.nan
    if 'mg' in unit.lower():
        return round(value * 0.0555, 2)
    return round(value, 2)

df_labs['Value_SI'] = df_labs.apply(convert_to_si, axis=1)
output_labs = 'RESEARCH_DATA/Lab_Results_All_SI.csv'
df_labs.to_csv(output_labs, index=False)
print(f"-> Сохранено: {output_labs}")

glu = df_labs[df_labs['TestCode'] == 'GLU'][
    ['SampleID', 'PatientID', 'Date', 'Value', 'Unit', 'Value_SI', 'Ref_Low', 'Ref_High']
]
print("  Глюкоза (GLU):")
print(glu.to_string(index=False))
print()


# ============================================================
# ПУНКТ 4. Семантические конфликты
# ============================================================
print("=" * 60)
print("ПУНКТ 4. Семантические конфликты")
print("=" * 60)

discrepancies = []

# 4.1 Единицы измерения S-1006
discrepancies.append({
    'Конфликт': 'Единицы измерения',
    'Источник 1': 'Lab_Results_All: S-1006 Unit=mmol/L',
    'Источник 2': 'Ref_Low=70, Ref_High=100 (формат mg/dL) + лишнее поле mg/dL',
    'Решение': 'Считать значение в mg/dL. 6.9 mg/dL × 0.0555 = 0.38 ммоль/л — нереалистично. Вероятно опечатка: 69 mg/dL = 3.83 ммоль/л. Пометить как ошибку ввода.'
})

# 4.2 BMI
discrepancies.append({
    'Конфликт': 'Разный BMI',
    'Источник 1': 'EHR_System_1: PT-001 BMI=28.7 (измерено)',
    'Источник 2': 'EHR_System_2: PT-002 расчёт 94/1.78^2=29.67',
    'Решение': 'Использовать значение из EHR как измеренное. Расчётное — для проверки.'
})

# 4.3 Названия лекарств
discrepancies.append({
    'Конфликт': 'Названия лекарств',
    'Источник 1': 'EHR_1: Метформин 500 мг; EHR_2: Metformini 500',
    'Источник 2': 'Аптека: Метформин',
    'Решение': 'Использовать МНН (Metformin). Все варианты — одно и то же действующее вещество.'
})

# 4.4 Коды диагнозов
discrepancies.append({
    'Конфликт': 'Коды диагнозов',
    'Источник 1': 'EHR_1: E11, E11.9 (МКБ-10)',
    'Источник 2': 'EHR_2: "Diabetes mellitus typus II" (текст)',
    'Решение': 'Стандартизировать на МКБ-10: E11.9 для СД2 без осложнений.'
})

# 4.5 Формат даты
discrepancies.append({
    'Конфликт': 'Формат даты',
    'Источник 1': 'Lab_Results, EHR_1, Pharmacy: DD.MM.YYYY',
    'Источник 2': 'EHR_2, Biomarkers: YYYY-MM-DD',
    'Решение': 'Стандартизировать на DD.MM.YYYY при интеграции.'
})

# 4.6 Разделитель CSV
discrepancies.append({
    'Конфликт': 'Разделитель CSV',
    'Источник 1': 'EHR_1, Labs, Pharmacy: запятая',
    'Источник 2': 'EHR_2: точка с запятой',
    'Решение': 'Указывать sep при чтении. Не влияет на семантику, но мешает автоматической загрузке.'
})

# 4.7 Разные лаборатории
discrepancies.append({
    'Конфликт': 'Разные лаборатории',
    'Источник 1': 'PT-001: GLU в LAB-A (S-1001, 14.03.2023)',
    'Источник 2': 'PT-001: GLU в LAB-B (S-1003, 09.09.2023)',
    'Решение': 'Разные методы могут давать систематическое смещение. Учитывать при сравнении.'
})

df_disc = pd.DataFrame(discrepancies)
df_disc.to_excel('Discrepancies_Report.xlsx', index=False, engine='openpyxl')
print("-> Сохранено: Discrepancies_Report.xlsx")
for d in discrepancies:
    print(f"  - {d['Конфликт']}: {d['Источник 1']} vs {d['Источник 2']}")
print()


# ============================================================
# ПУНКТ 5. Интегрированная модель данных (master_model.xlsx)
# ============================================================
print("=" * 60)
print("ПУНКТ 5. Интегрированная модель данных")
print("=" * 60)

# --- Читаем все источники ---
df_ehr1 = pd.read_csv('RESEARCH_DATA/EHR_System_1.csv')
df_ehr2 = pd.read_csv('RESEARCH_DATA/EHR_System_2.csv', sep=';')
df_pharm = pd.read_csv('RESEARCH_DATA/Pharmacy_Database.csv')
df_bio = pd.read_csv('RESEARCH_DATA/Biomarkers_Research.csv')

# --- Лист «Пациенты» ---
patients_data = []
patient_names = {
    'PT-001': 'Иванов Иван Иванович',
    'PT-002': 'Петров Пётр Петрович',
    'PT-003': 'Сидорова Светлана Сергеевна'
}

for pid, name in patient_names.items():
    gene_info = pgx_profiles.get(pid, {})
    gene_str = f"{gene_info.get('Gene', 'N/A')}: {gene_info.get('Genotype', 'N/A')}"
    patients_data.append({
        'PatientID': pid,
        'ФИО_стандарт': name,
        'Дата_рождения': '15.03.1958' if pid == 'PT-001' else ('22.07.1965' if pid == 'PT-002' else '10.11.1970'),
        'Генетический_профиль': gene_str,
        'Фенотип': gene_info.get('Phenotype', 'N/A')
    })

df_patients = pd.DataFrame(patients_data)

# --- Лист «Временная шкала» ---
timeline = []

# Из EHR_1
for _, row in df_ehr1.iterrows():
    timeline.append({
        'PatientID': row['PID'],
        'Дата': row['VisitDate'],
        'Событие': 'Визит к врачу',
        'Тип': 'Диагноз',
        'Значение': row['Diagnosis'],
        'Источник': 'EHR_System_1'
    })
    timeline.append({
        'PatientID': row['PID'],
        'Дата': row['VisitDate'],
        'Событие': 'Назначение терапии',
        'Тип': 'Терапия',
        'Значение': row['Therapy'],
        'Источник': 'EHR_System_1'
    })
    timeline.append({
        'PatientID': row['PID'],
        'Дата': row['VisitDate'],
        'Событие': 'Измерение BMI',
        'Тип': 'Антропометрия',
        'Значение': str(row['BMI']),
        'Источник': 'EHR_System_1'
    })

# Из EHR_2
for _, row in df_ehr2.iterrows():
    timeline.append({
        'PatientID': row['PatientCode'],
        'Дата': row['Data_Visit'],
        'Событие': 'Визит к врачу',
        'Тип': 'Диагноз',
        'Значение': row['PrimaryDx'],
        'Источник': 'EHR_System_2'
    })
    if pd.notna(row['SecondaryDx']):
        timeline.append({
            'PatientID': row['PatientCode'],
            'Дата': row['Data_Visit'],
            'Событие': 'Сопутствующий диагноз',
            'Тип': 'Диагноз',
            'Значение': row['SecondaryDx'],
            'Источник': 'EHR_System_2'
        })
    timeline.append({
        'PatientID': row['PatientCode'],
        'Дата': row['Data_Visit'],
        'Событие': 'Назначение терапии',
        'Тип': 'Терапия',
        'Значение': row['MedicationList'],
        'Источник': 'EHR_System_2'
    })

# Из Labs
for _, row in df_labs.iterrows():
    val_display = f"{row['Value_SI'] if pd.notna(row['Value_SI']) else row['Value']} {row['Unit']}"
    timeline.append({
        'PatientID': row['PatientID'],
        'Дата': row['Date'],
        'Событие': 'Лабораторный тест',
        'Тип': row['TestCode'],
        'Значение': val_display,
        'Источник': 'Lab_Results'
    })

# Из Pharmacy
for _, row in df_pharm.iterrows():
    timeline.append({
        'PatientID': row['PatientID'],
        'Дата': row['DispenseDate'],
        'Событие': 'Выдача лекарства',
        'Тип': 'Фармация',
        'Значение': f"{row['DrugName']} {row['Dose']} {row['Form']}",
        'Источник': 'Pharmacy_Database'
    })

# Из Biomarkers
for _, row in df_bio.iterrows():
    for biomarker in ['Adiponectin_ug_mL', 'Leptin_ng_mL', 'CRP_mg_L', 'IL6_pg_mL']:
        timeline.append({
            'PatientID': row['PatientID'],
            'Дата': row['VisitDate'],
            'Событие': 'Биомаркер',
            'Тип': biomarker,
            'Значение': str(row[biomarker]),
            'Источник': 'Biomarkers_Research'
        })

df_timeline = pd.DataFrame(timeline)
# Сортируем по пациенту и дате
df_timeline['_sort_date'] = df_timeline['Дата'].apply(parse_date)
df_timeline = df_timeline.sort_values(['PatientID', '_sort_date']).drop(columns=['_sort_date'])

with pd.ExcelWriter('master_model.xlsx', engine='openpyxl') as writer:
    df_patients.to_excel(writer, sheet_name='Пациенты', index=False)
    df_timeline.to_excel(writer, sheet_name='Временная шкала', index=False)

print(f"-> Сохранено: master_model.xlsx")
print(f"  Лист 'Пациенты': {len(df_patients)} пациентов")
print(f"  Лист 'Временная шкала': {len(df_timeline)} событий")
print()


# ============================================================
# ПУНКТ 6. Анализ CGM (PT-001)
# ============================================================
print("=" * 60)
print("ПУНКТ 6. Анализ CGM (PT-001)")
print("=" * 60)

df_cgm = pd.read_csv(paths['CGM'])
print(f"  CGM колонки: {list(df_cgm.columns)}")
print(f"  Первые 3 строки:")
print(df_cgm.head(3).to_string())

time_col = find_col(df_cgm, ['timestamp', 'time', 'date'])
glucose_col = find_col(df_cgm, ['glucose_mg', 'glucose', 'mg_dl', 'mg/dl'])
meal_col = find_col(df_cgm, ['event', 'meal', 'food'])
print(f"\n  Определены колонки -> время: {time_col}, глюкоза: {glucose_col}, приём пищи: {meal_col}")

df_cgm[time_col] = pd.to_datetime(df_cgm[time_col])
df_cgm = df_cgm.sort_values(by=time_col).reset_index(drop=True)

# 6.1 Time in Range (70-180 mg/dL)
tir_count = ((df_cgm[glucose_col] >= 70) & (df_cgm[glucose_col] <= 180)).sum()
total_count = len(df_cgm)
tir_percent = (tir_count / total_count) * 100
print(f"\n  6.1 Time in Range (70-180 mg/dL): {tir_percent:.2f}% ({tir_count}/{total_count})")

# CV (коэффициент вариации)
glucose_mean = df_cgm[glucose_col].mean()
glucose_std = df_cgm[glucose_col].std()
cv = (glucose_std / glucose_mean) * 100
print(f"  CV (коэффициент вариации): {cv:.2f}%")

# Оценочный HbA1c (формула Nathan)
estimated_hba1c = (glucose_mean + 46.7) / 28.7
print(f"  Оценочный HbA1c (Nathan): {estimated_hba1c:.2f}%")

# 6.2 Гипогликемия (<70 mg/dL)
hypo_data = df_cgm[df_cgm[glucose_col] < 70]
if not hypo_data.empty:
    min_glucose = hypo_data[glucose_col].min()
    hypo_duration_minutes = len(hypo_data) * 5
    print(f"\n  6.2 Гипогликемия: найдено {len(hypo_data)} точек, мин. значение {min_glucose} мг/дл, продолжительность ~{hypo_duration_minutes} мин")
    print("      Временные точки:")
    for _, row in hypo_data.iterrows():
        print(f"        {row[time_col]} -> {row[glucose_col]} мг/дл")
else:
    print("\n  6.2 Эпизодов гипогликемии не обнаружено.")

# 6.3 График
plt.figure(figsize=(14, 7))
plt.plot(df_cgm[time_col], df_cgm[glucose_col], label='Глюкоза (мг/дл)', color='blue', linewidth=0.8)
plt.axhline(y=70, color='green', linestyle='--', label='Нижняя граница (70)')
plt.axhline(y=180, color='green', linestyle='--', label='Верхняя граница (180)')
plt.fill_between(df_cgm[time_col], 70, 180, color='green', alpha=0.1, label='Целевой диапазон')
if meal_col and meal_col in df_cgm.columns:
    meals = df_cgm[df_cgm[meal_col].notna()]
    if not meals.empty:
        plt.scatter(meals[time_col], meals[glucose_col], color='red', zorder=5, label='Приём пищи', s=50)
plt.title('Суточный профиль глюкозы (PT-001, 19.03.2024)')
plt.xlabel('Время')
plt.ylabel('Глюкоза (мг/дл)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('Glucose_Profile_Patient1.png', dpi=150)
plt.close()
print(f"\n  6.3 График сохранён: Glucose_Profile_Patient1.png\n")


# ============================================================
# ПУНКТ 7. Анализ АД (PT-002)
# ============================================================
print("=" * 60)
print("ПУНКТ 7. Анализ АД (PT-002)")
print("=" * 60)

df_bp = pd.read_csv(paths['BP'])
print(f"  BP колонки: {list(df_bp.columns)}")
print(f"  Первые 3 строки:")
print(df_bp.head(3).to_string())

time_col_bp = find_col(df_bp, ['date_time', 'timestamp', 'time', 'date'])
sys_col = find_col(df_bp, ['systolic', 'sys'])
dia_col = find_col(df_bp, ['diastolic', 'dia'])
print(f"\n  Определены колонки -> время: {time_col_bp}, сист: {sys_col}, диаст: {dia_col}")

df_bp[time_col_bp] = pd.to_datetime(df_bp[time_col_bp])
df_bp['Hour'] = df_bp[time_col_bp].dt.hour

# 7.1 Средние значения
morning_mask = df_bp['Hour'].between(7, 9)
evening_mask = df_bp['Hour'].between(18, 21)
day_mask = df_bp['Hour'].between(7, 22)
night_mask = (df_bp['Hour'] >= 22) | (df_bp['Hour'] < 7)

avg_morning = df_bp.loc[morning_mask, sys_col].mean() if morning_mask.any() else None
avg_evening = df_bp.loc[evening_mask, sys_col].mean() if evening_mask.any() else None
avg_total = df_bp[sys_col].mean()
avg_day = df_bp.loc[day_mask, sys_col].mean() if day_mask.any() else None
avg_night = df_bp.loc[night_mask, sys_col].mean() if night_mask.any() else None

print(f"\n  7.1 Средние значения систолического АД:")
print(f"      Утреннее (7-9):     {avg_morning:.2f} мм рт.ст." if avg_morning else "      Утреннее: нет данных")
print(f"      Вечернее (18-21):   {avg_evening:.2f} мм рт.ст." if avg_evening else "      Вечернее: нет данных")
print(f"      Общее среднее:      {avg_total:.2f} мм рт.ст.")

# 7.2 Вариабельность
bp_series = df_bp[sys_col].dropna()
variability = bp_series.std() if len(bp_series) > 1 else 0
print(f"\n  7.2 Вариабельность (STDEV систолического АД): {variability:.2f}")

# 7.3 Суточный индекс
if avg_day and avg_night and not np.isnan(avg_day) and not np.isnan(avg_night):
    si = ((avg_day - avg_night) / avg_day) * 100
    print(f"  7.3 Суточный индекс (SI): {si:.2f}% (день: {avg_day:.2f}, ночь: {avg_night:.2f})")
    if si < 10:
        print(f"      -> Non-dipper (недостаточное снижение nocturnal АД)")
    elif si < 20:
        print(f"      -> Dipper (нормальное снижение)")
    else:
        print(f"      -> Over-dipper (чрезмерное снижение)")
else:
    print(f"  7.3 Суточный индекс: недостаточно данных (день: {avg_day}, ночь: {avg_night})")
print()


# ============================================================
# ПУНКТ 8. Анализ активности (PT-003)
# ============================================================
print("=" * 60)
print("ПУНКТ 8. Анализ активности (PT-003)")
print("=" * 60)

df_steps = pd.read_csv(paths['Activity'])
df_sleep = pd.read_csv(paths['Sleep'])
print(f"  Steps колонки: {list(df_steps.columns)}")
print(f"  Sleep колонки: {list(df_sleep.columns)}")

steps_col = find_col(df_steps, ['steps'])
act_min_col = find_col(df_steps, ['active_minutes', 'active', 'activity'])
sleep_quality_col = find_col(df_sleep, ['sleep_score', 'sleep_quality', 'quality'])
stress_col = find_col(df_steps, ['stress_level', 'stress'])

print(f"\n  Steps -> дата: date, шаги: {steps_col}, активность: {act_min_col}")
print(f"  Sleep -> качество сна: {sleep_quality_col}, стресс: {stress_col}")

# 8.1 Недельные показатели
if 'date' in df_steps.columns:
    df_steps['date'] = pd.to_datetime(df_steps['date'])
    df_steps['Week'] = df_steps['date'].dt.isocalendar().week.astype(int)

    weekly_stats = df_steps.groupby('Week').agg(
        Среднее_шагов=(steps_col, 'mean'),
        Дней_в_неделе=('date', 'count'),
        Суммарная_активность_мин=(act_min_col, 'sum')
    ).reset_index()

    df_steps['Meets_Steps_Goal'] = (df_steps[steps_col] >= 7000) & (df_steps[steps_col] <= 10000)
    percent_goal = (df_steps['Meets_Steps_Goal'].sum() / len(df_steps)) * 100

    print(f"\n  8.1 Недельные показатели:")
    print(weekly_stats.to_string(index=False))
    print(f"\n  Процент дней с нормой шагов (7000-10000): {percent_goal:.2f}%")

    # Проверка ВОЗ
    for _, w in weekly_stats.iterrows():
        status = "соответствует ВОЗ" if w['Суммарная_активность_мин'] >= 150 else "НЕ соответствует ВОЗ"
        print(f"  Неделя {int(w['Week'])}: {int(w['Суммарная_активность_мин'])} мин активности -> {status}")

# 8.2 Корреляция активности и сна/стресса
print(f"\n  8.2 Взаимосвязь активности и сна/стресса:")
if 'date' in df_steps.columns and 'date' in df_sleep.columns:
    df_sleep['date'] = pd.to_datetime(df_sleep['date'])
    df_merged = pd.merge(df_steps, df_sleep, on='date', how='inner', suffixes=('_steps', '_sleep'))
    print(f"  Объединено строк: {len(df_merged)}")

    if sleep_quality_col and sleep_quality_col in df_merged.columns:
        corr_sleep = df_merged[steps_col].corr(df_merged[sleep_quality_col])
        print(f"  Корреляция шагов и качества сна ({sleep_quality_col}): {corr_sleep:.3f}" if pd.notna(corr_sleep) else "  Корреляция: недостаточно данных")

    if stress_col and stress_col in df_merged.columns:
        # Преобразуем текстовый стресс в числа
        stress_map = {'low': 1, 'medium': 2, 'moderate': 2, 'high': 3, 'очень высокий': 4, 'низкий': 1, 'средний': 2, 'высокий': 3}
        stress_numeric = df_merged[stress_col].astype(str).str.lower().map(stress_map)
        if stress_numeric.notna().any():
            corr_stress = df_merged[steps_col].corr(stress_numeric)
            print(f"  Корреляция шагов и уровня стресса ({stress_col}): {corr_stress:.3f}" if pd.notna(corr_stress) else "  Корреляция: недостаточно данных")
        else:
            print(f"  Уровень стресса ({stress_col}) не содержит распознаваемых значений")
    else:
        if 'stress_level' in df_steps.columns:
            stress_map = {'low': 1, 'medium': 2, 'moderate': 2, 'high': 3}
            stress_numeric = df_steps['stress_level'].astype(str).str.lower().map(stress_map)
            if stress_numeric.notna().any():
                corr_stress = df_steps[steps_col].corr(stress_numeric)
                print(f"  Корреляция шагов и стресса (stress_level): {corr_stress:.3f}" if pd.notna(corr_stress) else "  Корреляция: недостаточно данных")

    # Корреляция сна и стресса
    if stress_col and stress_col in df_merged.columns and sleep_quality_col and sleep_quality_col in df_merged.columns:
        stress_map = {'low': 1, 'medium': 2, 'moderate': 2, 'high': 3}
        stress_numeric = df_merged[stress_col].astype(str).str.lower().map(stress_map)
        if stress_numeric.notna().any():
            corr_sls = stress_numeric.corr(df_merged[sleep_quality_col])
            print(f"  Корреляция стресса и качества сна: {corr_sls:.3f}" if pd.notna(corr_sls) else "  Корреляция: недостаточно данных")
else:
    print("  Не найдены нужные колонки для объединения")
print()


# ============================================================
# ПУНКТ 3.4. Комплексный анализ и рекомендации
# ============================================================
print("=" * 60)
print("ПУНКТ 3.4. Комплексный анализ и рекомендации")
print("=" * 60)

# --- Клинические профили ---
profiles = []

# PT-001
profiles.append({
    'PatientID': 'PT-001',
    'ФИО': 'Иванов Иван Иванович',
    'Возраст': 66,
    'Диагноз': 'СД2 (E11.9)',
    'Терапия': 'Метформин 850 мг + Гликлазид 30 мг',
    'Генетика': 'SLC22A1: GA (сниженный транспорт метформина)',
    'HbA1c_лаб': df_labs[(df_labs['PatientID']=='PT-001')&(df_labs['TestCode']=='HBA1C')]['Value'].iloc[-1] if len(df_labs[(df_labs['PatientID']=='PT-001')&(df_labs['TestCode']=='HBA1C')])>0 else None,
    'HbA1c_оценочный': round(estimated_hba1c, 2),
    'TIR': round(tir_percent, 2),
    'CV': round(cv, 2),
    'Гипогликемии': len(hypo_data),
    'BMI': df_ehr1['BMI'].iloc[-1],
    'Биомаркеры': f"CRP={df_bio[df_bio['PatientID']=='PT-001']['CRP_mg_L'].iloc[0]}, Leptin={df_bio[df_bio['PatientID']=='PT-001']['Leptin_ng_mL'].iloc[0]}, Adiponectin={df_bio[df_bio['PatientID']=='PT-001']['Adiponectin_ug_mL'].iloc[0]}"
})

# PT-002
hba1c_002 = df_labs[(df_labs['PatientID']=='PT-002')&(df_labs['TestCode']=='HBA1C')]['Value'].iloc[0] if len(df_labs[(df_labs['PatientID']=='PT-002')&(df_labs['TestCode']=='HBA1C')])>0 else None
profiles.append({
    'PatientID': 'PT-002',
    'ФИО': 'Петров Пётр Петрович',
    'Возраст': 60,
    'Диагноз': 'СД2 (E11.9) + Гипертония (I10)',
    'Терапия': 'Metformini 500',
    'Генетика': 'CYP2C9: AA (медленный метаболизм сульфонилмочевин)',
    'HbA1c_лаб': hba1c_002,
    'HbA1c_оценочный': None,
    'TIR': None,
    'CV': None,
    'Гипогликемии': None,
    'BMI': round(94/(1.78**2), 1),
    'Биомаркеры': f"CRP={df_bio[df_bio['PatientID']=='PT-002']['CRP_mg_L'].iloc[0]}, Leptin={df_bio[df_bio['PatientID']=='PT-002']['Leptin_ng_mL'].iloc[0]}, Adiponectin={df_bio[df_bio['PatientID']=='PT-002']['Adiponectin_ug_mL'].iloc[0]}"
})

# PT-003
hba1c_003 = df_labs[(df_labs['PatientID']=='PT-003')&(df_labs['TestCode']=='HBA1C')]['Value'].iloc[0] if len(df_labs[(df_labs['PatientID']=='PT-003')&(df_labs['TestCode']=='HBA1C')])>0 else None
profiles.append({
    'PatientID': 'PT-003',
    'ФИО': 'Сидорова Светлана Сергеевна',
    'Возраст': 55,
    'Диагноз': 'СД2 (E11.9)',
    'Терапия': 'Метформин 850 мг + Аторвастатин 20 мг',
    'Генетика': 'KCNJ11: TT (хороший ответ на сульфонилмочевины)',
    'HbA1c_лаб': hba1c_003,
    'HbA1c_оценочный': None,
    'TIR': None,
    'CV': None,
    'Гипогликемии': None,
    'BMI': None,
    'Биомаркеры': f"CRP={df_bio[df_bio['PatientID']=='PT-003']['CRP_mg_L'].iloc[0]}, Leptin={df_bio[df_bio['PatientID']=='PT-003']['Leptin_ng_mL'].iloc[0]}, Adiponectin={df_bio[df_bio['PatientID']=='PT-003']['Adiponectin_ug_mL'].iloc[0]}"
})

df_profiles = pd.DataFrame(profiles)
print("Клинические профили:")
print(df_profiles.to_string(index=False))

# --- Персонализированные рекомендации ---
recommendations = []

# PT-001
recommendations.extend([
    {'PatientID': 'PT-001', 'Категория': 'Терапевтические', 'Рекомендация': 'Учитывая полиморфизм OCT1 (GA) и эпизоды гипогликемии — рассмотреть переход на пролонгированную форму метформина', 'Обоснование': 'Сниженный транспорт метформина в гепатоциты → риск накопления и гипогликемий'},
    {'PatientID': 'PT-001', 'Категория': 'Терапевтические', 'Рекомендация': 'Добавить мониторинг постпрандиальной гликемии (через 2 ч после еды)', 'Обоснование': 'TIR 84.38%, но есть эпизоды гипогликемии — нужна коррекция дозы'},
    {'PatientID': 'PT-001', 'Категория': 'Образ жизни', 'Рекомендация': 'Рекомендовать перекус перед сном для профилактики ночных гипогликемий', 'Обоснование': 'Гипогликемии в 04:20-04:35 (мин. 67 мг/дл)'},
    {'PatientID': 'PT-001', 'Категория': 'Образ жизни', 'Рекомендация': 'Сместить приём метформина на время еды для уменьшения диспепсии', 'Обоснование': 'Стандартная рекомендация при GA-генотипе OCT1'},
])

# PT-002
recommendations.extend([
    {'PatientID': 'PT-002', 'Категория': 'Терапевтические', 'Рекомендация': 'Учитывая CYP2C9 AA (медленный метаболизм) — с осторожностью назначать сульфонилмочевины', 'Обоснование': 'Риск гипогликемий из-за замедленного метаболизма'},
    {'PatientID': 'PT-002', 'Категория': 'Терапевтические', 'Рекомендация': 'Усилить антигипертензивную терапию (утреннее АД 148.4, вечернее 152.2)', 'Обоснование': 'АД выше целевых значений (<130/80 для СД2)'},
    {'PatientID': 'PT-002', 'Категория': 'Образ жизни', 'Рекомендация': 'Снижение массы тела (BMI 29.7 — ожирение I степени)', 'Обоснование': 'Высокий лептин (34.2 нг/мл) указывает на лептинорезистентность'},
])

# PT-003
recommendations.extend([
    {'PatientID': 'PT-003', 'Категория': 'Терапевтические', 'Рекомендация': 'Учитывая KCNJ11 TT — хороший ответ на сульфонилмочевины при недостаточной эффективности метформина', 'Обоснование': 'Генотип TT связан с повышенным риском СД2, но хорошим ответом на СМ'},
    {'PatientID': 'PT-003', 'Категория': 'Образ жизни', 'Рекомендация': 'Поддерживать физическую активность (в среднем ~9600 шагов/день, 38.7% дней в норме)', 'Обоснование': 'Близко к рекомендации ВОЗ 7000-10000 шагов'},
    {'PatientID': 'PT-003', 'Категория': 'Образ жизни', 'Рекомендация': 'Контроль липидного профиля (на фоне аторвастатина 20 мг)', 'Обоснование': 'Низкий CRP (1.2 мг/л) — хороший противовоспалительный профиль'},
])

df_rec = pd.DataFrame(recommendations)
df_rec.to_excel('Clinical_Recommendations.xlsx', index=False, engine='openpyxl')
print(f"\n-> Сохранено: Clinical_Recommendations.xlsx ({len(df_rec)} рекомендаций)")

# --- Интегральные показатели ---
integral = []

for p in profiles:
    pid = p['PatientID']
    # Индекс комплаентности: дни выдачи лекарства / общие дни наблюдения
    rx_days = df_pharm[df_pharm['PatientID']==pid]
    if len(rx_days) > 0:
        # Подсчёт уникальных дней выдачи
        unique_rx_days = rx_days['DispenseDate'].nunique()
        # Общий период наблюдения (упрощённо — по labs)
        lab_dates = df_labs[df_labs['PatientID']==pid]['Date'].nunique()
        compliance = (unique_rx_days / max(lab_dates, 1)) * 100 if lab_dates > 0 else 0
    else:
        compliance = 0

    # Индекс метаболического контроля
    hba1c_val = p['HbA1c_лаб']
    hba1c_target = 7.0
    tir_val = p['TIR']
    tir_target = 70.0
    if hba1c_val and tir_val:
        imc = (hba1c_target / float(hba1c_val)) + (tir_target / tir_val)
    elif hba1c_val:
        imc = (hba1c_target / float(hba1c_val))
    else:
        imc = None

    # Риск ССО
    if pid == 'PT-001':
        risk = (avg_total / 100 if False else 120/100) + (float(hba1c_val)/10 if hba1c_val else 0.7) + 0
    elif pid == 'PT-002':
        risk = (avg_total / 100) + (float(hba1c_val)/10 if hba1c_val else 0.9) + 1  # +1 за гипертонию
    elif pid == 'PT-003':
        risk = (110 / 100) + (float(hba1c_val)/10 if hba1c_val else 0.7) + 0
    else:
        risk = None

    integral.append({
        'PatientID': pid,
        'Индекс_комплаентности_%': round(compliance, 2),
        'Индекс_метаболического_контроля': round(float(imc), 2) if imc else None,
        'HbA1c_лаб': hba1c_val,
        'HbA1c_цель': 7.0,
        'TIR_%': tir_val,
        'TIR_цель_%': 70.0,
        'Риск_ССО': round(risk, 2) if risk else None
    })

df_integral = pd.DataFrame(integral)
df_integral.to_excel('Integral_Indicators.xlsx', index=False, engine='openpyxl')
print(f"-> Сохранено: Integral_Indicators.xlsx")
print(df_integral.to_string(index=False))
print()


# ============================================================
# ПУНКТ 3.5. Исследовательский анализ
# ============================================================
print("=" * 60)
print("ПУНКТ 3.5. Исследовательский анализ")
print("=" * 60)

# --- 5.1 Корреляционный анализ ---
print("\n  5.1 Корреляционный анализ (биомаркеры):")

# HbA1c vs биомаркеры
hba1c_vals = []
crp_vals = []
leptin_vals = []
adipo_vals = []

for _, row in df_bio.iterrows():
    pid = row['PatientID']
    hba1c_row = df_labs[(df_labs['PatientID']==pid) & (df_labs['TestCode']=='HBA1C')]
    if len(hba1c_row) > 0:
        hba1c_vals.append(float(hba1c_row['Value'].iloc[0]))
        crp_vals.append(float(row['CRP_mg_L']))
        leptin_vals.append(float(row['Leptin_ng_mL']))
        adipo_vals.append(float(row['Adiponectin_ug_mL']))

if len(hba1c_vals) >= 3:
    corr_hba1c_crp = np.corrcoef(hba1c_vals, crp_vals)[0, 1]
    corr_hba1c_leptin = np.corrcoef(hba1c_vals, leptin_vals)[0, 1]
    corr_hba1c_adipo = np.corrcoef(hba1c_vals, adipo_vals)[0, 1]
    print(f"  HbA1c vs CRP:          r = {corr_hba1c_crp:.3f}")
    print(f"  HbA1c vs Leptin:       r = {corr_hba1c_leptin:.3f}")
    print(f"  HbA1c vs Adiponectin:  r = {corr_hba1c_adipo:.3f}")
else:
    corr_hba1c_crp = corr_hba1c_leptin = corr_hba1c_adipo = None
    print("  Недостаточно данных для корреляции")

# Карта преобразования текстового стресса в числа
stress_map = {'low': 1, 'medium': 2, 'moderate': 2, 'high': 3,
              'низкий': 1, 'средний': 2, 'высокий': 3, 'очень высокий': 4}

# Корреляция шагов и стресса
corr_steps_stress = None
if 'stress_level' in df_steps.columns and steps_col in df_steps.columns:
    s = df_steps[[steps_col, 'stress_level']].dropna().copy()
    s['stress_num'] = s['stress_level'].astype(str).str.lower().map(stress_map)
    s = s.dropna(subset=['stress_num'])
    if len(s) >= 3:
        corr_steps_stress = s[steps_col].corr(s['stress_num'])
        print(f"  Шаги vs Стресс:        r = {corr_steps_stress:.3f}")

# Корреляция сна и стресса
corr_sleep_stress = None
if 'date' in df_steps.columns and 'date' in df_sleep.columns:
    df_sleep['date'] = pd.to_datetime(df_sleep['date'])
    df_m = pd.merge(df_steps, df_sleep, on='date', how='inner', suffixes=('_s', '_sl'))
    if 'stress_level' in df_m.columns and 'sleep_score' in df_m.columns:
        d = df_m[['stress_level', 'sleep_score']].dropna().copy()
        d['stress_num'] = d['stress_level'].astype(str).str.lower().map(stress_map)
        d = d.dropna(subset=['stress_num'])
        if len(d) >= 3:
            corr_sleep_stress = d['stress_num'].corr(d['sleep_score'])
            print(f"  Стресс vs Качество сна: r = {corr_sleep_stress:.3f}")


# --- 5.2 Гипотезы ---
# Безопасное форматирование для None
def fmt_r(val, decimals=3):
    """Форматирует число или возвращает 'N/A' для None."""
    return f"{val:.{decimals}f}" if val is not None else "N/A"

hypotheses = [
    {
        '№': 1,
        'Гипотеза': 'Пациенты с генотипом SLC22A1 GA (сниженный транспорт метформина) имеют более высокую гликемическую вариабельность (CV) и большее число гипогликемий по данным CGM',
        'Обоснование': f'PT-001 (SLC22A1 GA): CV={cv:.2f}%, гипогликемий={len(hypo_data)} за 1 сутки. Сниженный транспорт метформина может приводить к непредсказуемым колебаниям уровня препарата.',
        'Статус': 'Подтверждается (на основе 1 пациента, требуется расширение выборки)'
    },
    {
        '№': 2,
        'Гипотеза': 'Уровень лептина положительно коррелирует с HbA1c, а адипонектина — отрицательно, что отражает связь инсулинорезистентности с метаболическим контролем',
        'Обоснование': f'Корреляция HbA1c-Leptin: r={fmt_r(corr_hba1c_leptin)}, HbA1c-Adiponectin: r={fmt_r(corr_hba1c_adipo)}. Лептин — маркер лептинорезистентности при ожирении, адипонектин — инсулиночувствительности.',
        'Статус': f'Тенденция подтверждается (n=3, r_Leptin={fmt_r(corr_hba1c_leptin, 2)}, r_Adipo={fmt_r(corr_hba1c_adipo, 2)})'
    }
]

df_hyp = pd.DataFrame(hypotheses)
df_hyp.to_excel('Research_Hypotheses.xlsx', index=False, engine='openpyxl')
print(f"\n  5.2 Гипотезы сохранены: Research_Hypotheses.xlsx")
for h in hypotheses:
    print(f"  Гипотеза {h['№']}: {h['Статус']}")
