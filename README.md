# CLI Automation User Manual

## Overview

This CLI tool is an AI-powered system monitoring and automation toolkit that helps monitor CPU and Memory usage, get recommendations, and automate logging and monitoring tasks.

## Project Structure

```
CLIAutomationWithQ/
├── automation_scripts/
│   ├── __init__.py                  # Marks this directory as a Python package
│   ├── email_monitor.py             # Monitors system stats and sends email alerts
│   └── performance_logger.py        # Logs system performance to a CSV
├── htmlcov/                         # (Optional) Coverage report output folder
├── .gitignore                       # Files to ignore
├── cli.py                           # Main CLI file
├── README.md                        # User Manual
├── requirements.txt                 # Dependencies for this project
├── setup.py                         # Setup script for packaging
├── tests/                           # Unit test folder
│   ├── test_cli.py                  # Tests for cli.py
│   ├── test_email_monitor.py        # Tests for automation_scripts/email_monitor.py
│   └── test_performance_logger.py   # Tests for automation_scripts/performance_logger.py
```

## Components

- **Main CLI Tool** (cli.py) - Main system monitoring CLI file that calls GPT for recommendations
- **Health Monitor** (email_monitor.py) - Automated alerting system that sends emails
- **Performance Logger** (performance_logger.py) - Data collection for trend analysis

## Installation

### Prerequisites
- Python 3.9 or higher
- Virtual environment (recommended)

### Setup

1. Clone Project
```bash
git clone https://github.com/notthattal/CLIAutomationWithQ.git
```

2. change directory to project dir
```bash
cd CLIAutomationWithQ
```

3. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

4. Install the package
```bash
pip install -e .
```

### Environment Configuration
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-openai-api-key-here
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=alerts@yourcompany.com
```

## Main CLI Tool

### Basic Usage

**Single system check:**
```bash
system-advisor
```

**Continuous monitoring:**
```bash
system-advisor --watch
```

**JSON output (for automation):**
```bash
system-advisor --json
```

### Command Options

|   Option   |         Description        |     Default    |
|------------|----------------------------|----------------|
| --watch    | Continuous monitoring mode |       N/A      |
| --interval | Update interval in seconds |        5       |
| --json     |    Output in JSON format   |       N/A      |

### Output Explanation

The CLI provides:
- **CPU Usage**: Overall CPU percentage and per-core breakdown
- **Memory Usage**: RAM usage with total/used amounts
- **Top Processes**: Highest CPU and memory consuming processes
- **AI Recommendations**: Intelligent suggestions for optimization

### AI Analysis

- Context-aware recommendations
- Considers process types and system state
- More nuanced suggestions

## Automation Scripts

### Email Monitor

Automatically monitors your system and sends email alerts when thresholds are exceeded.

#### Usage

1. One-time check
```bash
email-monitor
```

2. Continuous monitoring
```bash
email-monitor --monitor
```

3. Custom thresholds
```bash
email-monitor --cpu-thresh 80 --mem-thresh 85
```

4. Custom check interval (in seconds)
```bash
email-monitor --monitor --time 15
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `--cpu-thresh` | CPU threshold percentage | 90% |
| `--mem-thresh` | Memory threshold percentage | 95% |
| `--time` | Check interval in seconds | 300 |
| `--monitor` | Run continuously | N/A |

#### Email Alerts
When thresholds are exceeded the email-monitor:
1. Captures the full system report from the main CLI
2. Sends an email with the complete analysis
3. Logs the alert to the console

### Performance Logger

Collects system performance data over time and outputs it to a CSV for trend analysis.

#### Usage
1. Log to CSV file
```bash
performance-logger
```

2. Setting a custom output file
```bash
performance-logger --output my_data.csv
```

3. Continuous monitoring
```bash
performance-logger --monitor
```
4. Custom check interval (in seconds)
```bash
performance-logger --monitor --time 15
```

#### Options
| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Custom filename | system_performance.csv |
| `--time` | Check interval in seconds | 300 |
| `--monitor` | Run continuously | N/A |

#### Data Collected
- Timestamps
- CPU percentages
- Memory percentages
- Memory used/total (in GB)
- Top CPU process and usage
- Top memory process and usage

## Workflow Examples

### Daily Monitoring
```bash
# Quick system check
system-advisor

# Set up continuous health monitoring
email-monitor --monitor --cpu-thresh 80 --mem-thresh 85

# Or start logging performance data to a csv to use for trend analysis later
performance-logger --monitor
```

## Troubleshooting

### Common Issues

**"Command not found" errors:**
- Ensure you've run `pip install -e .`
- Check that your virtual environment is activated
- Verify the commands are `system-advisor`, `email-monitor`, `performance-logger`

**Email alerts not working:**
- Verify your `.env` file contains correct email credentials
- For Gmail, use an App Password, not your regular password
- Check that `EMAIL_USERNAME`, `EMAIL_PASSWORD`, and `EMAIL_TO` are set

**AI analysis not working:**
- Verify your `OPENAI_API_KEY` is set in `.env`
- Check your OpenAI account has credits

**High CPU/Memory false positives:**
- Adjust thresholds using `--cpu-thresh` and `--mem-thresh`
- Some system processes normally use high resources
- Consider the context of what you're currently running

### File Locations

- **Main CLI**: `cli.py`
- **Email Monitor**: `automation_scripts/email_monitor.py`
- **Performance Logger**: `automation_scripts/performance_logger.py`
- **Configuration**: `.env`
- **Setup**: `setup.py`
- **Requirements**: `requirements.txt`
- **Test Files**: `tests/`
- **Coverage Report**: `htmlcov/`

### Logs

- **Email Monitor**: Console output and email alerts
- **Performance Data**: `system_performance.csv` and console output
- **System Logs**: Console output


# Python Test Suite

This section will explain the automated test suite built using `pytest` and `pytest-cov`.

## What the Tests Cover

### test_cli.py

- Tests system statistics, extraction and formatting
- Validates correct parsing of CPU and memory usage and their respective processes
- Mocks `psutil` and OpenAI API calls

### test_email_monitor.py

- Mocks subprocess calls to `cli.py`
- Validates error handling for CLI failure and bad JSON
- Tests email notification logic
- Covers CLI `main()` logic and argument validation

### test_performance_logger.py

- Tests logging system data to CSV
- Mocks CLI subprocess and file writing calls
- Validates filenames and monitoring logic
- Covers both single executions and runs with continuous monitoring

## How the Tests Work

- **Mocking**: Tests avoid real subprocess calls and API usage by mocking:
  - `subprocess.run`
  - `smtplib.SMTP`
  - `psutil`
  - `openai.OpenAI`

- **Fixtures**: Reusable sample data for system stats is provided by `@pytest.fixture`.

- **Monkeypatching**: CLI argument parsing is tested using `monkeypatch.setattr("sys.argv", [...])`.

- **Error Paths**: Tests include bad input cases to ensure failure handling and logging are robust.

## Running Tests
```bash
pytest --cov=. --cov-report=html
```
- *Note*: Make sure you run the above command from the root of the project folder

## AI Usage

- AI was used as a source for documentation as well as to help with the creation of the test suite and for understanding how to implement error handling

## Version

System Advisor v1.0.0
