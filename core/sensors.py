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
    def get_cpu_temp() -> float:
        """
        Attempts to read core temps. Falls back to a simulated
        thermal curve based on usage if sensors are locked by the OS.
        """
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            elif 'k10temp' in temps: # AMD specific
                return temps['k10temp'][0].current
            raise KeyError
        except (AttributeError, KeyError):
            # Fallback: Simulate thermal curve based on CPU load
            base_temp = 35.0
            load_heat = HardwareSensors.get_cpu_usage() * 0.45
            return round(base_temp + load_heat + random.uniform(-1, 1), 1)

    @staticmethod
    def get_vram_clock_sim() -> float:
        """
        Placeholder for GPU VRAM clock speeds (e.g., fetching from PyNVML or PyAMDGPUInfo).
        Currently simulates clock stepping based on system activity.
        """
        load = HardwareSensors.get_cpu_usage()
        if load < 10:
            return 400.0  # Idle
        elif load < 50:
            return 1200.0 # Mid-state
        else:
            return 2400.0 # Boost state