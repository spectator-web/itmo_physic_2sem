

import math
import os
import sys
from typing import List, Tuple, Optional
G_CONST = 9.81
N_OSCILLATIONS = 10
I_0_HUB = 8e-3
# Попытка импорта scipy для расчёта коэффициента Стьюдента
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ------------------------------------------------------------
# Класс DataParser: разбор файла с данными
# ------------------------------------------------------------
class DataParser:
    @staticmethod
    def parse_number(s: str) -> Optional[float]:
        """Преобразует строку в число, заменяя запятую на точку."""
        s = s.strip().replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def parse_line(line: str) -> List[float]:
        """Разбивает строку по разделителям (табуляция, пробел, точка с запятой)."""
        parts = line.replace(';', ' ').replace('\t', ' ').split()
        nums = []
        for p in parts:
            num = DataParser.parse_number(p)
            if num is not None:
                nums.append(num)
        return nums

    @staticmethod
    def parse_file(filename: str):
        """Парсит файл со структурой Таблицы 2, Таблицы 3 и констант."""
        if not os.path.exists(filename):
            print(f"Ошибка: файл '{filename}' не найден.")
            return None, None, None

        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        damped_times = []
        periods_times = []
        instr_meas = []
        i = 0
        n_lines = len(lines)

        while i < n_lines:
            line = lines[i]
            if not line:
                i += 1
                continue

            # Обработка Таблицы 2 (Затухание)
            if '--table[3,5]' in line:
                i += 1
                trials = []
                while len(trials) < 3 and i < n_lines:
                    if lines[i]:
                        row_data = DataParser.parse_line(lines[i])
                        if row_data:
                            trials.append(row_data)
                    i += 1
                # Транспонируем: из [попытка][амплитуда] в [амплитуда][попытка]
                if len(trials) == 3:
                    damped_times = [[trials[row][col] for row in range(3)] for col in range(5)]
                continue

            # Обработка Таблицы 3 (Периоды)
            elif '--table[6,3]' in line:
                i += 1
                while len(periods_times) < 6 and i < n_lines:
                    if lines[i]:
                        row_data = DataParser.parse_line(lines[i])
                        if row_data:
                            periods_times.append(row_data)
                    i += 1
                continue

            # Обработка констант после разделителя
            elif line.startswith('---'):
                i += 1
                while i < n_lines:
                    curr_line = lines[i]
                    if not curr_line or curr_line.startswith('---'):
                        i += 1
                        continue
                    parts = curr_line.replace('+-', '±').split('±')
                    if len(parts) == 2:
                        val = DataParser.parse_number(parts[0])
                        err = DataParser.parse_number(parts[1])
                        if val is not None:
                            instr_meas.append((val, err))
                    else:
                        num = DataParser.parse_number(curr_line)
                        if num is not None:
                            instr_meas.append((num, 0.0))
                    i += 1
                break
            i += 1

        return damped_times, periods_times, instr_meas


# ------------------------------------------------------------
# Класс Statistics: статистическая обработка
# ------------------------------------------------------------
class Statistics:
    @staticmethod
    def mean(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def std_dev(values: List[float], ddof: int = 1) -> float:
        n = len(values)
        if n <= ddof:
            return 0.0
        avg = Statistics.mean(values)
        variance = sum((x - avg) ** 2 for x in values) / (n - ddof)
        return math.sqrt(variance)

    @staticmethod
    def sem(values: List[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        return Statistics.std_dev(values) / math.sqrt(n)

    @staticmethod
    def student_error(values: List[float], t_coef: float) -> float:
        return t_coef * Statistics.sem(values)

    @staticmethod
    def total_error(values: List[float], t_coef: float, instr_error: float) -> float:
        rand_err = Statistics.student_error(values, t_coef)
        return math.sqrt(rand_err ** 2 + ((2/3)*instr_error) ** 2)


# ------------------------------------------------------------
# Класс Regression: метод наименьших квадратов
# ------------------------------------------------------------
class Regression:
    @staticmethod
    def linear(x: List[float], y: List[float]) -> Tuple[float, float, float, float]:
        """
        МНК для аппроксимации прямой y = a*x + b.
        Возвращает кортеж: (a, b, delta_a, delta_b), 
        где a - угловой коэффициент, b - свободный член, 
        delta_a и delta_b - их абсолютные погрешности.
        """
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0, 0.0

        sum_x = sum(x)
        sum_y = sum(y)
        sum_x2 = sum(xi**2 for xi in x)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))

        D = n * sum_x2 - sum_x**2
        
        # Защита от деления на ноль, если все x одинаковые
        if D == 0:
            return 0.0, 0.0, 0.0, 0.0

        a = (n * sum_xy - sum_x * sum_y) / D
        b = (sum_y * sum_x2 - sum_x * sum_xy) / D

        # Расчет погрешностей коэффициентов МНК
        if n > 2:
            S_y2 = sum((yi - (a * xi + b))**2 for xi, yi in zip(x, y)) / (n - 2)
            delta_a = math.sqrt(n * S_y2 / D) if D != 0 else 0.0
            delta_b = math.sqrt(sum_x2 * S_y2 / D) if D != 0 else 0.0
        else:
            delta_a, delta_b = 0.0, 0.0

        return a, b, delta_a, delta_b


# ------------------------------------------------------------
# Класс ExperimentData: хранение параметров
# ------------------------------------------------------------
class ExperimentData:
    def __init__(self):
        self.damped_times = []      # [amplitude_idx][trial] -> times
        self.periods_times = []     # [position][trial] -> times of 10 oscillations
        
        # --- ИСХОДНЫЕ ДАННЫЕ УГЛОВ (не загружаются из файла) ---
        self.amplitudes = [25, 20, 15, 10, 5]
        self.A0 = 30 # Начальная амплитуда в градусах

        self.student_coef = 4.3 
        self.instr_error_time = 0.25 # Погрешность секундомера
        
        # Физические параметры установки (по умолчанию)
        self.g = 9.81
        self.m_gr = 0.220           # кг (масса одного груза)
        self.I0 = 0.008             # кг*м^2 (момент инерции крестовины по методичке)
        self.l1 = 0.057             # м
        self.l0 = 0.025             # м
        self.b = 0.040              # м
        
    def load_from_parser(self, damped, periods, instr_meas):
        if damped:
            self.damped_times = damped
        if periods:
            self.periods_times = periods
            
        if instr_meas and len(instr_meas) >= 7:
            self.m_gr = instr_meas[1][0] / 1000.0   
            self.l1 = instr_meas[3][0] / 1000.0     
            self.l0 = instr_meas[4][0] / 1000.0     
            self.b = instr_meas[6][0] / 1000.0      


# ------------------------------------------------------------
# Вспомогательные функции для вычислений 1.05
# ------------------------------------------------------------
def calc_R(data: ExperimentData, mark: int) -> float:
    return data.l1 + (mark - 1) * data.l0 + data.b / 2

def calc_I_gr(data: ExperimentData, mark_side: int) -> float:
    R_up = calc_R(data, 1)
    R_down = calc_R(data, 6)
    R_side = calc_R(data, mark_side)
    return data.m_gr * (R_up**2 + R_down**2 + 2 * R_side**2)

def calc_l_teor(data: ExperimentData) -> float:
    R_up = calc_R(data, 1)
    R_down = calc_R(data, 6)
    return abs(R_down - R_up) / 4


# ------------------------------------------------------------
# Интерфейс
# ------------------------------------------------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    print("\n" + "=" * 75)
    print(" ЛАБОРАТОРНАЯ РАБОТА №1.05: КОЛЕБАНИЯ ФИЗИЧЕСКОГО МАЯТНИКА")
    print("=" * 75)
    print("1. Загрузить данные из файла (input.txt)")
    print("2. Таблица 2 и анализ затухания (вязкое/сухое трение + погрешности)")
    print("3. Таблица 3 (периоды колебаний + погрешности)")
    print("4. Таблица 4 (моменты инерции и приведенная длина)")
    print("5. Расчет МНК для всех данных (Затухание и T^2 от I)")
    print("6. Вывести ВСЕ данные и расчеты (Полный отчет с МНК и погрешностями)")
    print("0. Выход")
    print("-" * 75)

def analyze_damped(data: ExperimentData):
    if not data.damped_times:
        print("\n[!] Данные для затухания не загружены.")
        return
        
    print("\n--- ТАБЛИЦА 2: Затухающие колебания ---")
    print("Амплитуда (°)\t" + "\t".join(str(a) for a in data.amplitudes))
    
    for i in range(3):
        row_str = f"t{i+1}, c \t\t" + "\t".join(f"{data.damped_times[j][i]:.2f}" for j in range(5))
        print(row_str)
        
    t_avgs = [Statistics.mean(data.damped_times[j]) for j in range(5)]
    # Расчет полной погрешности для времени
    t_errs = [Statistics.total_error(data.damped_times[j], data.student_coef, data.instr_error_time) for j in range(5)]
    
    print("t_ср ± Δt, c \t" + "\t".join(f"{t:.2f}±{e:.2f}" for t, e in zip(t_avgs, t_errs)))
    
    # Регрессия: Вязкое трение ( ln(A/A0) = -beta * t )
    y_viscous = [math.log(A / data.A0) for A in data.amplitudes]
    slope_visc, intercept_visc, _, _ = Regression.linear(t_avgs, y_viscous)
    beta = -slope_visc
    tau = 1 / beta if beta != 0 else float('inf')
    
    # Регрессия: Сухое трение ( A = A0 - k*t )
    y_dry = data.amplitudes
    slope_dry, intercept_dry, _, _ = Regression.linear(t_avgs, y_dry)
    
    # Берем T из Таблицы 3 (3-я риска)
    T_val = 1.8  # fallback
    if len(data.periods_times) >= 3:
        T_val = Statistics.mean(data.periods_times[2]) / 10.0
        
    delta_phi_z = - (slope_dry * T_val) / 4 if slope_dry < 0 else 0
    
    # Оценка числа периодов до остановки
    periods_to_stop = data.A0 / (4 * delta_phi_z) if delta_phi_z > 0 else float('inf')

    print("\n--- АНАЛИЗ ТИПА ТРЕНИЯ ---")
    print(f"Период маятника в конфигурации для затухания T ≈ {T_val:.3f} с")
    print(f"Гипотеза ВЯЗКОГО трения [ln(A/A0) = -β*t]:")
    print(f"  Коэф. затухания β = {beta:.5f} с⁻¹")
    print(f"  Время затухания τ = {tau:.2f} с")
    
    print(f"\nГипотеза СУХОГО трения [A = A0 - k*t]:")
    print(f"  Угловой коэфф. k = {slope_dry:.4f} град/с")
    print(f"  Зона застоя Δφ_з = {delta_phi_z:.3f}°")
    print(f"  Оценочное число периодов до полной остановки: N ≈ {math.ceil(periods_to_stop)} колебаний")


def analyze_periods(data: ExperimentData):
    if not data.periods_times:
        print("\n[!] Данные для периодов не загружены.")
        return
        
    print("\n--- ТАБЛИЦА 3: Периоды колебаний (N=10) ---")
    print("Положение\tt1\tt2\tt3\tt_ср ± Δt (с)\tT ± ΔT (с)")
    
    for i, trials in enumerate(data.periods_times):
        t_avg = Statistics.mean(trials)
        t_err = Statistics.total_error(trials, data.student_coef, data.instr_error_time)
        T = t_avg / 10.0
        T_err = t_err / 10.0 # Погрешность периода в 10 раз меньше погрешности 10 колебаний
        trials_str = "\t".join(f"{t:.2f}" for t in trials)
        print(f"{i+1} риска\t\t{trials_str}\t{t_avg:.2f} ± {t_err:.2f}\t{T:.4f} ± {T_err:.4f}")


def analyze_inertia(data: ExperimentData):
    if not data.periods_times:
        print("\n[!] Данные для расчетов не загружены.")
        return
        
    print("\n--- ТАБЛИЦА 4: Моменты инерции и Приведенная длина ---")
    
    R_up = calc_R(data, 1)
    R_down = calc_R(data, 6)
    l_teor = calc_l_teor(data)
    m_total_gr = 4 * data.m_gr
    
    print(f"Константы: R_верх = {R_up:.4f} м, R_ниж = {R_down:.4f} м")
    print(f"l_теор (от грузов) = {l_teor:.4f} м")
    
    print("\nРиски\t\t1\t\t2\t\t3\t\t4\t\t5\t\t6")
    
    R_sides = [calc_R(data, i) for i in range(1, 7)]
    print("R_бок, м\t" + "\t".join(f"{r:.4f}" for r in R_sides))
    
    I_grs = [calc_I_gr(data, i) for i in range(1, 7)]
    print("I_гр, кг·м²\t" + "\t".join(f"{i:.5f}" for i in I_grs))
    
    Is = [igr + data.I0 for igr in I_grs]
    print("I, кг·м²\t" + "\t".join(f"{i:.5f}" for i in Is))
    
    T_vals = [Statistics.mean(row) / 10.0 for row in data.periods_times]
    T2_vals = [T**2 for T in T_vals]
    
    l_pr_exps = [(data.g * T2) / (4 * math.pi**2) for T2 in T2_vals]
    print("l_пр_эксп, м\t" + "\t".join(f"{l:.4f}" for l in l_pr_exps))
    
    l_pr_teors = [I / (m_total_gr * l_teor) for I in Is]
    print("l_пр_теор, м\t" + "\t".join(f"{l:.4f}" for l in l_pr_teors))
    
    print("\n--- ПРОВЕРКА T²(I) И РАСЧЕТ ml ---")
    slope_I, intercept_I, _, _ = Regression.linear(Is, T2_vals)
    
    ml_exp = (4 * math.pi**2) / (data.g * slope_I) if slope_I > 0 else 0
    ml_teor = m_total_gr * l_teor
    
    print(f"Наклон T²(I) k = {slope_I:.4f} с²/кг·м²")
    print(f"Экспериментальное (ml)_эксп = {ml_exp:.5f} кг·м")
    print(f"Теоретическое (ml)_теор = {ml_teor:.5f} кг·м")

# ------------------------------------------------------------
# Новые функции для пунктов 5 и 6
# ------------------------------------------------------------
def analyze_mnk(data: ExperimentData):
    """
    Пункт 5: Вычисление МНК для вязкого трения и моментов инерции.
    Сюда необходимо передать подготовленные массивы X и Y из ваших данных.
    """
    print("\n" + "-" * 50)
    print(" РАСЧЕТ МНК ДЛЯ ВСЕХ ДАННЫХ ")
    print("-" * 50)
    
    if not data.damped_times and not data.periods_times:
        print("[!] Нет загруженных данных для расчёта МНК.")
        return

    # Пример структуры расчета (замените x_data и y_data на реальные массивы из объекта data)
    print("1. МНК для графика затухания (вязкое трение: ln(A) от t):")
    # x_data_damped = [...] # время t
    # y_data_damped = [...] # ln(A0/A)
    # a_damp, b_damp, da_damp, db_damp = Regression.linear(x_data_damped, y_data_damped)
    print("   Коэффициент затухания (beta) = ... +/- ...")
    
    print("\n2. МНК для периодов (T^2 от I):")
    # x_data_inertia = [...] # Моменты инерции I
    # y_data_periods = [...] # T^2
    # a_per, b_per, da_per, db_per = Regression.linear(x_data_inertia, y_data_periods)
    print("   Угловой коэффициент (a) = ... +/- ...")
    print("   (Используется для нахождения произведения m*l)")
    print("-" * 50)

def print_full_report(data: ExperimentData):
    """
    Пункт 6: Вывод всех таблиц и расчетов разом.
    """
    print("\n" + "=" * 75)
    print(" ПОЛНЫЙ ОТЧЕТ (ВСЕ ДАННЫЕ И РАСЧЕТЫ) ")
    print("=" * 75)
    
    analyze_damped(data)
    analyze_periods(data)
    analyze_inertia(data)
    analyze_mnk(data)
    
    print("=" * 75)

def main():
    data = ExperimentData()
    filename = "lab5/input.txt"
    
    if os.path.exists(filename):
        damped, periods, instr_meas = DataParser.parse_file(filename)
        data.load_from_parser(damped, periods, instr_meas)
        print(f"Данные автоматически загружены из '{filename}'")

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == '1':
            damped, periods, instr_meas = DataParser.parse_file(filename)
            data.load_from_parser(damped, periods, instr_meas)
            print("Данные успешно загружены.")
            input("Нажмите Enter для продолжения...")
            
        elif choice == '2':
            analyze_damped(data)
            input("\nНажмите Enter для продолжения...")
            
        elif choice == '3':
            analyze_periods(data)
            input("\nНажмите Enter для продолжения...")
            
        elif choice == '4':
            analyze_inertia(data)
            input("\nНажмите Enter для продолжения...")
        elif choice == '5':
            analyze_mnk(data)
            input("\nНажмите Enter для продолжения...")
                
        elif choice == '6':
            clear_screen()
            print("==== ПОЛНЫЙ ОТЧЕТ ЛАБ 1.05 ====")
            print_full_report(data)
            input("\nНажмите Enter для продолжения...")
            
        elif choice == '0':
            break

if __name__ == "__main__":
    main()