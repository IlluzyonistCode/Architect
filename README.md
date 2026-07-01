# Architect

> *Design it. Describe it. Build it.*

![Python](https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white)

## Overview

Architect is a PyQt6 desktop application for 3D structural modeling using a custom AML (Architect Modeling Language). It translates declarative primitive descriptions into solid geometry through a boolean CSG pipeline and renders the result in an interactive viewport.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

---

## Features

|      | Component         | Details                                                                                                                                                                                                                                  |
| :--- | :---------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ⚙️  | **Architecture**  | <ul><li>Python-based application architecture</li><li>No containerization or orchestration layer detected</li></ul>               |
| 🔩  | **Code Quality**  | <ul><li>Written in **Python** (`.py` files)</li><li>No linter or formatter configuration detected (e.g., no `pyproject.toml`, `.flake8`, or `.pylintrc`)</li><li>No static analysis tooling identified</li></ul>                        |
| 📄  | **Documentation** | <ul><li>No dedicated documentation framework detected (e.g., no Sphinx, MkDocs)</li><li>No `docs/` directory or `README` identified in source metadata</li><li>License file present — baseline legal documentation covered</li></ul>    |
| 🔌  | **Integrations**  | <ul><li>CI/CD tooling references: `python`, `license`, `.py` — minimal pipeline integration</li><li>No external API, webhook, or service integrations detected</li><li>No cloud provider integration identified</li></ul>               |
| 🧩  | **Modularity**    | <ul><li>Python's native module system (`.py` files) implies potential for modular design</li><li>No package manager detected — dependency isolation unclear</li><li>No evidence of plugin or extension architecture</li></ul>            |
| ⚡️  | **Performance**   | <ul><li>No profiling or benchmarking tooling detected</li><li>No async framework (e.g., `asyncio`, `FastAPI`) identified</li><li>Performance characteristics undetermined without source code access</li></ul>                           |
| 🛡️  | **Security**      | <ul><li>No dependency vulnerability scanning detected (e.g., no `safety`, `bandit`)</li><li>No secrets management tooling identified</li><li>License file present — open-source compliance partially addressed</li></ul>                |

---

## Project Structure

```
└── Architect/
    ├── architect
    │   ├── __init__.py
    │   ├── __main__.py
    ├── LICENSE
    ├── README.md
    ├── studio
    │   ├── __init__.py
    └── studio.py
```

---

## Getting Started

### Prerequisites

- Python 3.10+ / Node.js 18+ *(depending on the stack above)*

### Installation

```sh
git clone "https://github.com/IlluzyonistCode/Architect
cd Architect"
pip install -r requirements.txt
```

### Usage

```sh
python main.py
```

---

## Contributing

- [Report Issues](https://github.com/IlluzyonistCode/Architect/issues)
- [Submit Pull Requests](https://github.com/IlluzyonistCode/Architect/pulls)
- [Discussions](https://github.com/IlluzyonistCode/Architect/discussions)

---

## License

Distributed under the [AGPL-3.0](LICENSE) license.
