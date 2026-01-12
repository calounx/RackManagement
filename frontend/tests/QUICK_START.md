# HomeRack E2E Tests - Quick Start Guide

## Prerequisites

1. **Application Running**: Frontend must be available at `http://lampadas.local:8080`
2. **Backend API**: Backend must be running and accessible
3. **Browsers Installed**: Playwright browsers installed

## Installation

```bash
# If Playwright is not installed
cd /home/calounx/repositories/homerack/frontend
npm install

# Install Playwright browsers
npx playwright install chromium

# Install system dependencies (if needed)
npx playwright install-deps chromium
```

## Running Tests

### Quick Commands

```bash
# Run all tests (headless)
npm run test:e2e

# Interactive UI mode (recommended for development)
npm run test:e2e:ui

# See browser while testing
npm run test:e2e:headed

# Debug mode with inspector
npm run test:e2e:debug

# View last test report
npm run test:e2e:report
```

### Advanced Usage

```bash
# Run specific test file
npx playwright test tests/e2e/page-navigation.spec.ts

# Run tests matching pattern
npx playwright test --grep "should create"

# Run single test
npx playwright test tests/e2e/page-navigation.spec.ts:15

# Update snapshots (if using visual testing)
npx playwright test --update-snapshots

# Generate code for tests
npx playwright codegen http://lampadas.local:8080
```

## Test Organization

```
tests/e2e/
├── page-navigation.spec.ts      # Navigation & routing (11 tests)
├── rack-management.spec.ts      # Rack CRUD & optimization (19 tests)
├── device-management.spec.ts    # Device CRUD & filtering (20 tests)
├── catalog-management.spec.ts   # Brands, models, types (18 tests)
└── dcim-integration.spec.ts     # NetBox integration (15 tests)

Total: 83 E2E tests
```

## Common Issues

### "Cannot connect to http://lampadas.local:8080"
- Ensure frontend is running: `cd frontend && npm run dev`
- Check if port 8080 is accessible

### "Target closed" or browser crashes
- Install system dependencies: `npx playwright install-deps chromium`
- Try headed mode to see what's happening: `npm run test:e2e:headed`

### Tests are slow
- Normal for first run (browser download)
- Subsequent runs are faster
- Use `--workers=2` for parallel execution (with caution)

### Selector not found
- UI might have changed
- Use codegen to find new selectors: `npx playwright codegen http://lampadas.local:8080`

## Debugging

### View Screenshots
```bash
# Screenshots saved on failure
ls test-results/*/test-failed-*.png
```

### View Videos
```bash
# Videos saved on failure
ls test-results/*/video.webm
```

### View Traces
```bash
# View trace for failed test
npx playwright show-trace test-results/*/trace.zip
```

### Interactive Debugging
```bash
# Open Playwright Inspector
npm run test:e2e:debug

# Then in the inspector:
# - Step through test
# - Inspect elements
# - View console logs
# - Execute commands
```

## Test Results

After running tests, view the HTML report:

```bash
npm run test:e2e:report
```

This opens an interactive report showing:
- Test pass/fail status
- Execution time
- Screenshots/videos on failure
- Test traces
- Detailed logs

## CI/CD Integration

For CI environments:

```bash
# Set CI environment variable
CI=true npm run test:e2e

# Results in test-results/ directory
# HTML report in playwright-report/
# JSON report in test-results/results.json
```

## Documentation

- **README.md** - Comprehensive test documentation
- **E2E_TEST_SUMMARY.md** - Implementation summary
- **QUICK_START.md** - This file

## Support

For issues or questions:
1. Check the README.md for detailed info
2. View Playwright docs: https://playwright.dev
3. Check test-results/ for failure details
4. Use debug mode to investigate
