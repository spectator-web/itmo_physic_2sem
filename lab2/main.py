import math
import os
import sys
from typing import List, Tuple, Optional

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
    """
    Читает файл, содержащий:
    - команду --table[positions, loads, measurements] и блоки данных,
    - строки с instrument_measurements (после последнего '---').
    Поддерживает разделители: пробел, табуляция, ';'.
    """

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
        """Разбивает строку по разделителям и возвращает список чисел."""
        parts = line.replace(';', ' ').replace('\t', ' ').split()
        nums = []
        for p in parts:
            num = DataParser.parse_number(p)
            if num is not None:
                nums.append(num)
        return nums

    @staticmethod
    def parse_file(filename: str) -> Tuple[Optional[List[List[List[float]]]], Optional[List[Tuple[float, float]]]]:
        """
        Возвращает (times, instrument_measurements):
        times: list[position][load][measurement]
        instrument_measurements: list of (value, error)
        """
        if not os.path.exists(filename):
            print(f"Ошибка: файл '{filename}' не найден.")
            return None, None

        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]

        times = []
        instr_meas = []
        i = 0
        n_lines = len(lines)

        while i < n_lines:
            line = lines[i]
            if not line:
                i += 1
                continue

            # Обработка команды --table
            if line.startswith('--table'):
                # Извлекаем параметры в скобках
                bracket = line.find('[')
                if bracket != -1 and line.endswith(']'):
                    params = line[bracket+1:-1].split(',')
                    if len(params) == 3:
                        try:
                            num_positions = int(params[0])
                            num_loads = int(params[1])
                            num_meas = int(params[2])
                        except ValueError:
                            print("Ошибка в параметрах --table")
                            return None, None
                    else:
                        print("Неверный формат --table")
                        return None, None
                else:
                    print("Неверный формат --table")
                    return None, None

                i += 1
                # Пропускаем пустые строки после команды
                while i < n_lines and not lines[i]:
                    i += 1

                # Читаем данные для каждого положения
                for pos in range(num_positions):
                    pos_data = []
                    # Для каждого положения должно быть num_loads строк
                    for load_idx in range(num_loads):
                        if i >= n_lines or not lines[i]:
                            print(f"Недостаточно данных для позиции {pos+1}")
                            return None, None
                        row_nums = DataParser.parse_line(lines[i])
                        # Ожидаем либо 4 числа (номер нагрузки + 3 времени), либо 3 числа (только времена)
                        if len(row_nums) == 4:
                            # Проверим, что номер нагрузки соответствует ожидаемому (1..num_loads)
                            load_num = int(row_nums[0])
                            if load_num != load_idx + 1:
                                print(f"Предупреждение: ожидалась нагрузка {load_idx+1}, получена {load_num}")
                            meas_times = row_nums[1:1+num_meas]
                        elif len(row_nums) == 3:
                            meas_times = row_nums[:num_meas]
                        else:
                            print(f"Неверное число чисел в строке: {lines[i]}")
                            return None, None
                        if len(meas_times) != num_meas:
                            print(f"Ожидалось {num_meas} измерений, получено {len(meas_times)}")
                            return None, None
                        pos_data.append(meas_times)
                        i += 1
                    times.append(pos_data)
                    # Пропускаем пустые строки между блоками
                    while i < n_lines and not lines[i]:
                        i += 1

            # Обработка instrument_measurements (после последнего '---')
            elif line == '---':
                i += 1
                # Читаем все следующие строки до конца файла
                while i < n_lines:
                    line = lines[i]
                    if not line:
                        i += 1
                        continue
                    # Формат: "значение +- погрешность"
                    parts = line.replace('+-', '±').split('±')
                    if len(parts) == 2:
                        val = DataParser.parse_number(parts[0])
                        err = DataParser.parse_number(parts[1])
                        if val is not None and err is not None:
                            instr_meas.append((val, err))
                        else:
                            print(f"Не удалось распознать строку: {line}")
                    else:
                        # Возможно просто число без погрешности
                        num = DataParser.parse_number(line)
                        if num is not None:
                            instr_meas.append((num, 0.0))
                    i += 1
                break  # после instrument_measurements дальше ничего нет

            else:
                # Игнорируем другие строки (например, комментарии)
                i += 1

        return times if times else None, instr_meas if instr_meas else None


# ------------------------------------------------------------
# Класс Statistics: статистическая обработка
# ------------------------------------------------------------
class Statistics:
    @staticmethod
    def mean(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def std_dev(values: List[float], ddof: int = 1) -> float:
        """Выборочное стандартное отклонение."""
        n = len(values)
        if n <= ddof:
            return 0.0
        avg = Statistics.mean(values)
        variance = sum((x - avg) ** 2 for x in values) / (n - ddof)
        return math.sqrt(variance)

    @staticmethod
    def sem(values: List[float]) -> float:
        """Стандартная ошибка среднего."""
        n = len(values)
        if n < 2:
            return 0.0
        return Statistics.std_dev(values) / math.sqrt(n)

    @staticmethod
    def student_error(values: List[float], t_coef: float) -> float:
        """Случайная погрешность = t * SEM."""
        return t_coef * Statistics.sem(values)

    @staticmethod
    def total_error(values: List[float], t_coef: float, instr_error: float) -> float:
        """Полная погрешность = sqrt(случайная^2 + приборная^2)."""
        rand_err = Statistics.student_error(values, t_coef)
        return math.sqrt(rand_err ** 2 + ((2/3)*instr_error) ** 2)


# ------------------------------------------------------------
# Класс PhysicsCalculator: физические формулы
# ------------------------------------------------------------
class PhysicsCalculator:
    @staticmethod
    def acceleration(t: float, h: float) -> float:
        """Ускорение груза: a = 2h / t^2"""
        return 2 * h / (t * t)

    @staticmethod
    def angular_acceleration(a: float, d: float) -> float:
        """Угловое ускорение: ε = 2a / d"""
        return 2 * a / d

    @staticmethod
    def moment(t: float, m: float, d: float, g: float, h: float) -> float:
        """Момент силы натяжения: M = (m*d/2)*(g - 2h/t^2)"""
        a = PhysicsCalculator.acceleration(t, h)
        return (m * d / 2) * (g - a)

    @staticmethod
    def delta_acceleration(a, t, dt, h, dh):
        rel = math.sqrt((dh/h)**2 + (2*dt/t)**2)
        return a * rel, rel

    @staticmethod
    def delta_angular_acceleration(eps, a, da, d, dd):
        rel = math.sqrt((da/a)**2 + (dd/d)**2) if a != 0 else 0
        return eps * rel, rel

    @staticmethod
    def delta_moment(M, m, dm, d, dd, g, dg, a, da):
        denom = (g - a)
        if denom == 0:
            rel = float('inf')
        else:
            rel = math.sqrt((dm/m)**2 + (dd/d)**2 + (dg**2 + da**2)/(denom**2))
        return M * rel, rel


# ------------------------------------------------------------
# Класс Regression: метод наименьших квадратов
# ------------------------------------------------------------
class Regression:
    @staticmethod
    def linear(x: List[float], y: List[float]) -> Tuple[float, float, float, float]:
        """
        Линейная регрессия y = a*x + b.
        Возвращает (a, b, sigma_a, sigma_b) - коэффициенты и их стандартные ошибки.
        """
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0, 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Вычисляем числитель и знаменатель для a
        cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        var_x = sum((xi - mean_x) ** 2 for xi in x)

        if abs(var_x) < 1e-12:
            a = 0.0
        else:
            a = cov_xy / var_x

        b = mean_y - a * mean_x

        # Остаточная сумма квадратов
        resid = sum((y[i] - (a * x[i] + b)) ** 2 for i in range(n))
        if n > 2:
            s2 = resid / (n - 2)  # дисперсия остатков
        else:
            s2 = 0.0

        # Стандартные ошибки
        if var_x > 0:
            sigma_a = math.sqrt(s2 / var_x)
        else:
            sigma_a = 0.0
        sigma_b = math.sqrt(s2 * (1.0 / n + mean_x ** 2 / var_x)) if var_x > 0 else 0.0

        return a, b, sigma_a, sigma_b


# ------------------------------------------------------------
# Класс ExperimentData: хранение всех данных и параметров
# ------------------------------------------------------------
class ExperimentData:
    def __init__(self):
        self.times = []          # list[position][load][measurement]
        self.instr_meas = []     # list of (value, error)
        self.student_coef = 4.3  # по умолчанию для трёх измерений и α=0.95
        self.instr_error_time = 0.25  # приборная погрешность секундомера (с)
        self.height = 0.7       # м (по умолчанию)
        self.diameter = 0.046     # м (по умолчанию 4.6 см)
        self.masses = []          # кг, для каждой нагрузки
        self.g = 9.81             # м/с²
        # Параметры для расчёта R
        self.l1 = 0.057           # м
        self.l0 = 0.025           # м
        self.b = 0.04             # м
        self.delta_h = 0.0005      # м
        self.delta_d = 0.0005      # м
        self.delta_m = 0.0005      # кг
        self.delta_g = 0.01        # м/с²
        # Дополнительно: номера рисок (позиций)
        self.positions = []       # список номеров рисок (например, 1..n)

    def load_from_parser(self, times, instr_meas):
        self.times = times
        self.instr_meas = instr_meas
        # Попытаемся автоматически установить массы, если есть подходящие значения
        # Например, предположим, что в instr_meas есть масса одной шайбы и масса каретки
        # Но мы не знаем порядок. Пользователь может ввести вручную.
        # Пока оставим пустым.
        self.masses = []
        # Также можно попытаться определить количество нагрузок
        if times:
            self.positions = list(range(1, len(times) + 1))

    def get_num_positions(self):
        return len(self.times)

    def get_num_loads(self):
        if self.times:
            return len(self.times[0])
        return 0

    def get_num_measurements(self):
        if self.times and self.times[0]:
            return len(self.times[0][0])
        return 0


# ------------------------------------------------------------
# Вспомогательные функции для меню
# ------------------------------------------------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_menu(data: ExperimentData):
    print("\n" + "=" * 70)
    print("   ЛАБОРАТОРНАЯ РАБОТА №1.04: МАЯТНИК ОБЕРБЕКА")
    print("=" * 70)
    print(f"Файл загружен: {'да' if data.times else 'нет'}")
    if data.times:
        print(f"  Позиций: {data.get_num_positions()}, Нагрузок: {data.get_num_loads()}, Измерений: {data.get_num_measurements()}")
    print(f"Текущие параметры:")
    print(f"  Коэф. Стьюдента t = {data.student_coef:.3f}")
    print(f"  Приборная погрешность времени = {data.instr_error_time:.4f} с")
    print(f"  Высота h = {data.height:.3f} м")
    print(f"  Диаметр ступицы d = {data.diameter:.4f} м")
    print(f"  g = {data.g:.2f} м/с²")
    if data.masses:
        print(f"  Массы нагрузок: {data.masses}")
    print("-" * 70)
    print("1. Загрузить данные из файла")
    print("2. Показать полный отчёт (все данные и расчёты)")
    print("3. Рассчитать средние времена")
    print("4. Рассчитать статистику (СКО, погрешности)")
    print("5. Рассчитать физические величины (a, ε, M)")
    print("6. МНК для M(ε) (определить I и Mтр по позициям)")
    print("7. МНК для I(R²) (проверка теоремы Штейнера)")
    print("8. Вывести итоговую таблицу (position load t1 t2 t3 t_avg sigma dt a epsilon M)")
    print("9. Экспорт таблицы в файл")
    print("10. Изменить приборную погрешность времени")
    print("11. Ручной ввод параметров установки")
    print("0. Выход")
    print("-" * 70)


def input_float(prompt: str, default: Optional[float] = None) -> float:
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        try:
            return float(s.replace(',', '.'))
        except ValueError:
            print("Ошибка: введите число.")


def input_int(prompt: str, default: Optional[int] = None) -> int:
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        try:
            return int(s)
        except ValueError:
            print("Ошибка: введите целое число.")


def set_student_coef_interactively(data: ExperimentData):
    """Предлагает пользователю изменить коэффициент Стьюдента."""
    print(f"\nТекущий коэффициент Стьюдента: {data.student_coef:.3f}")
    if SCIPY_AVAILABLE:
        ans = input("Вычислить автоматически по вероятности и числу измерений? (y/n): ").strip().lower()
        if ans in ('y', 'yes', 'д', 'да'):
            prob = input_float("Доверительная вероятность (например, 0.95): ", 0.95)
            n = input_int("Число измерений (n): ", data.get_num_measurements() or 3)
            df = n - 1
            t_val = stats.t.ppf((1 + prob) / 2, df)
            data.student_coef = t_val
            print(f"Коэффициент Стьюдента установлен: {t_val:.6f}")
            return
    # Если scipy недоступен или пользователь отказался, предложим ввести вручную
    new_t = input_float("Введите коэффициент Стьюдента вручную (Enter для сохранения текущего): ", data.student_coef)
    data.student_coef = new_t


def print_full_report(data: ExperimentData):
    """Выводит полный отчёт: параметры, исходные данные, статистику, расчёты, МНК."""
    if not data.times:
        print("Данные не загружены.")
        return

    # Параметры установки
    print("\n" + "=" * 70)
    print("ПОЛНЫЙ ОТЧЁТ")
    print("=" * 70)
    print("Параметры установки:")
    print(f"  Высота падения h = {data.height:.3f} м")
    print(f"  Диаметр ступицы d = {data.diameter:.4f} м")
    print(f"  g = {data.g:.2f} м/с²")
    print(f"  l1 = {data.l1:.3f} м, l0 = {data.l0:.3f} м, b = {data.b:.3f} м")
    print(f"  Приборная погрешность времени = {data.instr_error_time:.4f} с")
    print(f"  Коэффициент Стьюдента = {data.student_coef:.3f}")
    print(f"  Погрешности измерений: dh = {data.delta_h:.4f} м, dd = {data.delta_d:.4f} м, dm = {data.delta_m:.4f} кг, dg = {data.delta_g:.4f} м/с²")
    if data.masses:
        print(f"  Массы нагрузок: {data.masses} кг")
    else:
        print("  Массы нагрузок не заданы (будут использованы значения по умолчанию).")

    # Исходные данные (времена)
    print("\nИсходные данные (время в секундах):")
    for p_idx, pos in enumerate(data.times):
        print(f"Позиция {p_idx+1}:")
        for l_idx, load in enumerate(pos):
            print(f"  Нагрузка {l_idx+1}: {load}")

    # Статистика времени
    print("\nСтатистика времени:")
    print("Pos Load  t_avg     sigma     dt_rand   dt_total  rel%")
    for p_idx, pos in enumerate(data.times):
        for l_idx, load in enumerate(pos):
            avg = Statistics.mean(load)
            sigma = Statistics.std_dev(load)
            rand_err = Statistics.student_error(load, data.student_coef)
            total_err = Statistics.total_error(load, data.student_coef, data.instr_error_time)
            rel = (total_err / avg * 100) if avg != 0 else 0
            print(f"{p_idx+1:3d} {l_idx+1:4d}  {avg:8.6f}  {sigma:8.6f}  {rand_err:8.6f}  {total_err:8.6f}  {rel:6.2f}%")

    # Физические величины с погрешностями
    print("\nФизические величины (по среднему времени):")
    print("Pos Load   t_avg      a (м/с²)   da        ε (рад/с²) deps      M (Н·м)    dM")
    for p_idx, pos in enumerate(data.times):
        for l_idx, load in enumerate(pos):
            t_avg = Statistics.mean(load)
            dt = Statistics.total_error(load, data.student_coef, data.instr_error_time)
            a = PhysicsCalculator.acceleration(t_avg, data.height)
            da, _ = PhysicsCalculator.delta_acceleration(a, t_avg, dt, data.height, data.delta_h)
            eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
            deps, _ = PhysicsCalculator.delta_angular_acceleration(eps, a, da, data.diameter, data.delta_d)
            # Определяем массу нагрузки (если не задана, используем заглушку)
            if l_idx < len(data.masses):
                m_load = data.masses[l_idx]
            else:
                m_load = 0.22 * (l_idx + 1)
            M = PhysicsCalculator.moment(t_avg, m_load, data.diameter, data.g, data.height)
            dM, _ = PhysicsCalculator.delta_moment(M, m_load, data.delta_m, data.diameter, data.delta_d, data.g, data.delta_g, a, da)
            print(f"{p_idx+1:3d} {l_idx+1:4d}  {t_avg:8.6f}  {a:10.6f}  {da:8.6f}  {eps:10.6f}  {deps:8.6f}  {M:10.6f}  {dM:8.6f}")

    # МНК для M(ε) по каждой позиции
    print("\nМНК для зависимости M = I·ε + Mтр по каждой позиции:")
    mnk_results = []
    for p_idx, pos in enumerate(data.times):
        eps_list = []
        M_list = []
        for l_idx, load in enumerate(pos):
            t_avg = Statistics.mean(load)
            a = PhysicsCalculator.acceleration(t_avg, data.height)
            eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
            m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.22 * (l_idx+1)
            M = PhysicsCalculator.moment(t_avg, m_load, data.diameter, data.g, data.height)
            eps_list.append(eps)
            M_list.append(M)
        if len(eps_list) >= 2:
            I, M_tr, sigma_I, sigma_Mtr = Regression.linear(eps_list, M_list)
            mnk_results.append((p_idx+1, I, M_tr, sigma_I, sigma_Mtr))
        else:
            print(f"Позиция {p_idx+1}: недостаточно точек для регрессии")
    if mnk_results:
        print("Позиция  I (кг·м²)     Mтр (Н·м)    σ_I        σ_Mtr")
        for r in mnk_results:
            print(f"{r[0]:7d}  {r[1]:10.6f}  {r[2]:10.6f}  {r[3]:8.6f}  {r[4]:8.6f}")

    # МНК для теоремы Штейнера
    print("\nМНК для I = I0 + 4·m_гр·R² (теорема Штейнера):")
    I_vals = []
    R2_vals = []
    for p_idx, pos in enumerate(data.times):
        eps_list = []
        M_list = []
        for l_idx, load in enumerate(pos):
            t_avg = Statistics.mean(load)
            a = PhysicsCalculator.acceleration(t_avg, data.height)
            eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
            m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.22 * (l_idx+1)
            M = PhysicsCalculator.moment(t_avg, m_load, data.diameter, data.g, data.height)
            eps_list.append(eps)
            M_list.append(M)
        if len(eps_list) >= 2:
            I, _, _, _ = Regression.linear(eps_list, M_list)
        else:
            I = 0.0
        I_vals.append(I)

        n = p_idx + 1
        R = data.l1 + (n - 1) * data.l0 + data.b / 2
        R2_vals.append(R ** 2)

    if len(I_vals) >= 2:
        m_gr4, I0, sigma_m4, sigma_I0 = Regression.linear(R2_vals, I_vals)
        m_gr = m_gr4 / 4
        sigma_m_gr = sigma_m4 / 4
        print(f"  I0 = {I0:.6f} ± {sigma_I0:.6f} кг·м²")
        print(f"  m_гр = {m_gr:.6f} ± {sigma_m_gr:.6f} кг")
        print("  (ожидаемая масса одного груза на крестовине около 0.2-0.3 кг)")
    else:
        print("Недостаточно данных для регрессии.")

    print("=" * 70)

# ------------------------------------------------------------
# Основная программа
# ------------------------------------------------------------
def main():
    data = ExperimentData()
    
    # Автоматическая загрузка данных при старте
    default_file = "lab2/input.txt"
    if os.path.exists(default_file):
        times, instr_meas = DataParser.parse_file(default_file)
        if times is not None:
            data.load_from_parser(times, instr_meas)
            print(f"Данные автоматически загружены из {default_file}")
            if instr_meas:
                print("Инструментальные измерения:")
                for i, (val, err) in enumerate(instr_meas):
                    print(f"  {i+1}: {val} ± {err}")
            # Предложим настроить коэффициент Стьюдента
            set_student_coef_interactively(data)
        else:
            print(f"Не удалось загрузить данные из {default_file}")
    else:
        print(f"Файл {default_file} не найден. Загрузите данные вручную (пункт 1).")
    
    while True:
        clear_screen()
        print_menu(data)
        choice = input("Выберите действие: ").strip()

        if choice == '1':
            # Загрузка из фиксированного файла
            filename = "lab2/input.txt"
            times, instr_meas = DataParser.parse_file(filename)
            if times is not None:
                data.load_from_parser(times, instr_meas)
                print("Данные успешно загружены.")
                if instr_meas:
                    print("Инструментальные измерения:")
                    for i, (val, err) in enumerate(instr_meas):
                        print(f"  {i+1}: {val} ± {err}")
                else:
                    print("Инструментальные измерения отсутствуют.")
                # Предложим настроить коэффициент Стьюдента
                set_student_coef_interactively(data)
            else:
                print("Не удалось загрузить данные.")
            input("Нажмите Enter для продолжения...")

        elif choice == '2':
            print_full_report(data)
            input("Нажмите Enter для продолжения...")

        elif choice == '3':
            if not data.times:
                print("Данные не загружены.")
            else:
                print("\nСредние времена:")
                for p_idx, pos in enumerate(data.times):
                    print(f"Позиция {p_idx+1}:")
                    for l_idx, load in enumerate(pos):
                        avg = Statistics.mean(load)
                        print(f"  Нагрузка {l_idx+1}: {avg:.6f} с")
            input("Нажмите Enter для продолжения...")

        elif choice == '4':
            if not data.times:
                print("Данные не загружены.")
            else:
                print("\nСтатистика по каждому набору измерений:")
                print("Pos Load  t_avg     sigma     dt_rand   dt_total  rel%")
                for p_idx, pos in enumerate(data.times):
                    for l_idx, load in enumerate(pos):
                        avg = Statistics.mean(load)
                        sigma = Statistics.std_dev(load)
                        rand_err = Statistics.student_error(load, data.student_coef)
                        total_err = Statistics.total_error(load, data.student_coef, data.instr_error_time)
                        rel = (total_err / avg * 100) if avg != 0 else 0
                        print(f"{p_idx+1:3d} {l_idx+1:4d}  {avg:8.6f}  {sigma:8.6f}  {rand_err:8.6f}  {total_err:8.6f}  {rel:6.2f}%")
            input("Нажмите Enter для продолжения...")

        elif choice == '5':
            if not data.times:
                print("Данные не загружены.")
            else:
                if not data.masses:
                    print("Внимание: не заданы массы нагрузок. Используем массы по умолчанию: 0.22, 0.44, ...")
                    num_loads = data.get_num_loads()
                    data.masses = [0.22 * (i+1) for i in range(num_loads)]
                print("\nФизические величины (по среднему времени):")
                print("Pos Load   t_avg      a (м/с²)   ε (рад/с²)  M (Н·м)")
                for p_idx, pos in enumerate(data.times):
                    for l_idx, load in enumerate(pos):
                        t_avg = Statistics.mean(load)
                        a = PhysicsCalculator.acceleration(t_avg, data.height)
                        eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
                        M = PhysicsCalculator.moment(t_avg, data.masses[l_idx], data.diameter, data.g, data.height)
                        print(f"{p_idx+1:3d} {l_idx+1:4d}  {t_avg:8.6f}  {a:10.6f}  {eps:10.6f}  {M:10.6f}")
            input("Нажмите Enter для продолжения...")

        elif choice == '6':
            if not data.times or not data.masses:
                print("Необходимо загрузить данные и задать массы нагрузок.")
            else:
                print("\nМНК для зависимости M = I·ε + Mтр по каждой позиции:")
                results = []
                for p_idx, pos in enumerate(data.times):
                    eps_list = []
                    M_list = []
                    for l_idx, load in enumerate(pos):
                        t_avg = Statistics.mean(load)
                        a = PhysicsCalculator.acceleration(t_avg, data.height)
                        eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
                        M = PhysicsCalculator.moment(t_avg, data.masses[l_idx], data.diameter, data.g, data.height)
                        eps_list.append(eps)
                        M_list.append(M)
                    if len(eps_list) >= 2:
                        I, M_tr, sigma_I, sigma_Mtr = Regression.linear(eps_list, M_list)
                        results.append((p_idx+1, I, M_tr, sigma_I, sigma_Mtr))
                    else:
                        print(f"Позиция {p_idx+1}: недостаточно точек для регрессии")

                print("\nРезультаты МНК:")
                print("Позиция  I (кг·м²)     Mтр (Н·м)    σ_I        σ_Mtr")
                for r in results:
                    print(f"{r[0]:7d}  {r[1]:10.6f}  {r[2]:10.6f}  {r[3]:8.6f}  {r[4]:8.6f}")
            input("Нажмите Enter для продолжения...")

        elif choice == '7':
            if not data.times:
                print("Данные не загружены.")
            else:
                print("\nМНК для I = I0 + 4·m_гр·R² (теорема Штейнера)")
                I_vals = []
                R2_vals = []
                for p_idx, pos in enumerate(data.times):
                    eps_list = []
                    M_list = []
                    for l_idx, load in enumerate(pos):
                        t_avg = Statistics.mean(load)
                        a = PhysicsCalculator.acceleration(t_avg, data.height)
                        eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
                        # Если массы не заданы, используем заглушку
                        m_load = data.masses[l_idx] if l_idx < len(data.masses) else 0.22 * (l_idx+1)
                        M = PhysicsCalculator.moment(t_avg, m_load, data.diameter, data.g, data.height)
                        eps_list.append(eps)
                        M_list.append(M)
                    if len(eps_list) >= 2:
                        I, _, _, _ = Regression.linear(eps_list, M_list)
                    else:
                        I = 0.0
                    I_vals.append(I)

                    n = p_idx + 1
                    R = data.l1 + (n - 1) * data.l0 + data.b / 2
                    R2_vals.append(R ** 2)

                if len(I_vals) >= 2:
                    I0, m_gr4, sigma_I0, sigma_m4 = Regression.linear(R2_vals, I_vals)
                    m_gr = m_gr4 / 4
                    sigma_m_gr = sigma_m4 / 4
                    print(f"\nРезультаты:")
                    print(f"  I0 = {I0:.6f} ± {sigma_I0:.6f} кг·м²")
                    print(f"  m_гр = {m_gr:.6f} ± {sigma_m_gr:.6f} кг")
                    print("Проверка: ожидаемая масса одного груза на крестовине около 0.2-0.3 кг.")
                else:
                    print("Недостаточно данных для регрессии.")
            input("Нажмите Enter для продолжения...")

        elif choice == '8':
            if not data.times:
                print("Данные не загружены.")
            else:
                if not data.masses:
                    num_loads = data.get_num_loads()
                    data.masses = [0.22 * (i+1) for i in range(num_loads)]
                print("\nИТОГОВАЯ ТАБЛИЦА")
                print("Pos\tLoad\tt1\tt2\tt3\tt_avg\tsigma\tdt\ta\tepsilon\tM")
                for p_idx, pos in enumerate(data.times):
                    for l_idx, load in enumerate(pos):
                        t1, t2, t3 = load[0], load[1], load[2] if len(load) > 2 else 0.0
                        t_avg = Statistics.mean(load)
                        sigma = Statistics.std_dev(load)
                        dt = Statistics.total_error(load, data.student_coef, data.instr_error_time)
                        a = PhysicsCalculator.acceleration(t_avg, data.height)
                        eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
                        M = PhysicsCalculator.moment(t_avg, data.masses[l_idx], data.diameter, data.g, data.height)
                        print(f"{p_idx+1}\t{l_idx+1}\t{t1:.3f}\t{t2:.3f}\t{t3:.3f}\t{t_avg:.6f}\t{sigma:.6f}\t{dt:.6f}\t{a:.6f}\t{eps:.6f}\t{M:.6f}")
            input("Нажмите Enter для продолжения...")

        elif choice == '9':
            if not data.times:
                print("Данные не загружены.")
            else:
                fname = "results.txt"  # фиксированное имя файла для экспорта
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write("Pos\tLoad\tt1\tt2\tt3\tt_avg\tsigma\tdt\ta\tepsilon\tM\n")
                    for p_idx, pos in enumerate(data.times):
                        for l_idx, load in enumerate(pos):
                            t1, t2, t3 = load[0], load[1], load[2] if len(load) > 2 else 0.0
                            t_avg = Statistics.mean(load)
                            sigma = Statistics.std_dev(load)
                            dt = Statistics.total_error(load, data.student_coef, data.instr_error_time)
                            a = PhysicsCalculator.acceleration(t_avg, data.height)
                            eps = PhysicsCalculator.angular_acceleration(a, data.diameter)
                            M = PhysicsCalculator.moment(t_avg, data.masses[l_idx], data.diameter, data.g, data.height)
                            f.write(f"{p_idx+1}\t{l_idx+1}\t{t1:.3f}\t{t2:.3f}\t{t3:.3f}\t{t_avg:.6f}\t{sigma:.6f}\t{dt:.6f}\t{a:.6f}\t{eps:.6f}\t{M:.6f}\n")
                print(f"Таблица сохранена в {fname}")
            input("Нажмите Enter для продолжения...")

        elif choice == '10':
            print("Текущая приборная погрешность времени: {:.4f} с".format(data.instr_error_time))
            new_err = input_float("Введите новую приборную погрешность (с): ", data.instr_error_time)
            data.instr_error_time = new_err
            input("Нажмите Enter для продолжения...")

        elif choice == '11':
            print("Ручной ввод параметров установки:")
            data.height = input_float("Высота h (м): ", data.height)
            data.diameter = input_float("Диаметр ступицы d (м): ", data.diameter)
            data.g = input_float("Ускорение g (м/с²): ", data.g)
            if data.times:
                num_loads = data.get_num_loads()
                print(f"Введите массы для {num_loads} нагрузок (кг):")
                masses = []
                for i in range(num_loads):
                    m = input_float(f"  Нагрузка {i+1}: ", 0.22*(i+1))
                    masses.append(m)
                data.masses = masses
            else:
                print("Сначала загрузите данные, чтобы определить количество нагрузок.")
            data.l1 = input_float("Расстояние до первой риски l1 (м): ", data.l1)
            data.l0 = input_float("Шаг рисок l0 (м): ", data.l0)
            data.b = input_float("Размер груза b (м): ", data.b)
            input("Нажмите Enter для продолжения...")

        elif choice == '0':
            print("Выход из программы.")
            break

        else:
            print("Неверный пункт меню.")
            input("Нажмите Enter для продолжения...")


if __name__ == "__main__":
    main()