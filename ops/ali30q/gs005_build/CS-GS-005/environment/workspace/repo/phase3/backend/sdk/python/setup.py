"""
SDK Package Setup

Install: pip install -e .
"""
from setuptools import setup, find_packages

setup(
    name="nautilus-oauth",
    version="1.0.0",
    description="Nautilus OAuth 2.0 Python SDK",
    author="Nautilus Team",
    author_email="support@nautilus.social",
    url="https://github.com/nautilus/nautilus-core",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
