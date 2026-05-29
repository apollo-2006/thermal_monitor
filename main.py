import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.theme import Theme
from rich.layout import Layout
from rich.panel import Panel

from core.sensors import HardwareSensors
from core.storage import TelemetryDB

# Stealth aesthetic
custom_theme = Theme({
    "metric": "dim cyan",
    "alert": "bold red",
    "stable": "dim green"
})

console = Console(theme=custom_theme)
db = TelemetryDB()
sensors = HardwareSensors()


def generate_dashboard() -> Table:
    """Generates the live-updating UI table."""
    cpu = sensors.get_cpu_usage()
    temp = sensors.get_cpu_temp()
    ram = sensors.get_ram_usage()
    vram = sensors.get_vram_clock_sim()

    # Log to local SQLite database
    db.log_metrics(cpu, temp, ram, vram)

    # Dynamic styling based on thermal thresholds
    temp_style = "stable" if temp < 65 else "alert"
    cpu_style = "metric" if cpu < 80 else "alert"

    table = Table(title="ThermalGrid Telemetry Daemon", style="dim", expand=True)
    table.add_column("Sensor", justify="left", style="dim white", no_wrap=True)
    table.add_column("Current Value", justify="right", style="bold")
    table.add_column("Status", justify="center")

    table.add_row("CPU Load", f"[{cpu_style}]{cpu}%[/{cpu_style}]", "🟢" if cpu < 80 else "🔴")
    table.add_row("Package Temp", f"[{temp_style}]{temp}°C[/{temp_style}]", "🟢" if temp < 65 else "🔴")
    table.add_row("RAM Usage", f"[{custom_theme.styles['metric']}]{ram}%[/{custom_theme.styles['metric']}]", "🟢")
    table.add_row("VRAM Clock", f"[dim magenta]{vram} MHz[/dim magenta]", "🔵")

    return table


def main():
    console.clear()
    console.print("\n[dim]Initializing hardware hooks...[/dim]")
    time.sleep(1)

    try:
        with Live(generate_dashboard(), refresh_per_second=2, console=console) as live:
            while True:
                live.update(generate_dashboard())
                time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[dim]Telemetry run completed. Data saved to thermal_grid.db.[/dim]\n")


if __name__ == "__main__":
    main()