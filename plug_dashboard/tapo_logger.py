import asyncio
import nest_asyncio
import sqlite3
from kasa import Discover
from datetime import datetime

nest_asyncio.apply()

DB_PATH = "Readings.db"

last_hour = None
last_energy = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS plug_readings(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT NOT NULL,
                   current_power REAL,
                   today_runtime INTEGER,
                   today_energy REAL,
                   month_runtime INTEGER,
                   month_energy REAL,
                   voltage_mv REAL,
                   current_ma REAL,
                   energy_wh REAL
                   )
            """)
    
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS hourly_readings(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date_time TEXT NOT NULL,
                   hourly_energy REAL
                   )
            """)
    
    conn.commit()
    conn.close()

def store_data(timestamp, current_power, today_runtime, today_energy, month_runtime, month_energy, voltage, current, energy_wh):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plug_readings(timestamp, current_power, today_runtime, today_energy, month_runtime, month_energy, voltage_mv, current_ma, energy_wh)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",(timestamp, current_power, today_runtime, today_energy, month_runtime, month_energy, voltage, current, energy_wh))
    conn.commit()
    conn.close()

def store_hourly_data(date_time, hourly_energy):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO hourly_readings(date_time, hourly_energy) VALUES (?, ?)""",(date_time, hourly_energy))
    conn.commit()
    conn.close()

async def collect_and_store_data():
    global last_hour, last_energy

    try:
        plug = await Discover.discover_single("192.168.0.44", username="rangalakshmirangaraj@gmail.com", password="admin123")

        if plug:
            await plug.update()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            energy_usage = plug.internal_state['get_energy_usage']

            current_power = energy_usage['current_power'] / 1000  # in W
            today_runtime = energy_usage['today_runtime']         # in minutes
            month_runtime = energy_usage['month_runtime']         # in minutes
            today_energy = energy_usage['today_energy'] / 1000    # in kWh
            month_energy = energy_usage['month_energy'] / 1000    # in kWh

            emeter_data = plug.internal_state['get_emeter_data']

            current = emeter_data['current_ma']                   # in mA
            voltage = emeter_data['voltage_mv']/1000              # in V
            energy_wh = emeter_data['energy_wh']/1000             # in KWh

            print(f"[{timestamp}] Logged data: Power {current_power} W, Today {today_energy} kWh, Month {month_energy} kWh, Current {current}, Voltage {voltage}")

            store_data(timestamp, current_power, today_runtime, today_energy, month_runtime, month_energy, voltage, current, energy_wh)

            # Storing hourly energy data
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

            if last_hour is None:
                last_hour = current_hour
                last_energy = today_energy
            elif current_hour != last_hour:
                energy_delta = round(today_energy - last_energy, 4)
                print(f"[{current_hour}] Hourly production: {energy_delta:.3f} kWh")
                store_hourly_data(last_hour, energy_delta)
                last_hour = current_hour
                last_energy = today_energy
            
            await plug.protocol.close()

        else:
            print(f"[{datetime.now()}] | Device not found at the provided IP")

    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")

async def main():
    init_db()
    while True:
        await collect_and_store_data()
        await asyncio.sleep(5)

asyncio.run(main())

