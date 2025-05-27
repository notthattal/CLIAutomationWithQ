import argparse
from datetime import datetime
from dotenv import load_dotenv
import json
from openai import OpenAI
import os
import psutil
import time
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Error loading .env file: {e}")

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class SystemMonitor:
    def get_system_stats(self):
        try:
            # Get CPU usage
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_per_core = psutil.cpu_percent(percpu=True)
            except Exception as e:
                raise RuntimeError(f"Error getting CPU stats: {e}")
            
            # Get memory info
            try:
                memory = psutil.virtual_memory()
            except Exception as e:
                raise RuntimeError(f"Error getting memory info: {e}")
            
            # Get top processes by CPU and memory
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    # Ensure all required fields exist
                    if proc_info.get('name') and proc_info.get('pid'):
                        processes.append(proc_info)
                except Exception as e:
                    raise RuntimeError(f"Error adding cpu and memory processes to list: {e}")
        
            # Sort by CPU usage with safe sorting
            try:
                top_cpu_processes = sorted(
                    processes, 
                    key=lambda x: x.get('cpu_percent') or 0, 
                    reverse=True
                )[:10]
            except Exception as e:
                raise RuntimeError(f"Error sorting CPU processes: {e}")
            
            try:
                top_memory_processes = sorted(
                    processes, 
                    key=lambda x: x.get('memory_percent') or 0, 
                    reverse=True
                )[:10]
            except Exception as e:
                raise RuntimeError(f"Error sorting memory processes: {e}")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'overall_percent': cpu_percent,
                    'per_core': cpu_per_core
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'top_cpu_processes': top_cpu_processes,
                'top_memory_processes': top_memory_processes
            }     
        except Exception as e:
            raise RuntimeError(f"Critical error in get_system_stats: {e}")


class AIAnalyzer:
    def __init__(self):
        if OPENAI_API_KEY:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        else:
            raise RuntimeError(f"Missing OpenAI API key: {e}")
    
    def ai_analysis(self, stats):
        try:
            cpu_percent = stats.get('cpu', {}).get('overall_percent', 0)
            memory_percent = stats.get('memory', {}).get('percent', 0)
            top_cpu_processes = stats.get('top_cpu_processes', [])[:5]
            top_memory_processes = stats.get('top_memory_processes', [])[:5]
            
            prompt = f"""
            Analyze this system performance data and provide specific recommendations.
            Only flag issues if they are actually problematic:
            - CPU usage over 90% is concerning
            - Memory usage over 95% is concerning
            - Below these thresholds, the system is performing normally
            
            Current data:
            CPU Usage: {cpu_percent:.1f}%
            Memory Usage: {memory_percent:.1f}%
            
            Top CPU processes:
            {json.dumps(top_cpu_processes, indent=2)}
            
            Top Memory processes:
            {json.dumps(top_memory_processes, indent=2)}
            
            Provide 1-3 specific, actionable recommendations in JSON format:
            [
                {{
                    "type": "recommendation_type",
                    "severity": "info|warning|critical",
                    "message": "brief description",
                    "action": "specific action to take"
                }}
            ]
            """
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                timeout=30
            )
            
            content = response.choices[0].message.content
                
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                parsed_recommendations = json.loads(json_match.group())
                # Validate the structure
                if isinstance(parsed_recommendations, list) and all(
                    isinstance(rec, dict) and 
                    all(key in rec for key in ['type', 'severity', 'message', 'action'])
                    for rec in parsed_recommendations
                ):
                    return parsed_recommendations
        except Exception as e:
            raise RuntimeError(f"Error in AI analysis: {e}")
    
def format_bytes(bytes_value):
    try:
        if not isinstance(bytes_value, (int, float)) or bytes_value < 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"
    except Exception as e:
        raise RuntimeError(f"Error formatting bytes: {e}")

def print_system_stats(stats):
    try:
        print("\n" + "="*50)
        print(f"SYSTEM MONITOR - {stats.get('timestamp', 'Unknown time')}")
        print("="*50)
        
        cpu_info = stats.get('cpu', {})
        memory_info = stats.get('memory', {})
        
        cpu_percent = cpu_info.get('overall_percent', 0)
        memory_percent = memory_info.get('percent', 0)
        memory_used = memory_info.get('used', 0)
        memory_total = memory_info.get('total', 0)
        
        print(f"\nCPU Usage: {cpu_percent:.1f}%")
        print(f"Memory Usage: {memory_percent:.1f}% ({format_bytes(memory_used)}/{format_bytes(memory_total)})")
        
        top_cpu_processes = stats.get('top_cpu_processes', [])
        print(f"\nTop CPU Processes:")
        for i, proc in enumerate(top_cpu_processes[:5], 1):
            cpu_pct = proc.get('cpu_percent') or 0
            name = proc.get('name', 'Unknown')
            pid = proc.get('pid', 'Unknown')
            print(f"  {i}. {name} (PID: {pid}) - {cpu_pct:.1f}%")
        
        top_memory_processes = stats.get('top_memory_processes', [])
        print(f"\nTop Memory Processes:")
        for i, proc in enumerate(top_memory_processes[:5], 1):
            memory_info_proc = proc.get('memory_info')
            memory_mb = memory_info_proc.rss / 1024 / 1024 if memory_info_proc and hasattr(memory_info_proc, 'rss') else 0
            memory_pct = proc.get('memory_percent') or 0
            name = proc.get('name', 'Unknown')
            pid = proc.get('pid', 'Unknown')
            print(f"  {i}. {name} (PID: {pid}) - {memory_mb:.1f}MB ({memory_pct:.1f}%)")     
    except Exception as e:
        raise RuntimeError(f"Error printing system stats: {e}")

def print_recommendations(recommendations):
    try:
        print(f"\nRECOMMENDATIONS")
        print("-" * 30)
        
        for rec in recommendations:
            severity = rec.get('severity', 'info')
            message = rec.get('message', 'No message')
            action = rec.get('action', 'No action specified')
            
            severity_prefix = {
                'critical': '[CRITICAL]',
                'warning': '[WARNING]',
                'info': '[INFO]'
            }.get(severity, '[INFO]')
            
            print(f"\n{severity_prefix} {message}")
            print(f"   Action: {action}")       
    except Exception as e:
        raise RuntimeError(f"Error printing recommendations: {e}")

def main():
    parser = argparse.ArgumentParser(description='AI-Powered System Monitor')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=5, help='Update interval in seconds (default: 5)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()

    monitor = SystemMonitor()
    analyzer = AIAnalyzer()
        
    if args.watch:
        logger.info("Starting continuous monitoring...")
        while True:
            stats = monitor.get_system_stats()
            recommendations = analyzer.ai_analysis(stats)
            
            if args.json:
                output = {'stats': stats, 'recommendations': recommendations}
                print(json.dumps(output, indent=2))
            else:
                print("\033[2J\033[H")
                print_system_stats(stats)
                print_recommendations(recommendations)
            
            time.sleep(args.interval)
    else:
        stats = monitor.get_system_stats()
        recommendations = analyzer.ai_analysis(stats)
        
        if args.json:
            output = {'stats': stats, 'recommendations': recommendations}
            print(json.dumps(output, indent=2))
        else:
            print_system_stats(stats)
            print_recommendations(recommendations)     

if __name__ == '__main__':
    main()