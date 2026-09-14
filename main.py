import os
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

# Next to this script rather than in the working directory, so starting the daemon from
# somewhere else appends to the same history instead of quietly starting a new one.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thermal_grid.db")

console = Console(theme=custom_theme)
db = TelemetryDB(DB_PATH)
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

    # Estimates are labelled where they are shown: the fallback temperature is derived from
    # load and the VRAM clock is modelled, and neither should read as a measurement.
    temp_label = "Package Temp" if reading["temp_measured"] else "Package Temp (est.)"

    table.add_row("CPU Load", f"[{cpu_style}]{cpu}%[/{cpu_style}]", "🟢" if cpu < LOAD_LIMIT else "🔴")
    table.add_row(temp_label, f"[{temp_style}]{temp}°C[/{temp_style}]", "🟢" if temp < TEMP_LIMIT else "🔴")
    table.add_row("RAM Usage", f"[metric]{ram}%[/metric]", "🟢")
    table.add_row("VRAM Clock (modelled)", f"[dim magenta]{vram} MHz[/dim magenta]", "🔵")

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
        console.print(f"\n[dim]Telemetry run completed. Data saved to {DB_PATH}.[/dim]\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
