import pytest
from unittest.mock import patch, Mock
from automation_scripts import email_monitor

def test_get_system_status_success():
    mock_output = '{"stats": {"cpu": {"overall_percent": 80}, "memory": {"percent": 50}}}'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout=mock_output)
        result = email_monitor.get_system_status()
        assert isinstance(result, dict)
        assert "stats" in result

def test_get_system_status_failure_returncode():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="Error")
        result = email_monitor.get_system_status()
        assert result is None

def test_get_system_status_invalid_json():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="not json")
        result = email_monitor.get_system_status()
        assert result is None

def test_get_system_status_exception():
    with patch("subprocess.run", side_effect=Exception("Boom")):
        result = email_monitor.get_system_status()
        assert result is None

def test_get_system_report_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="Report OK")
        result = email_monitor.get_system_report()
        assert "Report OK" in result

def test_get_system_report_error_returncode():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="Failure")
        result = email_monitor.get_system_report()
        assert "CLI error" in result

def test_get_system_report_exception():
    with patch("subprocess.run", side_effect=Exception("Boom")):
        result = email_monitor.get_system_report()
        assert "Error getting system report" in result

def test_send_email_success():
    with patch.dict("os.environ", {
        "EMAIL_USERNAME": "user@example.com",
        "EMAIL_PASSWORD": "pass",
        "EMAIL_TO": "to@example.com"
    }), patch("smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value
        result = email_monitor.send_email("subject", "body")
        assert result is True
        instance.send_message.assert_called_once()

def test_send_email_missing_env():
    with patch.dict("os.environ", {}, clear=True):
        result = email_monitor.send_email("subject", "body")
        assert result is False

def test_send_email_exception():
    with patch.dict("os.environ", {
        "EMAIL_USERNAME": "user@example.com",
        "EMAIL_PASSWORD": "pass",
        "EMAIL_TO": "to@example.com"
    }), patch("smtplib.SMTP", side_effect=Exception("fail")):
        result = email_monitor.send_email("subject", "body")
        assert result is False

def test_check_system_triggers_email():
    mock_data = {
        "stats": {
            "cpu": {"overall_percent": 95},
            "memory": {"percent": 96}
        }
    }
    args = Mock(cpu_thresh=90, mem_thresh=90)
    with patch("automation_scripts.email_monitor.get_system_status", return_value=mock_data), \
         patch("automation_scripts.email_monitor.get_system_report", return_value="report..."), \
         patch("automation_scripts.email_monitor.send_email", return_value=True):
        email_monitor.check_system(args)

def test_check_system_no_data():
    args = Mock(cpu_thresh=90, mem_thresh=90)
    with patch("automation_scripts.email_monitor.get_system_status", return_value=None):
        email_monitor.check_system(args)

def test_check_system_invalid_keys():
    args = Mock(cpu_thresh=90, mem_thresh=90)
    bad_data = {"stats": {}}
    with patch("automation_scripts.email_monitor.get_system_status", return_value=bad_data):
        email_monitor.check_system(args)

def test_email_monitor_main_single_run(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--cpu-thresh", "50", "--mem-thresh", "50"])
    with patch("automation_scripts.email_monitor.check_system") as mock_check:
        email_monitor.main()
        mock_check.assert_called_once()

def test_email_monitor_main_bad_thresh(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--cpu-thresh", "-5"])
    with pytest.raises(SystemExit):
        email_monitor.main()