# import math
# import os
# from typing import List, Tuple, Optional

# # Попытка импорта scipy для расчёта коэффициента Стьюдента
# try:
#     from scipy import stats
#     SCIPY_AVAILABLE = True
# except ImportError:
#     SCIPY_AVAILABLE = False


# # ------------------------------------------------------------
# # Класс DataParser: разбор файла с данными
# # ------------------------------------------------------------
# class DataParser:
#     @staticmethod
#     def parse_number(s: str) -> Optional[float]:
#         s = s.strip().replace(',', '.')
#         try:
#             return float(s)
#         except ValueError:
#             return None

#     @staticmethod
#     def parse_line(line: str) -> List[float]:
#         parts = line.replace(';', ' ').replace('\t', ' ').split()
#         nums = []
#         for p in parts:
#             num = DataParser.parse_number(p)
#             if num is not None:
#                 nums.append(num)
#         return nums

#     @staticmethod
#     def parse_file(filename: str):
#         """
#         Возвращает: list[load] -> list of tuples (w1, w2, T_pr)
#         Формат файла:
#         --table[num_loads, num_meas]
#         w1 w2 T_pr
#         w1 w2 T_pr
#         ...
#         """
#         if not os.path.exists(filename):
#             return None

#         with open(filename, 'r', encoding='utf-8') as f:
#             lines = [line.strip() for line in f]

#         data = []
#         i = 0
#         n_lines = len(lines)

#         while i < n_lines:
#             line = lines[i]
#             if not line:
#                 i += 1
#                 continue

#             if line.startswith('--table'):
#                 bracket = line.find('[')
#                 if bracket != -1 and line.endswith(']'):
#                     params = line[bracket+1:-1].split(',')
#                     if len(params) == 2:
#                         num_loads = int(params[0])
#                         num_meas = int(params[1])
#                     else:
#                         print("Неверный формат --table. Ожидается --table[num_loads, num_meas]")
#                         return None

#                 i += 1
#                 for load_idx in range(num_loads):
#                     load_data = []
#                     for meas_idx in range(num_meas):
#                         while i < n_lines and not lines[i]:
#                             i += 1
#                         if i >= n_lines:
#                             break
                        
#                         row_nums = DataParser.parse_line(lines[i])
#                         # Ожидаем 3 числа: w1, w2, T_pr
#                         if len(row_nums) >= 3:
#                             load_data.append((row_nums[-3], row_nums[-2], row_nums[-1]))
#                         i += 1
#                     data.append(load_data)
#             else:
#                 i += 1

#         return data if data else None


# # ------------------------------------------------------------
# # Класс Statistics
# # ------------------------------------------------------------
# class Statistics:
#     @staticmethod
#     def mean(values: List[float]) -> float:
#         return sum(values) / len(values) if values else 0.0


# # ------------------------------------------------------------
# # Класс PhysicsCalculator: формулы для гироскопа (Лаб 1.13)
# # ------------------------------------------------------------
# class PhysicsCalculator:
#     @staticmethod
#     def omega_rad_s(w_rpm: float) -> float:
#         """Перевод об/мин в рад/с"""
#         return w_rpm * 2 * math.pi / 60.0

#     @staticmethod
#     def I_theor(m_flywheel: float, R: float) -> float:
#         """I_теор = (m * R^2) / 2"""
#         return 0.5 * m_flywheel * (R ** 2)

#     @staticmethod
#     def I_exp(A: float, m_load: float, g: float, l: float) -> float:
#         """I_эксп = (A * m * g * l) / (2 * pi)"""
#         return (A * m_load * g * l) / (2 * math.pi)

#     @staticmethod
#     def get_final_error(I_exp_val, A, delta_A, m, delta_m):
#         """
#         Расчет абсолютной и относительной погрешности для I_exp.
#         Учитываем наклон графика (A) и точность весов (m).
#         """
#         # Относительная погрешность (складываем квадраты относительных ошибок)
#         rel_error = math.sqrt((delta_A / A)**2 + (delta_m / m)**2)
        
#         abs_error = rel_error * I_exp_val
#         return abs_error, rel_error * 100


# # ------------------------------------------------------------
# # Класс Regression: МНК для y = A*x
# # ------------------------------------------------------------
# class Regression:
#     @staticmethod
#     def linear_origin(x: List[float], y: List[float]) -> Tuple[float, float]:
#         """
#         Линейная регрессия через начало координат y = A*x.
#         Возвращает (A, sigma_A)
#         """
#         n = len(x)
#         if n < 1:
#             return 0.0, 0.0

#         sum_xy = sum(xi * yi for xi, yi in zip(x, y))
#         sum_xx = sum(xi ** 2 for xi in x)

#         if sum_xx == 0:
#             return 0.0, 0.0

#         A = sum_xy / sum_xx

#         if n > 1:
#             sum_res = sum((yi - A * xi) ** 2 for xi, yi in zip(x, y))
#             sigma_A = math.sqrt(sum_res / ((n - 1) * sum_xx))
#         else:
#             sigma_A = 0.0

#         return A, sigma_A


# # ------------------------------------------------------------
# # Класс ExperimentData
# # ------------------------------------------------------------
# class ExperimentData:
#     def __init__(self):
#         self.data = []           # list[load] -> list of (w1, w2, T_pr)
#         self.masses = []         # Массы нагрузок, кг
#         self.delta_m = 0.001     # Погрешность весов (1 г)
#         # Константы установки 1.13
#         self.m_flywheel = 1.5    # кг
#         self.R_flywheel = 0.125  # м
#         self.l_lever = 0.225     # м
#         self.g = 9.81            # м/с^2
#         self.t_student = 2.13    # для n=5, alpha=0.90 (примерно)

#     def load_from_parser(self, data):
#         self.data = data
#         if data:
#             self.masses = [0.0541, 0.1045, 0.1547]


# # ------------------------------------------------------------
# # Вспомогательные функции для меню
# # ------------------------------------------------------------
# def clear_screen():
#     os.system('cls' if os.name == 'nt' else 'clear')

# def print_menu(data: ExperimentData):
#     print("\n" + "=" * 75)
#     print("   ЛАБОРАТОРНАЯ РАБОТА №1.13: ПРЕЦЕССИЯ ГИРОСКОПА")
#     print("=" * 75)
#     if data.data:
#         print(f"Данные загружены: {len(data.data)} нагрузок")
#     else:
#         print("Данные не загружены.")
#     print("-" * 75)
#     print("1. Загрузить данные из файла")
#     print("2. Вывести исходные таблицы (w1, w2, w_ср, T_пр)")
#     print("3. Рассчитать коэффициент А (МНК) для каждой нагрузки")
#     print("4. Рассчитать I_теор и I_эксп, сравнить результаты")
#     print("5. Ручной ввод параметров установки и масс")
#     print("6. Вывести Таблицу 3 (Результаты косвенных измерений)")
#     print("0. Выход")
#     print("-" * 75)

# def input_float(prompt: str, default: Optional[float] = None) -> float:
#     while True:
#         s = input(prompt).strip()
#         if not s and default is not None:
#             return default
#         try:
#             return float(s.replace(',', '.'))
#         except ValueError:
#             print("Ошибка: введите число.")

# def main():
#     data = ExperimentData()
#     script_dir = os.path.dirname(os.path.abspath(__file__))
    
#     default_file = os.path.join(script_dir, "input.txt")
    
#     if os.path.exists(default_file):
#         parsed = DataParser.parse_file(default_file)
#         if parsed is not None:
#             data.load_from_parser(parsed)
#             print(f"--- Данные найдены и загружены автоматически: {default_file}")
#     else:
#         print(f"--- Файл {default_file} не найден. Используйте пункт 1 меню.")
            
#     while True:
#         print_menu(data)
#         choice = input("Выберите действие: ").strip()

#         if choice == '1':
#             filename = input("Введите имя файла (по умолчанию input.txt): ").strip() or "input.txt"
#             full_path = os.path.join(script_dir, filename)
            
#             parsed = DataParser.parse_file(full_path)
#             if parsed is not None:
#                 data.load_from_parser(parsed)
#                 print(f"Данные успешно загружены из {full_path}")
#             else:
#                 print(f"Не удалось загрузить данные по пути: {full_path}")
#             input("Нажмите Enter для продолжения...")

#         elif choice == '2':
#             if not data.data:
#                 print("Сначала загрузите данные.")
#             else:
#                 for l_idx, load in enumerate(data.data):
#                     m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.0
#                     print(f"\nНагрузка {l_idx+1} (Масса = {m_load:.3f} кг):")
#                     print(" № | w1 (об/мин) | w2 (об/мин) | w_ср (об/мин) | w_ср (рад/с) | T_пр (с)")
#                     print("-" * 68)
#                     for i, (w1, w2, T) in enumerate(load):
#                         w_sr_rpm = (w1 + w2) / 2
#                         w_sr_rad = PhysicsCalculator.omega_rad_s(w_sr_rpm)
#                         print(f"{i+1:2d} | {w1:11.1f} | {w2:11.1f} | {w_sr_rpm:13.1f} | {w_sr_rad:12.3f} | {T:7.2f}")
#             input("Нажмите Enter для продолжения...")

#         elif choice == '3':
#             if not data.data:
#                 print("Сначала загрузите данные.")
#             else:
#                 print("\nМНК: T_пр = A * w_ср (по формулам (8)-(10))")
#                 print("Нагрузка | Масса (кг) |   A (с²/(рад))  |  sigma_A  | delta_A")
#                 print("-" * 65)
#                 for l_idx, load in enumerate(data.data):
#                     m_load = data.masses[l_idx]
                    
#                     w_rad_list = [PhysicsCalculator.omega_rad_s((w1 + w2) / 2) for w1, w2, T in load]
#                     T_list = [T for w1, w2, T in load]
                    
#                     A, sigma_A = Regression.linear_origin(w_rad_list, T_list)
#                     delta_A = 2 * sigma_A 
#                     print(f"   {l_idx+1:2d}    |   {m_load:.3f}    | {A:15.6f} | {sigma_A:9.6f} | {delta_A:7.6f}")
#             input("Нажмите Enter для продолжения...")

#         elif choice == '4':
#             if not data.data:
#                 print("Сначала загрузите данные.")
#             else:
#                 I_teor = PhysicsCalculator.I_theor(data.m_flywheel, data.R_flywheel)
#                 print(f"\nТеоретический момент инерции I_теор = {I_teor:.6f} кг*м²")
#                 print("\nИТОГОВЫЕ РЕЗУЛЬТАТЫ (с учетом погрешностей):")
#                 print("Нагрузка |   I_эксп ± ΔI (кг*м²)   | Ош. % | Отклонение от теор.")
#                 print("-" * 75)
                
#                 for l_idx, load in enumerate(data.data):
#                     m_load = data.masses[l_idx]
#                     w_rad_list = [PhysicsCalculator.omega_rad_s((w1 + w2) / 2) for w1, w2, T in load]
#                     T_list = [T for w1, w2, T in load]
                    
#                     A, sigma_A = Regression.linear_origin(w_rad_list, T_list)
#                     delta_A = 2 * sigma_A 
                    
#                     I_val = PhysicsCalculator.I_exp(A, m_load, data.g, data.l_lever)
#                     delta_I, rel_perc = PhysicsCalculator.get_final_error(I_val, A, delta_A, m_load, data.delta_m)
#                     diff = abs(I_val - I_teor)
                    
#                     print(f"   {l_idx+1:2d}    | {I_val:8.6f} ± {delta_I:8.6f} | {rel_perc:5.2f}% | {diff:10.6f}")
#             input("\nНажмите Enter для продолжения...")
            
#         elif choice == '5':
#             print("\nПараметры установки:")
#             data.m_flywheel = input_float(f"Масса маховика (кг) [{data.m_flywheel}]: ", data.m_flywheel)
#             data.R_flywheel = input_float(f"Радиус маховика (м) [{data.R_flywheel}]: ", data.R_flywheel)
#             data.l_lever = input_float(f"Плечо силы (м) [{data.l_lever}]: ", data.l_lever)
            
#             if data.data:
#                 print("\nМассы подвешенных грузов (m0 + k*m1):")
#                 for i in range(len(data.data)):
#                     data.masses[i] = input_float(f" Масса для нагрузки {i+1} (кг) [{data.masses[i]}]: ", data.masses[i])
#             else:
#                 print("Сначала загрузите данные, чтобы задать массы для нагрузок.")
                
#             input("Нажмите Enter для продолжения...")

#         elif choice == '6':
#             if not data.data:
#                 print("Сначала загрузите данные.")
#             else:
#                 print("\nТаблица 3: Результаты косвенных измерений")
#                 for l_idx, load in enumerate(data.data):
#                     m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.0
#                     print(f"\n--- Нагрузка {l_idx+1} (Масса = {m_load:.4f} кг) ---")
#                     print(" w_ср (c⁻¹) | T_пр (с) | A = T_пр/w_ср (с²)")
#                     print("-" * 45)
#                     for w1, w2, T in load:
#                         w_sr_rpm = (w1 + w2) / 2
#                         w_sr_rad = PhysicsCalculator.omega_rad_s(w_sr_rpm)
#                         A_val = T / w_sr_rad if w_sr_rad != 0 else 0
#                         print(f" {w_sr_rad:9.2f} | {T:8.2f} | {A_val:18.4f}")
#             input("\nНажмите Enter для продолжения...")

#         elif choice == '0':
#             break
#         else:
#             print("Неверный ввод.")

# if __name__ == "__main__":
#     main()

import math
import os
from typing import List, Tuple, Optional

# Попытка импорта scipy
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
        s = s.strip().replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def parse_line(line: str) -> List[float]:
        parts = line.replace(';', ' ').replace('\t', ' ').split()
        nums = []
        for p in parts:
            num = DataParser.parse_number(p)
            if num is not None:
                nums.append(num)
        return nums

    @staticmethod
    def parse_file(filename: str):
        if not os.path.exists(filename):
            return None

        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        data = []
        i = 0
        n_lines = len(lines)

        while i < n_lines:
            line = lines[i]
            if not line:
                i += 1
                continue

            if line.startswith('--table'):
                bracket = line.find('[')
                if bracket != -1 and line.endswith(']'):
                    params = line[bracket+1:-1].split(',')
                    if len(params) == 2:
                        num_loads = int(params[0])
                        num_meas = int(params[1])
                    else:
                        print("Неверный формат --table. Ожидается --table[num_loads, num_meas]")
                        return None

                i += 1
                for load_idx in range(num_loads):
                    load_data = []
                    for meas_idx in range(num_meas):
                        while i < n_lines and not lines[i]:
                            i += 1
                        if i >= n_lines:
                            break
                        
                        row_nums = DataParser.parse_line(lines[i])
                        if len(row_nums) >= 3:
                            load_data.append((row_nums[-3], row_nums[-2], row_nums[-1]))
                        i += 1
                    data.append(load_data)
            else:
                i += 1

        return data if data else None


# ------------------------------------------------------------
# Класс PhysicsCalculator: формулы для гироскопа (Лаб 1.13)
# ------------------------------------------------------------
class PhysicsCalculator:
    @staticmethod
    def omega_rad_s(w_rpm: float) -> float:
        """Перевод об/мин в рад/с"""
        return w_rpm * 2 * math.pi / 60.0

    @staticmethod
    def I_theor(m_flywheel: float, R: float) -> float:
        """I_теор = (m * R^2) / 2"""
        return 0.5 * m_flywheel * (R ** 2)

    @staticmethod
    def I_exp(A: float, m_load: float, g: float, l: float) -> float:
        """I_эксп = (A * m * g * l) / (2 * pi)"""
        return (A * m_load * g * l) / (2 * math.pi)

    @staticmethod
    def get_final_error(I_exp_val, A, delta_A, m, delta_m):
        """Расчет абсолютной и относительной погрешности для I_exp."""
        rel_error = math.sqrt((delta_A / A)**2 + (delta_m / m)**2) if A != 0 and m != 0 else 0
        abs_error = rel_error * I_exp_val
        return abs_error, rel_error * 100


# ------------------------------------------------------------
# Класс Regression: МНК для y = A*x
# ------------------------------------------------------------
class Regression:
    @staticmethod
    def linear_origin(x: List[float], y: List[float]) -> Tuple[float, float]:
        """Линейная регрессия через начало координат y = A*x."""
        n = len(x)
        if n < 1:
            return 0.0, 0.0

        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)

        if sum_xx == 0:
            return 0.0, 0.0

        A = sum_xy / sum_xx

        if n > 1:
            sum_res = sum((yi - A * xi) ** 2 for xi, yi in zip(x, y))
            sigma_A = math.sqrt(sum_res / ((n - 1) * sum_xx))
        else:
            sigma_A = 0.0

        return A, sigma_A


# ------------------------------------------------------------
# Класс ExperimentData
# ------------------------------------------------------------
class ExperimentData:
    def __init__(self):
        self.data = []           
        self.masses = []         
        self.delta_m = 0.0001    # Погрешность весов (0.1 г в кг)
        self.m_flywheel = 1.5    
        self.R_flywheel = 0.125  
        self.l_lever = 0.225     
        self.g = 9.81            
        self.t_student = 2.0     # для n=5, alpha=0.90 

    def load_from_parser(self, data):
        self.data = data
        if data:
            self.masses = [0.0543, 0.1045, 0.1547] 


# ------------------------------------------------------------
# Вспомогательные функции для меню
# ------------------------------------------------------------
def print_menu(data: ExperimentData):
    print("\n" + "=" * 75)
    print("   ЛАБОРАТОРНАЯ РАБОТА №1.13: ПРЕЦЕССИЯ ГИРОСКОПА")
    print("=" * 75)
    if data.data:
        print(f"Данные загружены: {len(data.data)} нагрузок")
    else:
        print("Данные не загружены.")
    print("-" * 75)
    print("1. Загрузить данные из файла")
    print("2. Вывести исходные таблицы (w1, w2, w_ср, T_пр)")
    print("3. Расчет коэффициента А (МНК), момента инерции и погрешностей")
    print("4. Сравнение I_теор и I_эксп")
    print("5. Ручной ввод параметров установки и масс")
    print("6. Вывести Таблицу 3 (Результаты косвенных измерений)")
    print("0. Выход")
    print("-" * 75)

def input_float(prompt: str, default: Optional[float] = None) -> float:
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        try:
            return float(s.replace(',', '.'))
        except ValueError:
            print("Ошибка: введите число.")

def main():
    data = ExperimentData()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    default_file = os.path.join(script_dir, "input.txt")
    
    if os.path.exists(default_file):
        parsed = DataParser.parse_file(default_file)
        if parsed is not None:
            data.load_from_parser(parsed)
            print(f"--- Данные найдены и загружены автоматически: {default_file}")
    else:
        print(f"--- Файл {default_file} не найден. Используйте пункт 1 меню.")
            
    while True:
        print_menu(data)
        choice = input("Выберите действие: ").strip()

        if choice == '1':
            filename = input("Введите имя файла (по умолчанию input.txt): ").strip() or "input.txt"
            full_path = os.path.join(script_dir, filename)
            
            parsed = DataParser.parse_file(full_path)
            if parsed is not None:
                data.load_from_parser(parsed)
                print(f"Данные успешно загружены из {full_path}")
            else:
                print(f"Не удалось загрузить данные по пути: {full_path}")
            input("Нажмите Enter для продолжения...")

        elif choice == '2':
            if not data.data:
                print("Сначала загрузите данные.")
            else:
                for l_idx, load in enumerate(data.data):
                    m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.0
                    print(f"\nНагрузка {l_idx+1} (Масса = {m_load:.4f} кг):")
                    print(" № | w1 (об/мин) | w2 (об/мин) | w_ср (об/мин) | w_ср (рад/с) | T_пр (с)")
                    print("-" * 68)
                    for i, (w1, w2, T) in enumerate(load):
                        w_sr_rpm = (w1 + w2) / 2
                        w_sr_rad = PhysicsCalculator.omega_rad_s(w_sr_rpm)
                        print(f"{i+1:2d} | {w1:11.1f} | {w2:11.1f} | {w_sr_rpm:13.1f} | {w_sr_rad:12.3f} | {T:7.2f}")
            input("Нажмите Enter для продолжения...")

        elif choice == '3':
            if not data.data:
                print("Сначала загрузите данные.")
            else:
                print("\n" + "*" * 60)
                print("ПОДРОБНЫЙ РАСЧЕТ ДЛЯ КАЖДОЙ НАГРУЗКИ")
                print("*" * 60)
                for l_idx, load in enumerate(data.data):
                    m_load = data.masses[l_idx]
                    
                    w_rad_list = [PhysicsCalculator.omega_rad_s((w1 + w2) / 2) for w1, w2, T in load]
                    T_list = [T for w1, w2, T in load]
                    
                    A, sigma_A = Regression.linear_origin(w_rad_list, T_list)
                    delta_A = data.t_student * sigma_A 
                    
                    I_val = PhysicsCalculator.I_exp(A, m_load, data.g, data.l_lever)
                    delta_I, rel_perc = PhysicsCalculator.get_final_error(I_val, A, delta_A, m_load, data.delta_m)
                    
                    print(f"\n--- НАГРУЗКА {l_idx+1} ---")
                    print(f"Суммарная масса подвешенных грузов m = {m_load:.4f} кг")
                    print(f"Коэффициент (МНК): A = {A:.6f} с²")
                    print(f"Момент инерции (эксп): I_эксп = (A * m * g * l) / (2π) = {I_val:.6f} кг·м²")
                    
                    print("\n1. Расчет погрешностей измерений:")
                    print("   Погрешность коэффициента А:")
                    print(f"   Стандартное отклонение: σ_A = {sigma_A:.6f}")
                    print(f"   ΔA = {data.t_student} · σ_A = {data.t_student} · {sigma_A:.6f} = {delta_A:.6f}")
                    
                    print(f"\n   Относительная погрешность (ε): {rel_perc:.2f}%")
                    print(f"   Погрешность момента инерции ΔI: {delta_I:.6f} кг·м²")
                    
                    print("\n2. Результат:")
                    print(f"   I = ({I_val:.6f} ± {delta_I:.6f}) кг·м²")
                    print("-" * 60)
            input("\nНажмите Enter для продолжения...")

        elif choice == '4':
            if not data.data:
                print("Сначала загрузите данные.")
            else:
                I_teor = PhysicsCalculator.I_theor(data.m_flywheel, data.R_flywheel)
                print(f"\nТеоретический момент инерции I_теор = {I_teor:.6f} кг*м²")
                print("\nИТОГОВЫЕ РЕЗУЛЬТАТЫ (с учетом погрешностей):")
                # Изменены заголовки таблицы: добавлена колонка I_теор
                print("Нагрузка | I_теор (кг*м²) |   I_эксп ± ΔI (кг*м²)   | Ош. % | Отклонение")
                print("-" * 80)
                
                for l_idx, load in enumerate(data.data):
                    m_load = data.masses[l_idx]
                    w_rad_list = [PhysicsCalculator.omega_rad_s((w1 + w2) / 2) for w1, w2, T in load]
                    T_list = [T for w1, w2, T in load]
                    
                    A, sigma_A = Regression.linear_origin(w_rad_list, T_list)
                    delta_A = data.t_student * sigma_A 
                    
                    I_val = PhysicsCalculator.I_exp(A, m_load, data.g, data.l_lever)
                    delta_I, rel_perc = PhysicsCalculator.get_final_error(I_val, A, delta_A, m_load, data.delta_m)
                    diff = abs(I_val - I_teor)
                    
                    # Добавлен вывод I_teor перед I_val
                    print(f"   {l_idx+1:2d}    |   {I_teor:.6f}   | {I_val:8.6f} ± {delta_I:8.6f} | {rel_perc:5.2f}% | {diff:10.6f}")
            input("\nНажмите Enter для продолжения...")
            
        elif choice == '5':
            print("\nПараметры установки:")
            data.m_flywheel = input_float(f"Масса маховика (кг) [{data.m_flywheel}]: ", data.m_flywheel)
            data.R_flywheel = input_float(f"Радиус маховика (м) [{data.R_flywheel}]: ", data.R_flywheel)
            data.l_lever = input_float(f"Плечо силы (м) [{data.l_lever}]: ", data.l_lever)
            
            if data.data:
                print("\nМассы подвешенных грузов (m0 + k*m1):")
                for i in range(len(data.data)):
                    data.masses[i] = input_float(f" Масса для нагрузки {i+1} (кг) [{data.masses[i]}]: ", data.masses[i])
            else:
                print("Сначала загрузите данные, чтобы задать массы для нагрузок.")
                
            input("Нажмите Enter для продолжения...")

        elif choice == '6':
            if not data.data:
                print("Сначала загрузите данные.")
            else:
                print("\nТаблица 3: Результаты косвенных измерений")
                for l_idx, load in enumerate(data.data):
                    m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.0
                    print(f"\n--- Нагрузка {l_idx+1} (Масса = {m_load:.4f} кг) ---")
                    print(" w_ср (c⁻¹) | T_пр (с) | A = T_пр/w_ср (с²)")
                    print("-" * 45)
                    for w1, w2, T in load:
                        w_sr_rpm = (w1 + w2) / 2
                        w_sr_rad = PhysicsCalculator.omega_rad_s(w_sr_rpm)
                        A_val = T / w_sr_rad if w_sr_rad != 0 else 0
                        print(f" {w_sr_rad:9.2f} | {T:8.2f} | {A_val:18.4f}")
            input("\nНажмите Enter для продолжения...")

        elif choice == '0':
            break
        else:
            print("Неверный ввод.")

if __name__ == "__main__":
    main()