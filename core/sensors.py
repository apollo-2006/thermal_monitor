import time

import psutil
import random

# Thermal drivers that report the CPU package, in the order they are tried. coretemp is
# Intel; k10temp and zenpower are the two AMD drivers; cpu_thermal is ARM boards.
CPU_TEMP_DRIVERS = ("coretemp", "k10temp", "zenpower", "cpu_thermal")


class HardwareSensors:
    def __init__(self):
        # cpu_percent(interval=None) reports load since the previous call, and the first
        # call has nothing to compare against. Take that call here, then give the first
        # real sample a short window to measure.
        psutil.cpu_percent(interval=None)
        time.sleep(0.1)

    @staticmethod
    def get_cpu_usage() -> float:
        # Load since the last sample, so consecutive ticks cover the whole run. A blocking
        # 0.1s poll inside a 0.5s loop measured one sixth of it and slowed the loop to 1.7 Hz.
        return psutil.cpu_percent(interval=None)

    @staticmethod
    def get_ram_usage() -> float:
        return psutil.virtual_memory().percent

    @staticmethod
    def get_cpu_temp(cpu_usage: float) -> tuple[float, bool]:
        """
        Returns (temperature, measured). Reads the package sensor from the platform's
        thermal drivers. Falls back to a simulated curve derived from the current load when
        none is available, which is the common case on Windows and inside WSL, and says so
        through `measured` so the caller never shows an estimate as a reading.

        Takes the load reading rather than sampling it again so the fallback
        temperature lines up with the CPU figure shown for the same tick.
        """
        try:
            temps = psutil.sensors_temperatures()
        except AttributeError:  # not implemented on this platform (Windows)
            temps = {}
        for driver in CPU_TEMP_DRIVERS:
            if temps.get(driver):
                return temps[driver][0].current, True

        base_temp = 35.0
        load_heat = cpu_usage * 0.45
        return round(base_temp + load_heat + random.uniform(-1, 1), 1), False

    @staticmethod
    def get_vram_clock_sim(cpu_usage: float) -> float:
        """
        Placeholder for real GPU clocks (PyNVML on NVIDIA, PyAMDGPUInfo on AMD).
        Models the three clock states a card steps through, keyed off system
        activity rather than measured from the card.
        """
        if cpu_usage < 10:
            return 400.0    # Idle
        elif cpu_usage < 50:
            return 1200.0   # Mid-state
        else:
            return 2400.0   # Boost state

    @classmethod
    def sample(cls) -> dict:
        """
        Takes one coherent reading of every sensor.

        The CPU is polled exactly once here and the result threaded through the
        derived readings. Polling it separately per sensor produced three different
        load figures inside a single frame.
        """
        cpu = cls.get_cpu_usage()
        temp, temp_measured = cls.get_cpu_temp(cpu)
        return {
            "cpu": cpu,
            "temp": temp,
            "temp_measured": temp_measured,
            "ram": cls.get_ram_usage(),
            "vram": cls.get_vram_clock_sim(cpu),
        }
