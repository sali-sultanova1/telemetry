import pandas as pd
import numpy as np

timesteps = np.linspace(0, 45000, 450)
gps_speed = np.interp(timesteps, [0, 15000, 25000, 35000, 45000], [0, 24.0, 10.0, 20.0, 0.0])


# Добавляем ОГРОМНЫЙ шум (тряска мотора карта), проверяем устойчивость фильтра скользящего среднего
raw_pressure = 512 + (gps_speed * 2.2) + np.random.normal(0, 15.0, 450)
ay = np.sin(timesteps / 2000) * 10.0 + np.random.normal(0, 4.0, 450)  # Шум заносов
ax = np.cos(timesteps / 3000) * 4.5 + np.random.normal(0, 3.0, 450)  # Шум кочек

df = pd.DataFrame({
    'timestamp': timesteps.astype(int),
    'ax': ax, 'ay': ay, 'az': np.random.normal(9.81, 2.0, 450),
    'gx': 0.0, 'gy': 0.0, 'gz': 0.0,
    'raw_pressure': raw_pressure.astype(int),
    'lat': 42.894500 + (np.cos(timesteps / 3500) * 0.0005),
    'lng': 47.620200 + (np.sin(timesteps / 2000) * 0.0006),
    'gps_speed': gps_speed
})

df.to_csv('mock_track.csv', index=False)
print("⚠️ СГЕНЕРИРОВАН СЛОЖНЫЙ ЗАШУМЛЕННЫЙ ЛОГ ДЛЯ ПРОВЕРКИ ФИЛЬТРОВ БЭКЕНДА!")
