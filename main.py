import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.theme import Theme

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

TEMP_LIMIT = 65.0
LOAD_LIMIT = 80.0


def render_dashboard(reading: dict) -> Table:
    """Builds the live table for one sensor reading. Pure: no I/O, no logging."""
    cpu, temp = reading["cpu"], reading["temp"]
    ram, vram = reading["ram"], reading["vram"]

    # Dynamic styling based on thermal thresholds
    temp_style = "stable" if temp < TEMP_LIMIT else "alert"
    cpu_style = "metric" if cpu < LOAD_LIMIT else "alert"

    table = Table(title="ThermalGrid Telemetry Daemon", style="dim", expand=True)
    table.add_column("Sensor", justify="left", style="dim white", no_wrap=True)
    table.add_column("Current Value", justify="right", style="bold")
    table.add_column("Status", justify="center")

    table.add_row("CPU Load", f"[{cpu_style}]{cpu}%[/{cpu_style}]", "🟢" if cpu < LOAD_LIMIT else "🔴")
    table.add_row("Package Temp", f"[{temp_style}]{temp}°C[/{temp_style}]", "🟢" if temp < TEMP_LIMIT else "🔴")
    table.add_row("RAM Usage", f"[metric]{ram}%[/metric]", "🟢")
    table.add_row("VRAM Clock", f"[dim magenta]{vram} MHz[/dim magenta]", "🔵")

    return table


def main():
    console.clear()
    console.print("\n[dim]Initializing hardware hooks...[/dim]")

    try:
        # Sampling, logging and rendering are separated so that a redraw never
        # writes a row. Previously the table builder logged as a side effect, so
        # every repaint inserted another tick into the database.
        reading = sensors.sample()
        db.log_metrics(reading)

        with Live(render_dashboard(reading), refresh_per_second=2, console=console) as live:
            while True:
                reading = sensors.sample()
                db.log_metrics(reading)
                live.update(render_dashboard(reading))
                time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[dim]Telemetry run completed. Data saved to thermal_grid.db.[/dim]\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
