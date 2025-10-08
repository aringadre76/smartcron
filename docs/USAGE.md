# SmartCron Usage Guide

## Installation

### From Source

```bash
git clone https://github.com/yourusername/smartcron.git
cd smartcron
pip install -r requirements.txt
python3 setup.py install
```

### Development Mode

```bash
pip install -r requirements.txt
```

## Configuration

### Job Configuration Format

Create YAML or JSON files in the jobs directory:

```yaml
job_name: "my_job"
command: "/path/to/script.sh"
preferred_time:
  - "01:00"
  - "03:00"
max_cpu: 50
max_memory_percent: 80
min_battery: 30
min_disk_free_gb: 10
min_idle_time_sec: 300
ai_aware: true
retry_on_fail: true
max_retries: 3
timeout_sec: 3600
enabled: true
schedule_window_start: "22:00"
schedule_window_end: "06:00"
```

### Configuration Options

- `job_name`: Unique identifier for the job
- `command`: Shell command to execute
- `preferred_time`: List of preferred execution times (HH:MM format)
- `max_cpu`: Maximum CPU usage percentage allowed
- `max_memory_percent`: Maximum memory usage percentage allowed
- `min_battery`: Minimum battery level required (for laptops)
- `min_disk_free_gb`: Minimum free disk space in GB
- `min_idle_time_sec`: Minimum user idle time in seconds
- `ai_aware`: Enable AI-based scheduling decisions
- `retry_on_fail`: Retry failed jobs
- `max_retries`: Maximum number of retry attempts
- `timeout_sec`: Job timeout in seconds
- `enabled`: Enable/disable the job
- `schedule_window_start`: Start of allowed execution window
- `schedule_window_end`: End of allowed execution window

## Running SmartCron

### As a Python Module

```bash
python3 -m smartcron.core.scheduler --config-dir /etc/smartcron/jobs
```

### With Custom Options

```bash
python3 -m smartcron.core.scheduler \
  --config-dir ./jobs \
  --model ./models/model.pkl \
  --db ./smartcron_logs.db \
  --log-dir ./logs \
  --interval 60
```

### As a systemd Service

```bash
sudo cp smartcron.service /etc/systemd/system/
sudo systemctl enable smartcron
sudo systemctl start smartcron
sudo systemctl status smartcron
```

## CLI Commands

### List All Jobs

```bash
python3 -m smartcron.cli.smartcronctl list
```

### Show Job Details

```bash
python3 -m smartcron.cli.smartcronctl show job_name
```

### System Status

```bash
python3 -m smartcron.cli.smartcronctl status
```

### Job Execution History

```bash
python3 -m smartcron.cli.smartcronctl history job_name --limit 20 --verbose
```

### Enable/Disable Jobs

```bash
python3 -m smartcron.cli.smartcronctl enable job_name
python3 -m smartcron.cli.smartcronctl disable job_name
```

## Training the AI Model

### Generate Synthetic Training Data

```bash
python3 -m smartcron.ai.train_model --generate 1000 --db ./smartcron_logs.db
```

### Train Model from Existing Data

```bash
python3 -m smartcron.ai.train_model --db /var/lib/smartcron/logs.db --output ./models/model.pkl
```

## Monitoring and Debugging

### View Logs

```bash
tail -f /var/log/smartcron/smartcron.log
tail -f /var/log/smartcron/job_name.log
```

### Check Database

```bash
sqlite3 /var/lib/smartcron/logs.db
sqlite> SELECT * FROM job_executions ORDER BY start_time DESC LIMIT 10;
sqlite> SELECT * FROM system_snapshots ORDER BY timestamp DESC LIMIT 10;
```

## Tips and Best Practices

1. Start with `ai_aware: false` for new jobs to test them first
2. Use appropriate timeout values to prevent hung jobs
3. Set reasonable constraints to avoid jobs never running
4. Monitor logs regularly to identify issues
5. Retrain the AI model periodically with real execution data
6. Use schedule windows for jobs that should only run during specific times
7. Test jobs manually before enabling them in SmartCron

## Troubleshooting

### Jobs Not Running

- Check if job is enabled: `smartcronctl show job_name`
- Check system constraints: `smartcronctl status`
- Review logs: `tail -f /var/log/smartcron/smartcron.log`
- Verify job configuration syntax

### AI Model Not Loading

- Check if model file exists: `ls -l models/model.pkl`
- Train a new model: `python3 -m smartcron.ai.train_model --generate 1000`
- SmartCron will fall back to heuristics if model is unavailable

### Permission Errors

- Ensure proper permissions on log directories
- Run as appropriate user (root for system-wide, user for personal use)
- Check file ownership: `ls -la /var/lib/smartcron/`

### High Resource Usage

- Reduce check interval: `--interval 120`
- Limit concurrent jobs in decision engine
- Adjust job constraints to be more restrictive

