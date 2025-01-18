import re
from pathlib import Path

from setuptools import find_packages, setup

version_raw = (Path(__file__).parent / "red_orm" / "version.py").read_text()
version = re.compile(r'__version__\s=\s"(\d+\.\d+.\d)').search(version_raw).group(1)


setup(
    name="red-orm",
    version=version,
    author="Vertyco",
    url="https://github.com/vertyco/red-orm",
    author_email="alex.c.goble@gmail.com",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    description="Postgres and SQLite extensions for Red-DiscordBot",
    packages=find_packages(),
    keywords=[
        "postgres",
        "sqlite",
        "piccolo",
        "red",
        "redbot",
        "red-discordbot",
        "red",
        "bot",
        "discord",
        "database",
        "async",
        "asyncpg",
        "aiosqlite",
        "orm",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Pydantic :: 2",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    install_requires=["piccolo>=1.0.0", "discord.py", "Red-DiscordBot"],
    python_requires=">=3.10",
    project_urls={
        "Homepage": "https://github.com/vertyco/red-orm",
        "Bug Tracker": "https://github.com/vertyco/red-orm/issues",
        "Changelog": "https://github.com/vertyco/red-orm/blob/main/CHANGELOG.md",
    },
)
