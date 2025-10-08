# SmartCron: AI-Augmented Cron Job Scheduler

SmartCron is a next-generation replacement for the traditional `cron` daemon that integrates AI-based decision-making to determine the optimal time and conditions to run jobs.

## Features

- Intelligent job scheduling based on system state
- AI predictions for optimal execution times
- System resource monitoring (CPU, RAM, battery, disk)
- Constraint-based execution (only run when conditions are met)
- Comprehensive logging and job history
- Easy-to-use CLI for job management
- Backward-compatible with static scheduling

## Quick Start

### Installation

```bash
pip install -r requirements.txt
python3 setup.py install
```

### Basic Usage

1. Create a job configuration in `jobs/` directory:

```yaml
job_name: "my_backup"
command: "/home/user/scripts/backup.sh"
preferred_time: ["01:00"]
max_cpu: 50
min_battery: 30
ai_aware: true
enabled: true
```

2. Run the scheduler:

```bash
python3 -m smartcron.core.scheduler --config-dir ./jobs
```

3. Use the CLI to manage jobs:

```bash
python3 -m smartcron.cli.smartcronctl list
python3 -m smartcron.cli.smartcronctl show my_backup
python3 -m smartcron.cli.smartcronctl status
```

### Training the AI Model

Generate synthetic training data and train the model:

```bash
python3 -m smartcron.ai.train_model --generate 1000 --db ./smartcron_logs.db --output ./models/model.pkl
```

## Running Tests

```bash
python3 -m pytest tests/
```

Or run individual test files:

```bash
python3 tests/test_system_metrics.py
python3 tests/test_config_parser.py
python3 tests/test_decision_engine.py
python3 tests/test_job_executor.py
```

## System Requirements

- Python 3.8+
- Linux operating system
- Required packages listed in requirements.txt

## Architecture

SmartCron consists of several core components:

- **System Monitor**: Collects CPU, RAM, battery, disk metrics
- **AI Core**: Predicts optimal execution times using ML models
- **Decision Engine**: Applies rules and AI scores to make run decisions
- **Job Executor**: Executes jobs with retry and timeout support
- **Logger**: Comprehensive logging and history tracking

## Documentation

See `plan.md` for detailed architecture and design decisions.

## License

MIT License