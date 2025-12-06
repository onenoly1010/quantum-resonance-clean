# Changelog

All notable changes to the Quantum Resonance Clean project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-10

### Added
- Initial clean install infrastructure
- Automated installation scripts for Linux/macOS (`install.sh`) and Windows (`install.ps1`)
- Docker support with Dockerfile and docker-compose.yml
- FastAPI server with health check and info endpoints
- Comprehensive README with installation and usage instructions
- Getting Started documentation
- Environment configuration template (.env.example)
- Python dependency management with requirements.txt
- Comprehensive .gitignore for Python, Node.js, and IDEs
- Basic project structure (server/, frontend/, docs/)

### Security
- FastAPI updated to version 0.115.6 (fixes CVE for ReDoS vulnerability)
- CodeQL security scanning implemented (0 vulnerabilities)
- All dependencies verified against GitHub Advisory Database

### Documentation
- Installation guide for multiple platforms
- API endpoint documentation
- Troubleshooting section
- Docker deployment instructions

[1.0.0]: https://github.com/onenoly1010/quantum-resonance-clean/releases/tag/v1.0.0
