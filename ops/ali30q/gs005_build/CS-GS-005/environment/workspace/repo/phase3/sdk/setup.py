from setuptools import setup, find_packages

setup(
    name="nautilus-agent-sdk",
    version="0.1.0",
    description="Nautilus Agent SDK - Connect AI agents to the Nautilus platform",
    author="Nautilus Team",
    url="https://github.com/chunxiaoxx/nautilus-core",
    py_modules=["nautilus_client"],
    install_requires=["httpx>=0.24.0"],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
)
