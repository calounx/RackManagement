# Contributing to RackManagement

Thank you for your interest in contributing to RackManagement! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/RackManagement.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

See [SETUP.md](SETUP.md) for detailed instructions on setting up the development environment.

### Quick Start

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-simple.txt
python init_db.py
uvicorn app.main:app --reload

# Frontend (when available)
cd frontend
npm install
npm run dev
```

## Code Style

- **Python**: Follow PEP 8 style guide
- **TypeScript/JavaScript**: Use ESLint and Prettier
- **Commits**: Write clear, concise commit messages

## Testing

Before submitting a PR, ensure:

- All tests pass
- Code follows the project's style guidelines
- Documentation is updated if needed
- No unnecessary dependencies are added

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update documentation for any new features
3. The PR will be merged once you have approval from maintainers

## Reporting Bugs

Use GitHub Issues to report bugs. Include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Screenshots if applicable

## Feature Requests

We welcome feature requests! Please:

- Check if the feature has already been requested
- Provide a clear description of the feature
- Explain why it would be useful
- Suggest how it might be implemented

## Device Specification Contributions

If you're contributing device specifications:

- Verify specifications from manufacturer datasheets
- Include the source URL
- Mark confidence level appropriately
- Test with real devices if possible

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards other community members

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.

Thank you for contributing!
