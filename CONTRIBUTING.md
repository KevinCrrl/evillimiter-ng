# Contributing to EvilLimiter Next Generation

Thank you for your interest in contributing to `evillimiter-ng`! This document provides guidelines to help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Style Guidelines](#style-guidelines)

---

## Code of Conduct

Please use this project responsibly and ethically. Only use `evillimiter-ng` on networks you own or have explicit permission to test. Refer to [LEGAL.md](./LEGAL.md) for the full legal disclaimer.

---

## How Can I Contribute?

There are several ways to contribute:

- **Report bugs** — Test the tool and open an issue if you find unexpected behavior.
- **Fix bugs** — Browse open issues and submit a fix via Pull Request.
- **Improve documentation** — Keep the README and other docs up to date.
- **Add new features** — Propose and implement enhancements.

---

## Getting Started

1. **Fork** this repository by clicking the "Fork" button on GitHub.
2. **Clone** your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/evillimiter-ng.git
cd evillimiter-ng
```

3. **Create a new branch** for your changes:

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## Development Setup

### Requirements

- Linux distribution
- Python 3 or greater
- Root/sudo privileges (required for ARP spoofing and traffic shaping)

### Install in development mode

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install .
```

### Run the tool locally

```bash
sudo evillimiter-ng -i wlan0
```

---

## Submitting a Pull Request

1. Make sure your changes are on a dedicated branch (not `main`).
2. Test your changes thoroughly before submitting.
3. Commit with a clear and descriptive message:

```bash
git commit -m "feat: add support for IPv6 detection warning"
# or
git commit -m "fix: resolve crash on empty host scan"
# or
git commit -m "docs: update README installation steps"
```

4. Push your branch to your fork:

```bash
git push origin feat/your-feature-name
```

5. Open a **Pull Request** on GitHub against the `main` branch of the original repo.
6. Fill in the PR description explaining **what** you changed and **why**.

---

## Reporting Bugs

When opening a bug report, please include:

- Your Linux distribution and version
- Python version (`python --version`)
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages or stack traces

---

## Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style.
- Keep functions small and focused.
- Add comments for non-obvious logic.
- Do not commit unnecessary files (e.g., `__pycache__`, `.env`, `venv/`).

---

Thank you for helping keep `evillimiter-ng` alive and improving! 🚀
