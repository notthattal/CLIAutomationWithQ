from setuptools import setup, find_packages

setup(
    name="system-advisor",
    version="1.0.0",
    description="AI-Powered System Monitor CLI Tool",
    author="Tal Erez",
    author_email="tal.erez@duke.edu",
    packages=find_packages(),
    py_modules=["cli"],
    install_requires=[
        "psutil>=7.0.0",
        "openai>=1.82.0",
        "python-dotenv>=1.1.0",
    ],
    entry_points={
        "console_scripts": [
            "system-advisor=cli:main",
            "email-monitor=automation_scripts.email_monitor:main",
            "performance-logger=automation_scripts.performance_logger:main",
        ],
    },
    python_requires=">=3.9",
)