import pytest
from unittest.mock import patch, Mock
from datetime import datetime
import cli


@pytest.fixture
def sample_stats():
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": {"overall_percent": 55.5, "per_core": [50.0, 60.0]},
        "memory": {"total": 8192, "available": 4096, "percent": 50.0, "used": 4096},
        "top_cpu_processes": [
            {"pid": 1234, "name": "proc1", "cpu_percent": 90.0},
            {"pid": 2345, "name": "proc2", "cpu_percent": 85.0},
        ],
        "top_memory_processes": [
            {"pid": 1234, "name": "proc1", "memory_percent": 45.0, "memory_info": Mock(rss=104857600)},
            {"pid": 2345, "name": "proc2", "memory_percent": 40.0, "memory_info": Mock(rss=52428800)},
        ],
    }


def test_format_bytes():
    assert cli.format_bytes(1024) == "1.0 KB"
    assert cli.format_bytes(1024 * 1024) == "1.0 MB"
    assert cli.format_bytes(-1) == "0 B"
    assert cli.format_bytes("bad") == "0 B"


def test_print_system_stats(sample_stats, capsys):
    cli.print_system_stats(sample_stats)
    output = capsys.readouterr().out
    assert "SYSTEM MONITOR" in output
    assert "CPU Usage" in output
    assert "Top CPU Processes" in output


def test_print_recommendations(capsys):
    recommendations = [
        {"severity": "critical", "message": "High CPU", "action": "Restart service"},
        {"severity": "info", "message": "All good", "action": "None"},
    ]
    cli.print_recommendations(recommendations)
    output = capsys.readouterr().out
    assert "[CRITICAL]" in output
    assert "High CPU" in output


def test_get_system_stats_success():
    monitor = cli.SystemMonitor()
    with patch("psutil.cpu_percent", side_effect=[70.0, [70.0, 60.0]]), \
         patch("psutil.virtual_memory") as mock_memory, \
         patch("psutil.process_iter") as mock_iter:

        mock_memory.return_value = Mock(total=8192, available=4096, percent=50.0, used=4096)
        mock_proc = Mock()
        mock_proc.info = {
            "pid": 1, "name": "test", "cpu_percent": 10.0, "memory_percent": 5.0, "memory_info": Mock(rss=1024)
        }
        mock_iter.return_value = [mock_proc]

        stats = monitor.get_system_stats()
        assert "cpu" in stats
        assert "memory" in stats
        assert isinstance(stats["top_cpu_processes"], list)


def test_ai_analysis_valid_response():
    analyzer = cli.AIAnalyzer()
    analyzer.client = Mock()
    analyzer.client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content="""
        [
            {
                "type": "performance",
                "severity": "info",
                "message": "CPU normal",
                "action": "Nothing needed"
            }
        ]
        """))
    ]
    stats = {
        "cpu": {"overall_percent": 70},
        "memory": {"percent": 40},
        "top_cpu_processes": [],
        "top_memory_processes": [],
    }
    result = analyzer.ai_analysis(stats)
    assert isinstance(result, list)
    assert result[0]["type"] == "performance"


def test_ai_analysis_malformed_response():
    analyzer = cli.AIAnalyzer()
    analyzer.client = Mock()
    analyzer.client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content="no json here"))
    ]
    stats = {
        "cpu": {"overall_percent": 80},
        "memory": {"percent": 60},
        "top_cpu_processes": [],
        "top_memory_processes": [],
    }
    result = analyzer.ai_analysis(stats)
    assert result is None or isinstance(result, list)

def test_ai_analysis_no_json_match():
    analyzer = cli.AIAnalyzer()
    analyzer.client = Mock()
    analyzer.client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content="no json found here"))
    ]
    stats = {
        "cpu": {"overall_percent": 99},
        "memory": {"percent": 99},
        "top_cpu_processes": [],
        "top_memory_processes": [],
    }
    assert analyzer.ai_analysis(stats) is None