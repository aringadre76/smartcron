#!/bin/bash

echo "SmartCron Demo Runner"
echo "===================="
echo ""

if [ ! -d "models" ]; then
    mkdir models
fi

if [ ! -f "models/model.pkl" ]; then
    echo "No AI model found. Training a new model with synthetic data..."
    python3 -m smartcron.ai.train_model --generate 1000 --db ./smartcron_logs.db --output ./models/model.pkl
    echo ""
fi

echo "Starting SmartCron scheduler..."
echo "Press Ctrl+C to stop"
echo ""

python3 -m smartcron.core.scheduler --config-dir ./jobs --model ./models/model.pkl --db ./smartcron_logs.db --log-dir ./logs --interval 60

