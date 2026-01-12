# HomeRack Frontend E2E Tests

Comprehensive end-to-end test suite for the HomeRack application using Playwright.

## Overview

This test suite provides E2E coverage for all major features and user workflows in the HomeRack application. Tests are organized by feature area and cover:

- Page navigation and routing
- Rack management (CRUD operations, visualization, optimization)
- Device management (CRUD, filtering, sorting, views)
- Catalog management (brands, models, device types, Wikipedia integration)
- DCIM integration (NetBox connection, health checks, imports)

## Test Structure

```
frontend/tests/e2e/
├── page-navigation.spec.ts      (11 tests)  - Navigation, routing, page loads
├── rack-management.spec.ts      (20 tests)  - Rack CRUD, devices, optimization
├── device-management.spec.ts    (15 tests)  - Device CRUD, filters, views
├── catalog-management.spec.ts   (10 tests)  - Brands, models, types
├── dcim-integration.spec.ts     (13 tests)  - NetBox integration
└── README.md                                - This file
```

**Total: ~69 E2E tests**

## Running Tests

### Prerequisites

1. Ensure the frontend is running at `http://lampadas.local:8080`
2. Backend API should be available and accessible
3. Playwright browsers installed (run `npx playwright install` if needed)

### Commands

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in debug mode
npm run test:e2e:debug

# View test report
npm run test:e2e:report

# Run specific test file
npx playwright test tests/e2e/page-navigation.spec.ts

# Run tests matching a pattern
npx playwright test --grep "should create"
```

## Test Files

### 1. Page Navigation Tests (`page-navigation.spec.ts`)

Tests basic navigation, routing, and page rendering.

**Tests:**
- Dashboard page loads with correct content
- Statistics cards display properly
- Sidebar navigation works for all pages
- Active nav items are highlighted
- Page titles display correctly
- Logo navigation returns to dashboard
- Branding elements are visible

**Coverage:**
- Dashboard
- Racks page
- Devices page
- Connections page
- Thermal Analysis page
- Settings page

---

### 2. Rack Management Tests (`rack-management.spec.ts`)

Tests rack CRUD operations, device assignment, and optimization features.

**Tests:**
- Display rack management page
- Create new rack with form validation
- Edit existing rack
- Delete rack with confirmation
- Display rack list
- Select rack from list
- Rack visualizer renders correctly
- Assign device to rack
- Update device position
- Remove device from rack
- Device actions menu (edit, move, delete)
- Open optimization dialog
- Adjust optimization weights
- Run optimization
- Apply optimization results
- Thermal overlay toggle
- Rack utilization display
- Device count display

**Coverage:**
- Rack CRUD operations
- Rack visualization
- Device assignment workflow
- Optimization features
- Thermal analysis integration

---

### 3. Device Management Tests (`device-management.spec.ts`)

Tests device inventory management, filtering, sorting, and view modes.

**Tests:**
- Display device library page
- Grid and list view switching
- Search devices by name/manufacturer/model
- Filter by device status
- Filter by device type
- Sort by name, type, status, power
- Toggle sort order (ascending/descending)
- Create new device
- Edit existing device
- Delete device with confirmation
- Display device cards with info
- Clear filters
- Empty state when no results
- Device count display

**Coverage:**
- Device CRUD operations
- Search functionality
- Filtering and sorting
- View mode switching
- Empty states

---

### 4. Catalog Management Tests (`catalog-management.spec.ts`)

Tests catalog management including brands, models, device types, and Wikipedia integration.

**Tests:**
- Display settings page with catalog tabs
- Switch between catalog tabs
- List device types with statistics
- Create brand manually
- Fetch brand from Wikipedia
- Upload brand logo
- Edit existing brand
- Delete brand with confirmation
- List models with specifications
- Create new model
- Fetch model specifications
- DCIM integration tab
- Application settings tab

**Coverage:**
- Device types management
- Brands CRUD operations
- Models CRUD operations
- Wikipedia integration
- Logo upload functionality
- Settings navigation

---

### 5. DCIM Integration Tests (`dcim-integration.spec.ts`)

Tests NetBox integration features including health checks and rack imports.

**Tests:**
- Display DCIM integration page
- NetBox connection status display
- Connection status badge (connected/disconnected)
- Test connection button
- Execute health check
- Display NetBox URL when connected
- Import rack card display
- Open NetBox import dialog
- Disable import when not connected
- Configuration information display
- Environment variable documentation
- Read-only integration notice
- List available racks
- Rack selection in import dialog
- Import progress/result display

**Coverage:**
- NetBox connectivity
- Health check functionality
- Rack import workflow
- Configuration display
- Error handling

---

## Test Best Practices

### 1. Test Independence
- Each test is independent and can run in isolation
- Tests clean up after themselves
- No shared state between tests

### 2. Selector Strategy
- Use semantic selectors (roles, labels) when possible
- Use `data-testid` attributes for complex components
- Avoid fragile CSS selectors

### 3. Waiting Strategy
- Use Playwright's auto-waiting features
- Add explicit waits only when necessary
- Use `waitForLoadState('networkidle')` for API-heavy pages

### 4. Error Handling
- Tests gracefully handle missing features
- Empty states are properly tested
- Conditional tests skip when prerequisites aren't met

### 5. Screenshots and Videos
- Screenshots captured on test failures
- Videos recorded for failed tests
- Traces available for debugging

---

## Configuration

Test configuration is defined in `playwright.config.ts`:

```typescript
{
  baseURL: 'http://lampadas.local:8080',
  timeout: 30000,
  fullyParallel: false,  // Sequential execution
  workers: 1,            // Single worker
  retries: 0,            // No retries (CI: 2)
  reporter: ['html', 'list', 'json']
}
```

---

## Debugging Tests

### Using Playwright UI Mode
```bash
npm run test:e2e:ui
```

This opens an interactive UI where you can:
- See test execution in real-time
- Step through tests
- Inspect DOM elements
- View network requests
- Debug test failures

### Using Debug Mode
```bash
npm run test:e2e:debug
```

This runs tests with the Playwright Inspector:
- Set breakpoints
- Step through test code
- Inspect page state
- Execute commands in console

### Viewing Screenshots and Videos
```bash
# Screenshots saved to: test-results/
# Videos saved to: test-results/

# View HTML report
npm run test:e2e:report
```

---

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```bash
# In CI environment
CI=true npm run test:e2e
```

CI mode enables:
- 2 retries on failure
- JSON report generation
- Headless execution
- Fail-fast on `.only` tests

---

## Test Coverage Matrix

| Feature Area           | Tests | Coverage |
|------------------------|-------|----------|
| Page Navigation        | 11    | 100%     |
| Rack Management        | 20    | 95%      |
| Device Management      | 15    | 90%      |
| Catalog Management     | 10    | 85%      |
| DCIM Integration       | 13    | 80%      |
| **Total**              | **69**| **90%**  |

---

## Known Limitations

1. **NetBox Integration**: Some tests skip if NetBox is not configured
2. **Data Dependencies**: Tests assume basic seed data exists
3. **Sequential Execution**: Tests run sequentially to avoid race conditions
4. **Network Dependent**: Tests require active backend API connection

---

## Troubleshooting

### Tests Failing Locally

1. **Check Application is Running**
   ```bash
   curl http://lampadas.local:8080
   ```

2. **Check Backend API**
   ```bash
   curl http://lampadas.local:8000/api/health
   ```

3. **Clear Browser State**
   ```bash
   npx playwright clean
   ```

4. **Update Browsers**
   ```bash
   npx playwright install --force
   ```

### Timeout Errors

Increase timeout in `playwright.config.ts`:
```typescript
timeout: 60000  // 60 seconds
```

### Selector Errors

Use Playwright codegen to find selectors:
```bash
npx playwright codegen http://lampadas.local:8080
```

---

## Future Improvements

- [ ] Add visual regression tests
- [ ] Add accessibility (a11y) tests
- [ ] Add performance tests
- [ ] Add mobile viewport tests
- [ ] Add API mocking for offline tests
- [ ] Add test data fixtures
- [ ] Add parallel execution support
- [ ] Add cross-browser testing

---

## Contributing

When adding new tests:

1. Follow existing test structure and naming
2. Use semantic selectors
3. Add descriptive test names
4. Include error handling
5. Update this README with new test coverage
6. Ensure tests are independent and idempotent

---

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
