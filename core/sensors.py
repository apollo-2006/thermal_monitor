import psutil
import random


class HardwareSensors:
    @staticmethod
    def get_cpu_usage() -> float:
        return psutil.cpu_percent(interval=0.1)

    @staticmethod
    def get_ram_usage() -> float:
        return psutil.virtual_memory().percent

    @staticmethod
    def get_cpu_temp(cpu_usage: float) -> float:
        """
        Reads core temps from the platform's thermal zones. Falls back to a
        simulated curve derived from the current load when the sensors are
        unavailable, which is the common case on Windows and inside WSL.

        Takes the load reading rather than sampling it again so the fallback
        temperature lines up with the CPU figure shown for the same tick.
        """
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            elif 'k10temp' in temps:  # AMD specific
                return temps['k10temp'][0].current
            raise KeyError
        except (AttributeError, KeyError):
            base_temp = 35.0
            load_heat = cpu_usage * 0.45
            return round(base_temp + load_heat + random.uniform(-1, 1), 1)

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
        derived readings. Polling it separately per sensor blocked for 0.1s each
        time and produced three different load figures inside a single frame.
        """
        cpu = cls.get_cpu_usage()
        return {
            "cpu": cpu,
            "temp": cls.get_cpu_temp(cpu),
            "ram": cls.get_ram_usage(),
            "vram": cls.get_vram_clock_sim(cpu),
        }
