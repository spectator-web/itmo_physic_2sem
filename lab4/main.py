# import math
# import os
# import re
# from typing import List, Tuple, Optional, Dict

# # ------------------------------------------------------------
# # Класс DataParser: умный разбор таблиц по тегам
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
#     def parse_file(filename: str) -> Optional[Dict]:
#         if not os.path.exists(filename):
#             return None

#         data = {'table3_2': [], 'table3_3': [], 'constants': {}}
#         with open(filename, 'r', encoding='utf-8') as f:
#             lines = [line.strip() for line in f if line.strip()]

#         i = 0
#         while i < len(lines):
#             line = lines[i]

#             match_2 = re.match(r'--table\[\s*(\d+)\s*,\s*(\d+)\s*\]', line)
#             match_4 = re.match(r'--table\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', line)

#             if line.startswith('--constants'):
#                 i += 1
#                 while i < len(lines) and not lines[i].startswith('--'):
#                     part = lines[i].split('=')
#                     if len(part) == 2:
#                         key = part[0].strip()
#                         val_nums = DataParser.parse_line(part[1])
#                         if val_nums:
#                             data['constants'][key] = val_nums[0]
#                     i += 1
#                 continue

#             if match_4:
#                 plates, heights, exps, times = map(int, match_4.groups())
#                 i += 1
#                 for p in range(plates):
#                     if i >= len(lines) or lines[i].startswith('--'): 
#                         break
                    
#                     nums = DataParser.parse_line(lines[i])
#                     i += 1
                    
#                     # Умный разбор первой строки блока
#                     # Идеальный формат: h, h', t1, t2 (len=4)
#                     # Формат с пластинами: N, h, h', t1, t2 (len=5)
#                     # Формат скопированный (с мусором): N, h, h', exp_num, t1, t2 (len=6)
                    
#                     if len(nums) >= 6:
#                         h = nums[-5]        # 0.212
#                         h_prime = nums[-4]  # 0.194
#                         t1 = nums[-2]       # 1.0
#                         t2 = nums[-1]       # 5.0
#                     elif len(nums) == 5:
#                         h = nums[1]
#                         h_prime = nums[2]
#                         t1 = nums[3]
#                         t2 = nums[4]
#                     elif len(nums) >= 4:
#                         h = nums[-4]
#                         h_prime = nums[-3]
#                         t1 = nums[-2]
#                         t2 = nums[-1]
#                     else:
#                         h = h_prime = t1 = t2 = 0.0
                    
#                     data['table3_3'].append((p+1, h, h_prime, t1, t2))
                    
#                     # Читаем оставшиеся опыты (строки со 2 по 5)
#                     for e in range(exps - 1):
#                         if i >= len(lines) or lines[i].startswith('--'): 
#                             break
#                         nums = DataParser.parse_line(lines[i])
#                         i += 1
                        
#                         # Здесь берем просто 2 последних числа (t1 и t2)
#                         t_vals = nums[-times:] if len(nums) >= times else [0.0] * times
#                         t1 = t_vals[0] if times > 0 else 0.0
#                         t2 = t_vals[1] if times > 1 else 0.0
                        
#                         data['table3_3'].append((p+1, h, h_prime, t1, t2))
#                 continue

#             elif match_2:
#                 rows, cols = map(int, match_2.groups())
#                 i += 1
#                 for r in range(rows):
#                     if i >= len(lines) or lines[i].startswith('--'): 
#                         break
#                     nums = DataParser.parse_line(lines[i])
#                     i += 1
                    
#                     vals = nums[-cols:] if len(nums) >= cols else [0.0] * cols
#                     data['table3_2'].append(tuple(vals))
#                 continue

#             i += 1

#         return data if (data['table3_2'] or data['table3_3'] or data['constants']) else None

# # ------------------------------------------------------------
# # Класс PhysicsCalculator
# # ------------------------------------------------------------
# class PhysicsCalculator:
#     @staticmethod
#     def get_task1_values(x1, x2, t1, t2):
#         Y = x2 - x1
#         Z = (t2**2 - t1**2) / 2.0
#         return Y, Z

#     @staticmethod
#     def get_task1_errors(x1, x2, t1, t2, delta_x_rail, delta_t_in):
#         # Используется погрешность линейки-планки (рельса)
#         delta_Y = math.sqrt(2) * delta_x_rail
#         delta_Z = delta_t_in * math.sqrt(t1**2 + t2**2)
#         return delta_Y, delta_Z

#     @staticmethod
#     def calc_sin_alpha(h0, h, h0_prime, h_prime, X, X_prime):
#         if X_prime == X: return 0.0
#         return abs((h0 - h) - (h0_prime - h_prime)) / abs(X_prime - X)

#     @staticmethod
#     def calc_mean_and_error(values: List[float], delta_in: float, t_student: float):
#         n = len(values)
#         if n == 0: return 0.0, 0.0, 0.0
#         mean_val = sum(values) / n
#         S = math.sqrt(sum((v - mean_val)**2 for v in values) / (n * (n - 1))) if n > 1 else 0.0
#         delta_rand = t_student * S
#         delta_total = math.sqrt(delta_rand**2 + ((2.0/3.0) * delta_in)**2)
#         return mean_val, delta_total, (delta_total / mean_val * 100 if mean_val != 0 else 0)

# # ------------------------------------------------------------
# # Класс Regression: МНК
# # ------------------------------------------------------------
# class Regression:
#     @staticmethod
#     def linear_origin(x: List[float], y: List[float]) -> Tuple[float, float]:
#         n = len(x)
#         if n < 1: return 0.0, 0.0
#         sum_xy = sum(xi * yi for xi, yi in zip(x, y))
#         sum_xx = sum(xi ** 2 for xi in x)
#         if sum_xx == 0: return 0.0, 0.0
        
#         a = sum_xy / sum_xx
#         sigma_a = math.sqrt(sum((yi - a * xi) ** 2 for xi, yi in zip(x, y)) / ((n - 1) * sum_xx)) if n > 1 else 0.0
#         return a, sigma_a

#     @staticmethod
#     def linear_full(x: List[float], y: List[float]) -> Tuple[float, float, float]:
#         n = len(x)
#         if n < 2: return 0.0, 0.0, 0.0
#         sum_x, sum_y = sum(x), sum(y)
#         sum_xy = sum(xi * yi for xi, yi in zip(x, y))
#         sum_xx = sum(xi ** 2 for xi in x)
        
#         D = sum_xx - (sum_x**2) / n
#         if D == 0: return 0.0, 0.0, 0.0
        
#         B = (sum_xy - (sum_y * sum_x) / n) / D
#         A = (sum_y - B * sum_x) / n
#         S_B = math.sqrt(sum((yi - (A + B * xi))**2 for xi, yi in zip(x, y)) / (D * (n - 2))) if n > 2 else 0.0
        
#         return A, B, S_B

# # ------------------------------------------------------------
# # Константы и Хранилище данных
# # ------------------------------------------------------------
# class ExperimentData:
#     def __init__(self):
#         self.t3_2 = [] 
#         self.t3_3 = []
        
#         # Координаты (Таблица 3.1)
#         self.X = 0.22          
#         self.X_prime = 1.0     
#         self.h0 = 0.194        
#         self.h0_prime = 0.195  
        
#         # Инструментальные погрешности (половина цены деления по умолчанию)
#         self.delta_x_rail = 0.05   # Планка: цена деления 0.1 м -> погр. 0.05 м
#         self.delta_h_tri = 0.0005  # Угольник: цена деления 0.1 см -> погр. 0.0005 м
#         self.delta_t_in = 0.05     # ПКЦ: цена деления 0.1 с -> погр. 0.05 с
        
#         self.t_student = 2.78  
#         self.g_tabl = 9.82     

#     def load_from_parser(self, data):
#         if not data: return
#         self.t3_2 = data.get('table3_2', self.t3_2)
#         self.t3_3 = data.get('table3_3', self.t3_3)
        
#         consts = data.get('constants', {})
#         self.X = consts.get('X', self.X)
#         self.X_prime = consts.get('X_prime', self.X_prime)
#         self.h0 = consts.get('h0', self.h0)
#         self.h0_prime = consts.get('h0_prime', self.h0_prime)
#         self.delta_x_rail = consts.get('delta_x_rail', self.delta_x_rail)
#         self.delta_h_tri = consts.get('delta_h_tri', self.delta_h_tri)
#         self.delta_t_in = consts.get('delta_t_in', self.delta_t_in)

# # ------------------------------------------------------------
# # Вспомогательные функции UI
# # ------------------------------------------------------------
# def print_menu(data: ExperimentData):
#     print("\n" + "=" * 75)
#     print("   ЛАБОРАТОРНАЯ РАБОТА №1.02: СКОЛЬЖЕНИЕ ТЕЛЕЖКИ ПО НАКЛОННОЙ ПЛОСКОСТИ")
#     print("=" * 75)
#     print(f" Данные: Задание 1 ({len(data.t3_2)} строк) | Задание 2 ({len(data.t3_3)} строк)")
#     print("-" * 75)
#     print("1. Загрузить/Перезагрузить данные из файла (input.txt)")
#     print("2. Расчет Задания 1 (Таблица 1 Приложения + a)")
#     print("3. Расчет Задания 2 (Таблица 2 Приложения + g)")
#     print("4. Ручной ввод констант и погрешностей приборов")
#     print("0. Выход")
#     print("-" * 75)

# def input_float(prompt: str, default: Optional[float] = None) -> float:
#     while True:
#         s = input(prompt).strip()
#         if not s and default is not None: return default
#         try: return float(s.replace(',', '.'))
#         except ValueError: print("Ошибка: введите число.")

# def process_task_1(data: ExperimentData):
#     if not data.t3_2:
#         print("Нет данных для Задания 1.")
#         return
        
#     print("\n" + "*" * 65)
#     print("ЗАДАНИЕ 1. ТАБЛИЦА 1 (Приложение) и МНК")
#     print("*" * 65)
#     print("  № |   Y, м   | ΔY, м | δY, % |  Z, с²  | ΔZ, с² | δZ, %")
#     print("-" * 65)
    
#     Y_list, Z_list = [], []
#     for i, row in enumerate(data.t3_2):
#         x1, x2, t1, t2 = row[0], row[1], row[2], row[3]
#         Y, Z = PhysicsCalculator.get_task1_values(x1, x2, t1, t2)
#         delta_Y, delta_Z = PhysicsCalculator.get_task1_errors(x1, x2, t1, t2, data.delta_x_rail, data.delta_t_in)
        
#         delta_Y_rel = (delta_Y / Y * 100) if Y != 0 else 0
#         delta_Z_rel = (delta_Z / Z * 100) if Z != 0 else 0
        
#         Y_list.append(Y)
#         Z_list.append(Z)
#         print(f"{i+1:3d} | {Y:8.4f} | {delta_Y:5.4f} | {delta_Y_rel:5.1f} | {Z:7.4f} | {delta_Z:6.4f} | {delta_Z_rel:5.1f}")
        
#     a, S_a = Regression.linear_origin(Z_list, Y_list)
#     delta_a = 2 * S_a
#     delta_a_rel = (delta_a / a * 100) if a != 0 else 0
    
#     print("-" * 65)
#     print(f"Итог: a = ({a:.4f} ± {delta_a:.4f}) м/с² (δa = {delta_a_rel:.2f}%)")

# def process_task_2(data: ExperimentData):
#     if not data.t3_3:
#         print("Нет данных для Задания 2.")
#         return
        
#     groups = {}
#     for row in data.t3_3:
#         N, h, h_prime, t1, t2 = row
#         if N not in groups: groups[N] = {'h': h, 'h_prime': h_prime, 't1': [], 't2': []}
#         groups[N]['t1'].append(t1)
#         groups[N]['t2'].append(t2)
        
#     print("\n" + "*" * 105)
#     print("ЗАДАНИЕ 2. ТАБЛИЦА 2 (Приложение) и расчет g")
#     print("*" * 105)
#     print(" N |  sin α  | <t1>,c | Δt1,c | δt1,% | <t2>,c | Δt2,c | δt2,% | <a>,м/с² | Δ<a>,м/с² | δ<a>,%")
#     print("-" * 105)
    
#     sin_alpha_list, a_mean_list = [], []
#     x1, x2 = 0.15, 1.10
    
#     for N, vals in groups.items():
#         h, h_prime = vals['h'], vals['h_prime']
#         sin_a = PhysicsCalculator.calc_sin_alpha(data.h0, h, data.h0_prime, h_prime, data.X, data.X_prime)
        
#         t1_mean, dt1, rel_dt1 = PhysicsCalculator.calc_mean_and_error(vals['t1'], data.delta_t_in, data.t_student)
#         t2_mean, dt2, rel_dt2 = PhysicsCalculator.calc_mean_and_error(vals['t2'], data.delta_t_in, data.t_student)
        
#         a_mean = 2 * (x2 - x1) / (t2_mean**2 - t1_mean**2)
#         # В формуле 22 используется погрешность линейки-планки (delta_x_rail)
#         term1 = 2 * (data.delta_x_rail**2) / ((x2 - x1)**2)
#         term2 = 4 * ((t1_mean * dt1)**2 + (t2_mean * dt2)**2) / ((t2_mean**2 - t1_mean**2)**2)
#         da = a_mean * math.sqrt(term1 + term2)
#         rel_da = (da / a_mean * 100) if a_mean != 0 else 0
        
#         sin_alpha_list.append(sin_a)
#         a_mean_list.append(a_mean)
#         print(f" {int(N):1d} | {sin_a:7.5f} | {t1_mean:6.3f} | {dt1:5.3f} | {rel_dt1:5.1f} | {t2_mean:6.3f} | {dt2:5.3f} | {rel_dt2:5.1f} | {a_mean:8.4f} | {da:9.4f} | {rel_da:6.1f}")
        
#     A, g_exp, S_g = Regression.linear_full(sin_alpha_list, a_mean_list)
#     delta_g = 2 * S_g
    
#     print("-" * 105)
#     print(f"Экспериментальное g: ({g_exp:.4f} ± {delta_g:.4f}) м/с²")
#     print(f"Отклонение от табличного ({data.g_tabl}): {abs(g_exp - data.g_tabl):.4f} м/с² ({(abs(g_exp - data.g_tabl)/data.g_tabl*100):.2f}%)")


# def main():
#     data = ExperimentData()
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     default_file = os.path.join(script_dir, "input.txt")
    
#     if os.path.exists(default_file):
#         parsed = DataParser.parse_file(default_file)
#         if parsed:
#             data.load_from_parser(parsed)
#             print(f"--- Данные автоматически загружены из {default_file} ---")
    
#     while True:
#         print_menu(data)
#         choice = input("Выберите действие: ").strip()

#         if choice == '1':
#             filename = input("Введите имя файла (по умолчанию input.txt): ").strip() or "input.txt"
#             parsed = DataParser.parse_file(os.path.join(script_dir, filename))
#             if parsed:
#                 data.load_from_parser(parsed)
#                 print("Данные успешно загружены.")
#             else:
#                 print("Не удалось загрузить данные.")
#             input("Нажмите Enter...")

#         elif choice == '2':
#             process_task_1(data)
#             input("Нажмите Enter...")

#         elif choice == '3':
#             process_task_2(data)
#             input("Нажмите Enter...")

#         elif choice == '4':
#             print("\nИзменение констант и погрешностей приборов:")
#             data.X = input_float(f"X (Координата h0) м [{data.X}]: ", data.X)
#             data.X_prime = input_float(f"X' (Координата h0') м [{data.X_prime}]: ", data.X_prime)
#             data.h0 = input_float(f"h0 (м) [{data.h0}]: ", data.h0)
#             data.h0_prime = input_float(f"h0' (м) [{data.h0_prime}]: ", data.h0_prime)
#             print("\nПогрешности приборов (по умолчанию - половина цены деления):")
#             data.delta_x_rail = input_float(f"Линейка-планка (Δx_rail) м [{data.delta_x_rail}]: ", data.delta_x_rail)
#             data.delta_h_tri = input_float(f"Угольник (Δh_tri) м [{data.delta_h_tri}]: ", data.delta_h_tri)
#             data.delta_t_in = input_float(f"Секундомер ПКЦ (Δt_in) с [{data.delta_t_in}]: ", data.delta_t_in)
#             input("Нажмите Enter...")

#         elif choice == '0':
#             break

# if __name__ == "__main__":
#     main()

import math
import os
import re
from typing import List, Tuple, Optional, Dict

# ------------------------------------------------------------
# Класс DataParser: умный разбор таблиц по тегам
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
    def parse_file(filename: str) -> Optional[Dict]:
        if not os.path.exists(filename):
            return None

        data = {'table3_2': [], 'table3_3': [], 'constants': {}}
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            match_2 = re.match(r'--table\[\s*(\d+)\s*,\s*(\d+)\s*\]', line)
            match_4 = re.match(r'--table\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', line)

            if line.startswith('--constants'):
                i += 1
                while i < len(lines) and not lines[i].startswith('--'):
                    part = lines[i].split('=')
                    if len(part) == 2:
                        key = part[0].strip()
                        val_nums = DataParser.parse_line(part[1])
                        if val_nums:
                            data['constants'][key] = val_nums[0]
                    i += 1
                continue

            if match_4:
                plates, heights, exps, times = map(int, match_4.groups())
                i += 1
                for p in range(plates):
                    if i >= len(lines) or lines[i].startswith('--'): 
                        break
                    
                    nums = DataParser.parse_line(lines[i])
                    i += 1
                    
                    if len(nums) >= 6:
                        h = nums[-5]
                        h_prime = nums[-4]
                        t1 = nums[-2]
                        t2 = nums[-1]
                    elif len(nums) == 5:
                        h = nums[1]
                        h_prime = nums[2]
                        t1 = nums[3]
                        t2 = nums[4]
                    elif len(nums) >= 4:
                        h = nums[-4]
                        h_prime = nums[-3]
                        t1 = nums[-2]
                        t2 = nums[-1]
                    else:
                        h = h_prime = t1 = t2 = 0.0
                    
                    data['table3_3'].append((p+1, h, h_prime, t1, t2))
                    
                    for e in range(exps - 1):
                        if i >= len(lines) or lines[i].startswith('--'): 
                            break
                        nums = DataParser.parse_line(lines[i])
                        i += 1
                        
                        t_vals = nums[-times:] if len(nums) >= times else [0.0] * times
                        t1 = t_vals[0] if times > 0 else 0.0
                        t2 = t_vals[1] if times > 1 else 0.0
                        
                        data['table3_3'].append((p+1, h, h_prime, t1, t2))
                continue

            elif match_2:
                rows, cols = map(int, match_2.groups())
                i += 1
                for r in range(rows):
                    if i >= len(lines) or lines[i].startswith('--'): 
                        break
                    nums = DataParser.parse_line(lines[i])
                    i += 1
                    
                    vals = nums[-cols:] if len(nums) >= cols else [0.0] * cols
                    data['table3_2'].append(tuple(vals))
                continue

            i += 1

        return data if (data['table3_2'] or data['table3_3'] or data['constants']) else None

# ------------------------------------------------------------
# Класс PhysicsCalculator
# ------------------------------------------------------------
class PhysicsCalculator:
    @staticmethod
    def get_task1_values(x1, x2, t1, t2):
        Y = x2 - x1
        Z = (t2**2 - t1**2) / 2.0
        return Y, Z

    @staticmethod
    def get_task1_errors(x1, x2, t1, t2, delta_x_rail, delta_t_in):
        delta_Y = math.sqrt(2) * delta_x_rail
        delta_Z = delta_t_in * math.sqrt(t1**2 + t2**2)
        return delta_Y, delta_Z

    @staticmethod
    def calc_sin_alpha(h0, h, h0_prime, h_prime, X, X_prime):
        if X_prime == X: return 0.0
        return abs((h0 - h) - (h0_prime - h_prime)) / abs(X_prime - X)

    @staticmethod
    def calc_mean_and_error(values: List[float], delta_in: float, t_student: float):
        n = len(values)
        if n == 0: return 0.0, 0.0, 0.0
        mean_val = sum(values) / n
        S = math.sqrt(sum((v - mean_val)**2 for v in values) / (n * (n - 1))) if n > 1 else 0.0
        delta_rand = t_student * S
        delta_total = math.sqrt(delta_rand**2 + ((2.0/3.0) * delta_in)**2)
        return mean_val, delta_total, (delta_total / mean_val * 100 if mean_val != 0 else 0), S, delta_rand

# ------------------------------------------------------------
# Класс Regression: МНК
# ------------------------------------------------------------
class Regression:
    @staticmethod
    def linear_origin(x: List[float], y: List[float]) -> Tuple[float, float]:
        n = len(x)
        if n < 1: return 0.0, 0.0
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)
        if sum_xx == 0: return 0.0, 0.0
        
        a = sum_xy / sum_xx
        sigma_a = math.sqrt(sum((yi - a * xi) ** 2 for xi, yi in zip(x, y)) / ((n - 1) * sum_xx)) if n > 1 else 0.0
        return a, sigma_a

    @staticmethod
    def linear_full(x: List[float], y: List[float]) -> Tuple[float, float, float]:
        n = len(x)
        if n < 2: return 0.0, 0.0, 0.0
        sum_x, sum_y = sum(x), sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)
        
        D = sum_xx - (sum_x**2) / n
        if D == 0: return 0.0, 0.0, 0.0
        
        B = (sum_xy - (sum_y * sum_x) / n) / D
        A = (sum_y - B * sum_x) / n
        S_B = math.sqrt(sum((yi - (A + B * xi))**2 for xi, yi in zip(x, y)) / (D * (n - 2))) if n > 2 else 0.0
        
        return A, B, S_B

# ------------------------------------------------------------
# Константы и Хранилище данных
# ------------------------------------------------------------
class ExperimentData:
    def __init__(self):
        self.t3_2 = [] 
        self.t3_3 = []
        
        self.X = 0.22          
        self.X_prime = 1.0     
        self.h0 = 0.194        
        self.h0_prime = 0.195  
        
        self.delta_x_rail = 0.05   
        self.delta_h_tri = 0.0005  
        self.delta_t_in = 0.05     
        
        self.t_student = 2.78  
        self.g_tabl = 9.82     

    def load_from_parser(self, data):
        if not data: return
        self.t3_2 = data.get('table3_2', self.t3_2)
        self.t3_3 = data.get('table3_3', self.t3_3)
        
        consts = data.get('constants', {})
        self.X = consts.get('X', self.X)
        self.X_prime = consts.get('X_prime', self.X_prime)
        self.h0 = consts.get('h0', self.h0)
        self.h0_prime = consts.get('h0_prime', self.h0_prime)
        self.delta_x_rail = consts.get('delta_x_rail', self.delta_x_rail)
        self.delta_h_tri = consts.get('delta_h_tri', self.delta_h_tri)
        self.delta_t_in = consts.get('delta_t_in', self.delta_t_in)

# ------------------------------------------------------------
# Вспомогательные функции UI
# ------------------------------------------------------------
def print_menu(data: ExperimentData):
    print("\n" + "=" * 75)
    print("   ЛАБОРАТОРНАЯ РАБОТА №1.02: СКОЛЬЖЕНИЕ ТЕЛЕЖКИ ПО НАКЛОННОЙ ПЛОСКОСТИ")
    print("=" * 75)
    print(f" Данные: Задание 1 ({len(data.t3_2)} строк) | Задание 2 ({len(data.t3_3)} строк)")
    print("-" * 75)
    print("1. Загрузить/Перезагрузить данные из файла (input.txt)")
    print("2. Расчет Задания 1 (Таблица 1 Приложения + a)")
    print("3. Расчет Задания 2 (Таблица 2 Приложения + g)")
    print("4. Ручной ввод констант и погрешностей приборов")
    print("5. Вывести все исходные данные и параметры")
    print("6. Пример расчета погрешностей (прямые и косвенные)")
    print("0. Выход")
    print("-" * 75)

def input_float(prompt: str, default: Optional[float] = None) -> float:
    while True:
        s = input(prompt).strip()
        if not s and default is not None: return default
        try: return float(s.replace(',', '.'))
        except ValueError: print("Ошибка: введите число.")

def process_task_1(data: ExperimentData):
    if not data.t3_2:
        print("Нет данных для Задания 1.")
        return
        
    print("\n" + "*" * 65)
    print("ЗАДАНИЕ 1. ТАБЛИЦА 1 (Приложение) и МНК")
    print("*" * 65)
    print("  № |   Y, м   | ΔY, м | δY, % |  Z, с²  | ΔZ, с² | δZ, %")
    print("-" * 65)
    
    Y_list, Z_list = [], []
    for i, row in enumerate(data.t3_2):
        x1, x2, t1, t2 = row[0], row[1], row[2], row[3]
        Y, Z = PhysicsCalculator.get_task1_values(x1, x2, t1, t2)
        delta_Y, delta_Z = PhysicsCalculator.get_task1_errors(x1, x2, t1, t2, data.delta_x_rail, data.delta_t_in)
        
        delta_Y_rel = (delta_Y / Y * 100) if Y != 0 else 0
        delta_Z_rel = (delta_Z / Z * 100) if Z != 0 else 0
        
        Y_list.append(Y)
        Z_list.append(Z)
        print(f"{i+1:3d} | {Y:8.4f} | {delta_Y:5.4f} | {delta_Y_rel:5.1f} | {Z:7.4f} | {delta_Z:6.4f} | {delta_Z_rel:5.1f}")
        
    a, S_a = Regression.linear_origin(Z_list, Y_list)
    delta_a = 2 * S_a
    delta_a_rel = (delta_a / a * 100) if a != 0 else 0
    
    print("-" * 65)
    print(f"Итог: a = ({a:.4f} ± {delta_a:.4f}) м/с² (δa = {delta_a_rel:.2f}%)")

def process_task_2(data: ExperimentData):
    if not data.t3_3:
        print("Нет данных для Задания 2.")
        return
        
    groups = {}
    for row in data.t3_3:
        N, h, h_prime, t1, t2 = row
        if N not in groups: groups[N] = {'h': h, 'h_prime': h_prime, 't1': [], 't2': []}
        groups[N]['t1'].append(t1)
        groups[N]['t2'].append(t2)
        
    print("\n" + "*" * 105)
    print("ЗАДАНИЕ 2. ТАБЛИЦА 2 (Приложение) и расчет g")
    print("*" * 105)
    print(" N |  sin α  | <t1>,c | Δt1,c | δt1,% | <t2>,c | Δt2,c | δt2,% | <a>,м/с² | Δ<a>,м/с² | δ<a>,%")
    print("-" * 105)
    
    sin_alpha_list, a_mean_list = [], []
    x1, x2 = 0.15, 1.10
    
    for N, vals in groups.items():
        h, h_prime = vals['h'], vals['h_prime']
        sin_a = PhysicsCalculator.calc_sin_alpha(data.h0, h, data.h0_prime, h_prime, data.X, data.X_prime)
        
        t1_mean, dt1, rel_dt1, _, _ = PhysicsCalculator.calc_mean_and_error(vals['t1'], data.delta_t_in, data.t_student)
        t2_mean, dt2, rel_dt2, _, _ = PhysicsCalculator.calc_mean_and_error(vals['t2'], data.delta_t_in, data.t_student)
        
        a_mean = 2 * (x2 - x1) / (t2_mean**2 - t1_mean**2)
        term1 = 2 * (data.delta_x_rail**2) / ((x2 - x1)**2)
        term2 = 4 * ((t1_mean * dt1)**2 + (t2_mean * dt2)**2) / ((t2_mean**2 - t1_mean**2)**2)
        da = a_mean * math.sqrt(term1 + term2)
        rel_da = (da / a_mean * 100) if a_mean != 0 else 0
        
        sin_alpha_list.append(sin_a)
        a_mean_list.append(a_mean)
        print(f" {int(N):1d} | {sin_a:7.5f} | {t1_mean:6.3f} | {dt1:5.3f} | {rel_dt1:5.1f} | {t2_mean:6.3f} | {dt2:5.3f} | {rel_dt2:5.1f} | {a_mean:8.4f} | {da:9.4f} | {rel_da:6.1f}")
        
    A, g_exp, S_g = Regression.linear_full(sin_alpha_list, a_mean_list)
    delta_g = 2 * S_g
    
    print("-" * 105)
    print(f"Экспериментальное g: ({g_exp:.4f} ± {delta_g:.4f}) м/с²")
    print(f"Отклонение от табличного ({data.g_tabl}): {abs(g_exp - data.g_tabl):.4f} м/с² ({(abs(g_exp - data.g_tabl)/data.g_tabl*100):.2f}%)")

def print_all_info(data: ExperimentData):
    print("\n" + "=" * 50)
    print("   ВСЕ ИСХОДНЫЕ ДАННЫЕ И ПАРАМЕТРЫ")
    print("=" * 50)
    print("\n--- Глобальные константы ---")
    print(f"Коэффициент Стьюдента (t_student): {data.t_student}")
    print(f"Табличное g (g_tabl): {data.g_tabl} м/с²")
    print(f"X (Координата h0): {data.X} м")
    print(f"X' (Координата h0'): {data.X_prime} м")
    print(f"h0: {data.h0} м")
    print(f"h0': {data.h0_prime} м")
    
    print("\n--- Инструментальные погрешности ---")
    print(f"Линейка-планка (Δx_rail): {data.delta_x_rail} м")
    print(f"Угольник (Δh_tri): {data.delta_h_tri} м")
    print(f"Секундомер ПКЦ (Δt_in): {data.delta_t_in} с")

    print("\n--- Считанные данные Таблицы 3.2 (Задание 1) ---")
    if not data.t3_2:
        print("Данные не загружены.")
    else:
        print(" № |  x1  |  x2  |  t1  |  t2  ")
        print("-" * 35)
        for i, row in enumerate(data.t3_2):
            print(f"{i+1:2d} | {row[0]:4.2f} | {row[1]:4.2f} | {row[2]:4.2f} | {row[3]:4.2f}")

    print("\n--- Считанные данные Таблицы 3.3 (Задание 2) ---")
    if not data.t3_3:
        print("Данные не загружены.")
    else:
        print(" № пл |   h   |   h'  |  t1  |  t2  ")
        print("-" * 40)
        for row in data.t3_3:
            print(f"  {int(row[0]):2d}  | {row[1]:5.3f} | {row[2]:5.3f} | {row[3]:4.2f} | {row[4]:4.2f}")

def print_error_examples(data: ExperimentData):
    print("\n" + "=" * 60)
    print("   ПРИМЕР РАСЧЕТА ПОГРЕШНОСТЕЙ ДЛЯ ОТЧЕТА")
    print("=" * 60)

    if data.t3_2:
        print("\n--- ЗАДАНИЕ 1 (Однократные измерения) ---")
        x1, x2, t1, t2 = data.t3_2[0]
        Y, Z = PhysicsCalculator.get_task1_values(x1, x2, t1, t2)
        delta_Y, delta_Z = PhysicsCalculator.get_task1_errors(x1, x2, t1, t2, data.delta_x_rail, data.delta_t_in)
        
        print("1. Прямые погрешности (инструментальные):")
        print(f"   Δx = {data.delta_x_rail} м (Линейка-планка)")
        print(f"   Δt = {data.delta_t_in} с (Секундомер ПКЦ)")
        
        print("\n2. Косвенные погрешности для Y и Z (по формулам 7 и 9):")
        print(f"   Для первой точки: t1 = {t1}, t2 = {t2}, x1 = {x1}, x2 = {x2}")
        print(f"   ΔY = √2 * Δx = 1.41 * {data.delta_x_rail} = {delta_Y:.4f} м")
        print(f"   ΔZ = Δt * √(t1² + t2²) = {data.delta_t_in} * √({t1}² + {t2}²) = {delta_Z:.4f} с²")
    else:
        print("\nЗагрузите данные Задания 1 для просмотра примера.")

    if data.t3_3:
        print("\n--- ЗАДАНИЕ 2 (Многократные измерения) ---")
        groups = {}
        for row in data.t3_3:
            N, h, h_prime, t1, t2 = row
            if N not in groups: groups[N] = {'t1': [], 't2': []}
            groups[N]['t1'].append(t1)
            groups[N]['t2'].append(t2)
        
        first_group_key = list(groups.keys())[0]
        t1_vals = groups[first_group_key]['t1']
        t2_vals = groups[first_group_key]['t2']

        # Расчет для t1
        n = len(t1_vals)
        mean_t1 = sum(t1_vals) / n
        S_t1 = math.sqrt(sum((v - mean_t1)**2 for v in t1_vals) / (n * (n - 1)))
        delta_rand_t1 = data.t_student * S_t1
        delta_tot_t1 = math.sqrt(delta_rand_t1**2 + ((2/3) * data.delta_t_in)**2)

        print("1. Прямые погрешности (многократные измерения для t1 первой пластины):")
        print(f"   Значения: {t1_vals}")
        print(f"   Среднее <t1> = {mean_t1:.3f} с")
        print(f"   СКО S_<t1> = {S_t1:.4f} с")
        print(f"   Случайная погрешность Δ_сл = t_ст * S = {data.t_student} * {S_t1:.4f} = {delta_rand_t1:.4f} с")
        print(f"   Полная погрешность Δt1 = √(Δ_сл² + (2/3 * Δ_ин)²) = √({delta_rand_t1:.4f}² + {(2/3 * data.delta_t_in):.4f}²) = {delta_tot_t1:.4f} с")

        # Косвенная погрешность для ускорения a
        mean_t2 = sum(t2_vals) / n
        S_t2 = math.sqrt(sum((v - mean_t2)**2 for v in t2_vals) / (n * (n - 1)))
        delta_tot_t2 = math.sqrt((data.t_student * S_t2)**2 + ((2/3) * data.delta_t_in)**2)
        
        x1, x2 = 0.15, 1.10
        a_mean = 2 * (x2 - x1) / (mean_t2**2 - mean_t1**2)
        term1 = 2 * (data.delta_x_rail**2) / ((x2 - x1)**2)
        term2 = 4 * ((mean_t1 * delta_tot_t1)**2 + (mean_t2 * delta_tot_t2)**2) / ((mean_t2**2 - mean_t1**2)**2)
        da = a_mean * math.sqrt(term1 + term2)

        print("\n2. Косвенная погрешность ускорения <a> (по формуле 22):")
        print(f"   <t1> = {mean_t1:.3f}, Δt1 = {delta_tot_t1:.4f}")
        print(f"   <t2> = {mean_t2:.3f}, Δt2 = {delta_tot_t2:.4f}")
        print(f"   <a> = {a_mean:.4f} м/с²")
        print(f"   Δ<a> = <a> * √( 2*(Δx/(x2-x1))² + 4*((<t1>Δt1)²+(<t2>Δt2)²)/(<t2>²-<t1>²)² ) = {da:.4f} м/с²")
    else:
        print("\nЗагрузите данные Задания 2 для просмотра примера.")


def main():
    data = ExperimentData()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_file = os.path.join(script_dir, "input.txt")
    
    if os.path.exists(default_file):
        parsed = DataParser.parse_file(default_file)
        if parsed:
            data.load_from_parser(parsed)
            print(f"--- Данные автоматически загружены из {default_file} ---")
    
    while True:
        print_menu(data)
        choice = input("Выберите действие: ").strip()

        if choice == '1':
            filename = input("Введите имя файла (по умолчанию input.txt): ").strip() or "input.txt"
            parsed = DataParser.parse_file(os.path.join(script_dir, filename))
            if parsed:
                data.load_from_parser(parsed)
                print("Данные успешно загружены.")
            else:
                print("Не удалось загрузить данные.")
            input("Нажмите Enter...")

        elif choice == '2':
            process_task_1(data)
            input("Нажмите Enter...")

        elif choice == '3':
            process_task_2(data)
            input("Нажмите Enter...")

        elif choice == '4':
            print("\nИзменение констант и погрешностей приборов:")
            data.X = input_float(f"X (Координата h0) м [{data.X}]: ", data.X)
            data.X_prime = input_float(f"X' (Координата h0') м [{data.X_prime}]: ", data.X_prime)
            data.h0 = input_float(f"h0 (м) [{data.h0}]: ", data.h0)
            data.h0_prime = input_float(f"h0' (м) [{data.h0_prime}]: ", data.h0_prime)
            print("\nПогрешности приборов:")
            data.delta_x_rail = input_float(f"Линейка-планка (Δx_rail) м [{data.delta_x_rail}]: ", data.delta_x_rail)
            data.delta_h_tri = input_float(f"Угольник (Δh_tri) м [{data.delta_h_tri}]: ", data.delta_h_tri)
            data.delta_t_in = input_float(f"Секундомер ПКЦ (Δt_in) с [{data.delta_t_in}]: ", data.delta_t_in)
            input("Нажмите Enter...")
            
        elif choice == '5':
            print_all_info(data)
            input("Нажмите Enter...")

        elif choice == '6':
            print_error_examples(data)
            input("Нажмите Enter...")

        elif choice == '0':
            break

if __name__ == "__main__":
    main()