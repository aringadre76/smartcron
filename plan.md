# 🧠 SmartCron: AI-Augmented Cron Job Scheduler

---

## 📌 Overview

**SmartCron** is a next-generation replacement for the traditional `cron` daemon that integrates **AI-based decision-making** to determine the *optimal time* and *conditions* to run jobs. Unlike conventional schedulers that operate purely on time-based triggers, SmartCron considers system state, historical outcomes, user behavior, and predictive AI models.

---

## 🚀 Project Goals

- Intelligent decision-making for job scheduling
- Reduce failed or wasteful executions
- Improve system responsiveness during peak usage
- Provide dynamic, context-aware automation
- Be backward-compatible (fallback to static scheduling)

---

## 📐 System Architecture

### 🧭 High-Level Diagram

```
                 +-------------------------+
                 |    User Job Configs     |
                 | (YAML / JSON files)     |
                 +-----------+-------------+
                             |
                             v
+------------------+     +--------+      +----------------+
| System Monitor   | --> | AI Core| -->  | Decision Engine|
| (load, battery,  |     +--------+      +----------------+
| user idle, etc.) |                         |
+------------------+                         |
                                             v
                                     +-------------------+
                                     | Smart Job Executor|
                                     +-------------------+
                                             |
                                             v
                                 +-------------------------+
                                 | Logging + History Store |
                                 +-------------------------+
```

---

## ⚙️ Core Components

### 1. 🧾 Job Configuration Manager

- Parses job definitions from YAML or JSON files.
- Each job can define:
  - Command to run
  - Constraints (CPU, RAM, battery)
  - Scheduling window
  - AI toggle
  - Historical weight/preference

📁 **Directory:** `/etc/smartcron/jobs/`  
📄 **Example:** `backup.yaml`

```yaml
job_name: "daily_backup"
command: "/home/user/scripts/backup.sh"
preferred_time: ["01:00", "03:00"]
max_cpu: 50       # %
min_battery: 30   # %
ai_aware: true
retry_on_fail: true
```

---

### 2. 📊 System Monitor

- Collects system metrics:
  - CPU load: `/proc/loadavg`, `psutil.getloadavg()`
  - RAM usage: `/proc/meminfo`, `psutil.virtual_memory()`
  - Battery status: `/sys/class/power_supply/`, `psutil.sensors_battery()`
  - User idle time: `xprintidle`, D-Bus
  - Disk space: `df -h`, `psutil.disk_usage()`

---

### 3. 🧠 AI Core

- Predicts optimal execution time using:
  - Supervised learning (Random Forest, LightGBM)
  - Input Features:
    - CPU load
    - User idle time
    - RAM usage
    - Historical job success/failure
  - Output:
    - `probability_of_success`
    - `expected_runtime`
    - `decision_score`

> Model can be trained offline and exported as `.pkl` or `.onnx`.

---

### 4. 🧮 Decision Engine

- Applies rules + AI scores to decide:
  - Run now
  - Defer
  - Reschedule
- Rule engine handles:
  - Hard constraints (battery, disk, time window)
  - Soft constraints (AI predictions)
  - Priority queueing if multiple jobs are due

---

### 5. 🏃 Job Executor

- Forks and runs jobs in a sandboxed environment (optional: `systemd-run`, `firejail`)
- Captures:
  - Exit code
  - Stdout/stderr
  - Execution time
- Sends signals for:
  - Timeout
  - Retry (if configured)

---

### 6. 📝 Logging + History

- Logs all executions with metadata:
  - Start time, end time, result
  - System state snapshot
  - AI decision reason
- Stored in:
  - SQLite DB: `/var/lib/smartcron/logs.db`
  - Or log files: `/var/log/smartcron/jobname.log`
- Used for retraining AI model

---

## 🧰 Technology Stack

| Layer | Tools / Libraries | Purpose |
|-------|--------------------|---------|
| Language | **Python 3.11+** | Rapid dev, AI support |
| AI / ML | `scikit-learn`, `LightGBM`, `pandas`, `joblib` | Modeling, prediction |
| Monitoring | `psutil`, `/proc`, `acpi`, `xprintidle` | System stats |
| Config Mgmt | `PyYAML`, `jsonschema` | Job definitions |
| Daemon Mgmt | `systemd` (or custom) | Run as service |
| Logging | `logging`, `sqlite3`, `logrotate` | Auditing, feedback |
| CLI Tooling | `argparse`, `rich` | Status & control |
| Security | `firejail`, `subprocess`, `os.fork()` | Sandboxing jobs |

---

## 📦 Package Structure

```
smartcron/
├── ai/
│   ├── model.py          # Prediction logic
│   └── train_model.py    # Offline training script
├── core/
│   ├── scheduler.py      # Main loop
│   ├── decision.py       # Decision engine
│   └── job_executor.py   # Forks jobs
├── config/
│   └── parser.py         # Loads job YAMLs
├── monitor/
│   └── system_metrics.py # CPU, RAM, battery, idle
├── utils/
│   └── logger.py         # Logging setup
├── cli/
│   └── smartcronctl.py   # CLI to manage jobs
└── smartcron.service     # systemd service file
```

---

## 📈 AI Model Design

### Model Type

- `RandomForestClassifier` or `LightGBMClassifier`

### Input Features (per job run):

| Feature | Description |
|--------|-------------|
| avg_cpu_load_5m | Average load over 5 minutes |
| ram_percent_used | RAM in use |
| battery_level | Current battery level |
| is_charging | True/False |
| idle_time_sec | User idle time in seconds |
| last_job_success | Binary (1/0) |
| time_of_day | Encoded hour (0–23) |

### Output

- `run_now_probability` → Used as input to decision engine

---

## ✅ Functional Features

| Feature | Status |
|--------|--------|
| Static scheduling | ✅ Supported |
| AI-based scheduling | ✅ Supported |
| System state constraints | ✅ CPU, RAM, battery |
| Logging and retry | ✅ Implemented |
| CLI interface (`smartcronctl`) | ✅ |
| Live job preview / status | ✅ |
| Training script for AI model | ✅ |

---

## 🧪 Testing Plan

- Unit test each module: monitoring, AI, executor
- Integration test: job lifecycle from config → decision → execution → logging
- Stress test: simulate multiple jobs under system load
- Regression test: fall back to fixed time if AI fails

---

## 📊 Future Improvements

- Online learning (retrain AI models continuously)
- Dashboard (web UI) for job history + metrics
- Docker & Kubernetes integration
- NLP job description parsing (e.g. “run backup when I’m idle”)
- User policy profiles
- System-wide scheduling optimization (not per-job)

---

## 🚀 Deployment

### As a systemd service:

```bash
sudo cp smartcron.service /etc/systemd/system/
sudo systemctl enable smartcron
sudo systemctl start smartcron
```

### Job directory:

```bash
/etc/smartcron/jobs/
```

---

## 📂 GitHub Repo Structure (Suggested)

```bash
$ tree -L 2
smartcron/
├── README.md
├── docs/
│   └── architecture.md
├── smartcron/
│   ├── ai/
│   ├── core/
│   ├── config/
│   ├── monitor/
│   └── cli/
├── tests/
│   └── test_scheduler.py
├── models/
│   └── model.pkl
├── jobs/
│   └── example_job.yaml
├── smartcron.service
└── requirements.txt
```

---

## 🧠 Summary

SmartCron modernizes job scheduling on Linux by integrating artificial intelligence into the scheduling loop. It balances system health, user context, and predictive analysis to make smarter choices, improving system efficiency and automation reliability.
