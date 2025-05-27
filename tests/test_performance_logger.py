import pytest
from unittest.mock import patch, Mock
import automation_scripts.performance_logger as pl
from pathlib import Path

@pytest.fixture
def mock_data():
    return {
        "stats": {
            "timestamp": "2025-05-26T19:00:00",
            "cpu": {"overall_percent": 75.0},
            "memory": {
                "percent": 60.0,
                "used": 4 * 1024**3,
                "total": 8 * 1024**3
            },
            "top_cpu_processes": [{"name": "proc1", "cpu_percent": 50.0}],
            "top_memory_processes": [{"name": "proc2", "memory_percent": 30.0}]
        }
    }

def test_get_system_data_success():
    mock_json = '{"stats": {"cpu": {"overall_percent": 70}, "memory": {"percent": 50}}}'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout=mock_json)
        result = pl.get_system_data()
        assert isinstance(result, dict)
        assert "stats" in result

def test_get_system_data_cli_error():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="fail")
        assert pl.get_system_data() is None

def test_get_system_data_json_error():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="bad json")
        assert pl.get_system_data() is None

def test_log_to_csv_valid_data(mock_data, tmp_path):
    csv_file = tmp_path / "log.csv"
    assert pl.log_to_csv(mock_data, str(csv_file)) is True
    content = csv_file.read_text()
    assert "timestamp" in content
    assert "cpu_percent" in content

def test_log_to_csv_invalid_data():
    assert pl.log_to_csv({}, "dummy.csv") is False

def test_log_data_success(tmp_path):
    with patch("automation_scripts.performance_logger.get_system_data") as mock_get, \
         patch("automation_scripts.performance_logger.log_to_csv") as mock_log:
        mock_get.return_value = {"stats": {}}
        mock_log.return_value = True
        assert pl.log_data(str(tmp_path / "out.csv")) is True

def test_log_data_failure(tmp_path):
    with patch("automation_scripts.performance_logger.get_system_data", return_value=None):
        assert pl.log_data(str(tmp_path / "out.csv")) is False


def test_validate_filename_valid(tmp_path):
    valid_file = tmp_path / "system_performance.csv"
    valid_file.parent.mkdir(parents=True, exist_ok=True)
    assert pl.validate_filename(str(valid_file)) is True

def test_validate_filename_valid():
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        mock_mkdir.return_value = None
        assert pl.validate_filename("valid_filename.csv") is True

def test_perf_logger_main_one_time(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--output", "test.csv"])
    with patch("automation_scripts.performance_logger.log_data", return_value=True):
        pl.main()

def test_perf_logger_main_invalid_time(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--time", "0"])
    with pytest.raises(SystemExit):
        pl.main()