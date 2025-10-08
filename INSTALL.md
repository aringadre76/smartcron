# SmartCron Installation Guide

## Quick Install

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install SmartCron

```bash
python3 setup.py install
```

Or for development mode:

```bash
python3 setup.py develop
```

## Running a Demo

The easiest way to try SmartCron is to use the demo script:

```bash
./run_demo.sh
```

This will:
1. Generate synthetic training data
2. Train an AI model
3. Start the scheduler with example jobs

## Manual Setup

### 1. Create Required Directories

For system-wide installation (requires root):

```bash
sudo mkdir -p /etc/smartcron/jobs
sudo mkdir -p /var/lib/smartcron
sudo mkdir -p /var/log/smartcron
sudo mkdir -p /opt/smartcron/models
```

For user installation:

```bash
mkdir -p ./jobs
mkdir -p ./logs
mkdir -p ./models
```

### 2. Copy Example Job Configurations

For system-wide:

```bash
sudo cp jobs/*.yaml /etc/smartcron/jobs/
```

For user installation:

```bash
cp jobs/*.yaml ./jobs/
```

### 3. Train the AI Model

```bash
python3 -m smartcron.ai.train_model --generate 1000 --db ./smartcron_logs.db --output ./models/model.pkl
```

### 4. Run the Scheduler

For user installation:

```bash
python3 -m smartcron.core.scheduler --config-dir ./jobs --model ./models/model.pkl --db ./smartcron_logs.db --log-dir ./logs
```

For system-wide installation:

```bash
sudo python3 -m smartcron.core.scheduler
```

## systemd Service Installation

### 1. Edit Service File

Edit `smartcron.service` to match your installation paths.

### 2. Install Service

```bash
sudo cp smartcron.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smartcron
```

### 3. Start Service

```bash
sudo systemctl start smartcron
sudo systemctl status smartcron
```

### 4. View Logs

```bash
sudo journalctl -u smartcron -f
```

## Verification

### Check System Status

```bash
python3 -m smartcron.cli.smartcronctl status
```

### List Jobs

```bash
python3 -m smartcron.cli.smartcronctl list
```

### Run Tests

```bash
python3 -m pytest tests/ -v
```

Or run individual tests:

```bash
python3 tests/test_system_metrics.py
python3 tests/test_config_parser.py
python3 tests/test_decision_engine.py
python3 tests/test_job_executor.py
```

## Troubleshooting

### Permission Issues

If running as non-root user, make sure to use local directories instead of system paths.

### Missing Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### AI Model Not Found

Generate a new model:

```bash
python3 -m smartcron.ai.train_model --generate 1000 --output ./models/model.pkl
```

## Next Steps

1. Read `docs/USAGE.md` for detailed usage instructions
2. Create your own job configurations in the jobs directory
3. Monitor logs to see how jobs are being scheduled
4. Train the AI model with real execution data for better predictions

