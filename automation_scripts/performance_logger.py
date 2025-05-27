import subprocess
import json
import csv
import argparse
import time
from pathlib import Path
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_system_data():
    try:
        result = subprocess.run(['python', 'cli.py', '--json'], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"CLI command failed with return code {result.returncode}: {result.stderr}")
            return None
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output from CLI: {e}")
            return None    
    except Exception as e:
        logger.error(f"Unexpected error running CLI: {e}")
        return None

def log_to_csv(data, filename='system_performance.csv'):
    try:
        if not data or 'stats' not in data:
            logger.error("Invalid data structure provided to log_to_csv")
            return False
            
        stats = data['stats']
        
        row = {
            'timestamp': stats.get('timestamp', ''),
            'cpu_percent': stats.get('cpu', {}).get('overall_percent', 0),
            'memory_percent': stats.get('memory', {}).get('percent', 0),
            'memory_used_gb': stats.get('memory', {}).get('used', 0) / (1024**3),
            'memory_total_gb': stats.get('memory', {}).get('total', 0) / (1024**3),
            'top_cpu_process': '',
            'top_cpu_percent': 0,
            'top_memory_process': '',
            'top_memory_percent': 0
        }
        
        # Safely extract top process information
        top_cpu_processes = stats.get('top_cpu_processes', [])
        if top_cpu_processes and len(top_cpu_processes) > 0:
            top_cpu = top_cpu_processes[0]
            row['top_cpu_process'] = top_cpu.get('name', '')
            row['top_cpu_percent'] = top_cpu.get('cpu_percent') or 0
        
        top_memory_processes = stats.get('top_memory_processes', [])
        if top_memory_processes and len(top_memory_processes) > 0:
            top_memory = top_memory_processes[0]
            row['top_memory_process'] = top_memory.get('name', '')
            row['top_memory_percent'] = top_memory.get('memory_percent') or 0       
        
        # Check if file exists and is writable
        file_path = Path(filename)
        file_exists = file_path.exists()
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        return True      
    except Exception as e:
        logger.error(f"Unexpected error in log_to_csv: {e}")
        return False

def log_data(output_filename):
    try:
        data = get_system_data()
        if not data:
            logger.warning("Could not retrieve system data")
            return False
        
        if log_to_csv(data, output_filename):
            logger.info(f"Successfully logged data to {output_filename}")
            return True
        else:
            logger.error(f"Failed to log data to {output_filename}")
            return False         
    except Exception as e:
        logger.error(f"Unexpected error in log_data: {e}")
        return False

def validate_filename(filename):
    try:
        # Check if filename is valid
        if not filename or len(filename.strip()) == 0:
            return False
        
        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in filename for char in invalid_chars):
            return False
        
        # Try to create the path to check if it's valid
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        return True     
    except Exception:
        return False

def main():
    try:
        parser = argparse.ArgumentParser(description='System Performance Logger')
        parser.add_argument('--output', help='Output filename')
        parser.add_argument('--time', type=int, default=300, help='Time interval to check system status in seconds')
        parser.add_argument('--monitor', action='store_true', help='Run continuously')
        
        args = parser.parse_args()
        
        # Validate arguments
        if args.time < 1:
            logger.error("Time interval must be at least 1 second")
            sys.exit(1)
        
        output_filename = args.output if args.output else 'system_performance.csv'
        
        # Validate output filename
        if not validate_filename(output_filename):
            logger.error(f"Invalid output filename: {output_filename}")
            sys.exit(1)

        if args.monitor:
            logger.info(f"Starting continuous monitoring, logging to {output_filename}...")
            consecutive_failures = 0
            max_failures = 5
            
            try:
                while True:
                    success = log_data(output_filename)
                    
                    if success:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            logger.error(f"Too many consecutive failures ({max_failures}). Stopping monitoring.")
                            sys.exit(1)
                    
                    time.sleep(args.time)        
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                sys.exit(1)
        else:
            success = log_data(output_filename)
            if not success:
                sys.exit(1)            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()