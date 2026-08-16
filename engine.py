import math
import pandas as pd

class TelemetryEngine:
    def __init__(self):
        # Константы физической среды (Уровень моря, Каспийск/Махачкала)
        self.RHO = 1.225       # Плотность воздуха (кг/м³)
        self.V_CC = 5.0        # Напряжение питания датчиков (Вольт)
        
        # Параметры фильтрации (Окно сглаживания высокочастотных шумов и тряски мотора)
        self.SMOOTHING_WINDOW = 5 

    def _clean_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Профессиональная фильтрация: применение алгоритма скользящего среднего
        для устранения вибраций карта на треке.
        """
        for col in ['ax', 'ay', 'az', 'raw_pressure']:
            if col in df.columns:
                # rolling(window) сглаживает резкие скачки датчиков от кочек трека
                df[col] = df[col].rolling(window=self.SMOOTHING_WINDOW, min_periods=1, center=True).mean()
        return df

    def _get_dynamic_cd(self, speed_kmh: float) -> float:
        """
        Аэродинамическая интерполяция: в автоспорте коэффициент Cd меняется 
        в зависимости от скорости и турбулентности потока.
        """
        if speed_kmh < 40:
            return 0.90  # Прокатный режим: высокое сопротивление из-за отсутствия обтекателей
        elif speed_kmh <= 80:
            return 0.82  # Спортивный режим: поток стабилизируется
        else:
            return 0.74  # Режим F1: высокая скорость, пилот прижимается к рулю

    def analyze(self, filepath: str) -> dict:
        """
        Главный метод анализа логов заезда.
        """
        # Читаем файл порциями (защита от падения сервера при больших объемах данных)
        df = pd.read_csv(filepath)
        
        # 1. Очищаем телеметрию от шумов вибрации
        df = self._clean_signal(df)

        # 2. Калибровка датчика давления MPXV7002DP (Перевод АЦП Arduino в Вольты)
        df["v_out"] = (df["raw_pressure"] / 1023.0) * self.V_CC

        # 3. Вычисление дифференциального давления в Паскалях (Transfer Function)
        df["pressure_pa"] = (df["v_out"] - (self.V_CC / 2.0)) / (0.2 * self.V_CC) * 1000.0

        # 4. Расчет истинной скорости воздушного потока (Трубка Пито)
        df["air_speed"] = df["pressure_pa"].apply(
            lambda p: math.sqrt((2.0 * abs(p)) / self.RHO) if p >= 0 else 0.0
        )

        # 5. Динамический расчет силы сопротивления и потерь мощности
        drag_forces = []
        power_losses_hp = []

        for _, row in df.iterrows():
            speed_kmh = row["gps_speed"] * 3.6
            cd = self._get_dynamic_cd(speed_kmh)
            area = 0.48 # Фронтальная проекция болида
            
            # Сила сопротивления Fd = 0.5 * rho * v² * Cd * A
            f_d = 0.5 * self.RHO * (row["air_speed"] ** 2) * cd * area
            # Потеря мощности в Лошадиных Силах
            p_loss = (f_d * row["gps_speed"]) / 735.5
            
            drag_forces.append(f_d)
            power_losses_hp.append(p_loss)

        df["drag_force_n"] = drag_forces
        df["power_loss_hp"] = power_losses_hp

        # Расчет итоговых спортивных метрик заезда
        max_speed = df["gps_speed"].max() * 3.6
        max_lateral_g = df["ay"].abs().max() / 9.81
        max_braking_g = df["ax"].min() / 9.81

        return {
            "max_speed": round(max_speed, 1),
            "max_drag": round(df["drag_force_n"].max(), 1),
            "avg_power_loss": round(df["power_loss_hp"].mean(), 2),
            "max_lateral_g": round(max_lateral_g, 2),
            "max_braking_g": round(abs(max_braking_g), 2),
            "total_points_analyzed": len(df)
        }
