# Performance evidence

Ubuntu 24.04 x86_64, CPython 3.14.7, actual native XKB compilation against temporary distro copies.
These timings include filesystem/journal/native validation but exclude setup,
authorization,
and desktop activation. They are local observations, not macOS or hosted-run results.

| Scenario | Result | Seconds |
|---|---|---:|
| fresh install | installed | 0.2012 |
| current invocation 1 | unchanged | 0.0308 |
| current invocation 2 | unchanged | 0.0313 |
| current invocation 3 | unchanged | 0.0325 |
| legacy update | updated | 0.1338 |
| missing registration repair | repaired | 0.1585 |

Local runs meet the 5-second inspection/no-op and 30-second apply budgets.
macOS baseline measurements remain pending; T058 remains open.
