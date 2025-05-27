import subprocess
import json
import smtplib
import os
import argparse
import time
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv
import sys
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_system_status():
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

def get_system_report():
    try:
        result = subprocess.run(['python', 'cli.py'], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"CLI command failed with return code {result.returncode}: {result.stderr}")
            return f"CLI error: {result.stderr}"
        return result.stdout      
    except Exception as e:
        logger.error(f"Unexpected error getting system report: {e}")
        return f"Error getting system report: {e}"

def send_email(subject, body):
    try:
        username = os.getenv('EMAIL_USERNAME')
        password = os.getenv('EMAIL_PASSWORD')
        to_email = os.getenv('EMAIL_TO')
        
        if not all([username, password, to_email]):
            missing = []
            if not username:
                missing.append('EMAIL_USERNAME')
            if not password:
                missing.append('EMAIL_PASSWORD')
            if not to_email:
                missing.append('EMAIL_TO')
            logger.error(f"Missing email configuration: {', '.join(missing)}")
            return False
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = to_email
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return False

def check_system(args):
    try:
        data = get_system_status()
        if not data:
            logger.warning("Could not retrieve system status")
            return
        
        try:
            cpu = data['stats']['cpu']['overall_percent']
            memory = data['stats']['memory']['percent']
        except KeyError as e:
            logger.error(f"Missing expected data in system status: {e}")
            return
        except TypeError as e:
            logger.error(f"Invalid data type in system status: {e}")
            return
        
        logger.info(f"CPU: {cpu:.1f}%, Memory: {memory:.1f}%")
        
        if cpu > args.cpu_thresh or memory > args.mem_thresh:
            subject = f"System Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            body = get_system_report()
            
            if send_email(subject, body):
                logger.info("Alert email sent successfully!")
            else:
                logger.error("Failed to send alert email")            
    except Exception as e:
        logger.error(f"Unexpected error in check_system: {e}")

def main():
    try:
        parser = argparse.ArgumentParser(description='System Monitor and Notification System')
        parser.add_argument('--cpu-thresh', type=int, default=90, help='CPU Threshold to notify')
        parser.add_argument('--mem-thresh', type=int, default=95, help='Memory Threshold to notify')
        parser.add_argument('--time', type=int, default=300, help='Time interval to check system status in seconds')
        parser.add_argument('--monitor', action='store_true', help='Run continuously')
        
        args = parser.parse_args()
        
        # Validate arguments
        if args.cpu_thresh < 0 or args.cpu_thresh > 100:
            logger.error("CPU threshold must be between 0 and 100")
            sys.exit(1)
        if args.mem_thresh < 0 or args.mem_thresh > 100:
            logger.error("Memory threshold must be between 0 and 100")
            sys.exit(1)
        if args.time < 1:
            logger.error("Time interval must be at least 1 second")
            sys.exit(1)
        
        if args.monitor:
            logger.info("Starting continuous monitoring...")
            try:
                while True:
                    check_system(args)
                    time.sleep(args.time)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                sys.exit(1)
        else:
            check_system(args)    
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()