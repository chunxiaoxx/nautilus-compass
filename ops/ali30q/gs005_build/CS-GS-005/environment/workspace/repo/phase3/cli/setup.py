"""Nautilus CLI · setup.py for pip install."""
from setuptools import setup, find_packages

setup(
    name="nautilus-cli",
    version="0.1.0",
    description="Nautilus CLI (product: Nautilus Soul) · multi-agent audit with stake-backed cert · github.com/chunxiaoxx/nautilus-core",
    long_description=(
        "Nautilus CLI · 国产 multi-agent audit CLI · 类 Claude Code 但加 audit cert + stake-backed. "
        "Dispatch a task spec · 3-agent council audits · receive HMAC-SHA256 signed JSON-LD certificate. "
        "Usage: `nautilus audit my_spec.md --budget 100 --watch`"
    ),
    long_description_content_type="text/plain",
    author="chunxiaoxx",
    author_email="chunxiaoxx@gmail.com",
    url="https://github.com/chunxiaoxx/nautilus-core",
    license="Apache-2.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],  # stdlib only · keep install footprint zero
    entry_points={
        "console_scripts": [
            "nautilus=nautilus_cli.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)
