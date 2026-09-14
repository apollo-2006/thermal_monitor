# thermal_monitor

A terminal telemetry daemon. It samples CPU load, package temperature and memory use twice
a second, renders them as a live-updating table, and writes every tick to a local SQLite
database so a run can be reviewed after the fact.

## How it works

* **One coherent sample per tick.** `HardwareSensors.sample()` polls the CPU exactly
  once and threads that reading through the derived values. Sampling per-sensor meant
  three separate blocking `cpu_percent` calls per frame and three different load figures
  inside a single row.
* **Load covers the whole run.** Each tick reports CPU load since the previous tick
  rather than blocking for a 0.1 s poll, which measured one sixth of every loop and
  slowed it to 1.7 Hz.
* **Thermal readings with a fallback.** Package temperature is read from `coretemp`
  (Intel), `k10temp` or `zenpower` (AMD), or `cpu_thermal` (ARM) via
  `psutil.sensors_temperatures`. Those thermal zones are not exposed on Windows or inside
  WSL, so when the read fails the daemon models a curve from load instead of reporting
  nothing, labels the row `(est.)`, and stores the tick with `temp_measured = 0`.
* **Sampling, logging and rendering are separate.** The table builder is pure. Only the
  loop writes rows, so a repaint never inserts a duplicate tick.
* **Persistent history.** Each tick lands in the `system_metrics` table of
  `thermal_grid.db`, next to `main.py` wherever you start it from, so you can query a
  session afterwards:

  ```sql
  SELECT MAX(cpu_temp), AVG(cpu_usage) FROM system_metrics
  WHERE timestamp > '2026-08-30' AND temp_measured = 1;
  ```

## Thresholds

Rows turn red past the limits set at the top of `main.py`: 80% sustained CPU load, 65 °C
package temperature.

## Run

```bash
git clone https://github.com/apollo-2006/thermal_monitor.git
cd thermal_monitor

pip install -r requirements.txt
python main.py
```

Ctrl-C stops the run and closes the database cleanly.

## Layout

```
main.py             loop, thresholds, table rendering
core/sensors.py     psutil reads, thermal fallback, one-shot sample()
core/storage.py     SQLite schema and per-tick inserts
```

## Known limits

* **VRAM clock is modelled, not measured.** `get_vram_clock_sim` steps through the three
  clock states a card uses, keyed off system activity. Reading the real value needs
  PyNVML (NVIDIA) or PyAMDGPUInfo (AMD).
* **The temperature fallback is an estimate.** When no thermal driver is available the
  number shown is derived from load, not measured from the die. It is labelled as such on
  screen and in the database.
* **Every tick commits.** At 2 Hz that is two `fsync`-backed commits a second, which is
  fine for a foreground session and wasteful for a long-running daemon.

## License

MIT. See [LICENSE](LICENSE).

## Author

**Abir Deol** · [abirdeol.tech](https://abirdeol.tech)
