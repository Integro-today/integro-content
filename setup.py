"""Setup configuration for Integro package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="integro",
    version="0.1.0",
    author="Integro Team",
    description="A generic, configurable AI agent framework with runtime tool configuration and Qdrant memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "agno>=0.1.0",
        "pydantic>=2.0.0",
        "qdrant-client>=1.7.0",
        "nanoid>=2.0.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0",
        "anyio>=4.0.0",
        "groq>=0.4.0",
        "sqlalchemy>=2.0.0",
        "textual>=0.47.0",
        "click>=8.0.0",
        "pyyaml>=6.0.0",
        "aiosqlite>=0.19.0",
        "fastembed>=0.1.0",
        "langchain-text-splitters>=0.0.1",
        "pypdf>=3.0.0",
        "python-docx>=1.0.0",
        "openpyxl>=3.1.0",
        "ebooklib>=0.18",
        "python-pptx>=0.6.0",
        "markdown>=3.5.0",
        "beautifulsoup4>=4.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "integro=integro.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)