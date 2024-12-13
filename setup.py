"""
ZQ Data - 基于 Polars 的行情数据服务
"""
import os
from setuptools import setup, find_packages

# 读取 README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取 requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# 包信息
setup(
    name="zq_data",
    version="0.1.0",
    author="ZQ Team",
    author_email="",
    description="基于 Polars 的高性能金融市场数据服务",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/zq_data",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/zq_data/issues",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=find_packages(include=["zq_data", "zq_data.*"]),
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "zq_data=zq_data.server.app:main",
        ],
    },
    package_data={
        "zq_data": ["py.typed"],
    },
    include_package_data=True,
    zip_safe=False,
)
