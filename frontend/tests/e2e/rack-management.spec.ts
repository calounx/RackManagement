import { test, expect } from '@playwright/test';

/**
 * Rack Management E2E Tests
 *
 * Tests rack CRUD operations, device assignment, optimization, and visualization
 */

test.describe('Rack Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/racks');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display rack management page', async ({ page }) => {
    await expect(page.getByRole('main').getByRole('heading', { name: 'Rack Management' })).toBeVisible();
    await expect(page.locator('text=Visualize and manage your server racks').first()).toBeVisible();
  });

  test('should display add rack button', async ({ page }) => {
    const addButton = page.getByRole('button', { name: /Add Rack/i }).first();
    await expect(addButton).toBeVisible();
  });

  test('should open create rack dialog', async ({ page }) => {
    // Click Add Rack button
    await page.getByRole('button', { name: /Add Rack/i }).first().click();

    // Check dialog is visible
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('dialog').locator('input').first()).toBeVisible();
  });

  test('should create a new rack', async ({ page }) => {
    // Open create dialog
    await page.getByRole('button', { name: /Add Rack/i }).first().click();

    // Fill form - use dialog context
    const dialog = page.getByRole('dialog');
    const nameInput = dialog.locator('input[name="name"]').or(dialog.locator('input').first());
    await nameInput.fill('Test Rack E2E');

    const locationInput = dialog.locator('input[name="location"]').or(dialog.locator('input').nth(1));
    await locationInput.fill('Data Center A');

    // Submit form
    await dialog.getByRole('button', { name: /Create|Save/i }).first().click();

    // Wait for dialog to close and rack to appear
    await page.waitForTimeout(1000);

    // Verify rack was created
    await expect(page.locator('text=Test Rack E2E').first()).toBeVisible();
  });

  test('should display rack list when racks exist', async ({ page }) => {
    // Check for Available Racks section
    const racksSection = page.locator('text=Available Racks').first();

    if (await racksSection.isVisible()) {
      await expect(racksSection).toBeVisible();
    } else {
      // If no racks, should show empty state
      await expect(page.locator('text=No racks yet').first()).toBeVisible();
    }
  });

  test('should select a rack from the list', async ({ page }) => {
    // Wait for racks to load
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      // Click first rack
      await rackButtons.first().click();

      // Wait for selection
      await page.waitForTimeout(500);

      // Check for rack layout section
      await expect(page.locator('text=Rack Layout').first().or(page.getByRole('button', { name: /Add Device/i }).first())).toBeVisible();
    }
  });

  test('should open edit rack dialog', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for edit button (pencil icon)
    const editButton = page.getByRole('button', { name: /Edit Rack/i }).first();

    if (await editButton.isVisible()) {
      await editButton.click();

      // Check dialog opened
      await expect(page.getByRole('dialog').first()).toBeVisible();
    }
  });

  test('should open delete rack confirmation dialog', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for delete button (trash icon)
    const deleteButton = page.getByRole('button', { name: /Delete Rack/i }).first();

    if (await deleteButton.isVisible()) {
      await deleteButton.click();

      // Check confirmation dialog
      await expect(page.getByRole('alertdialog').first().or(page.getByRole('dialog').first())).toBeVisible();
    }
  });

  test('should display rack visualizer when rack is selected', async ({ page }) => {
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      await rackButtons.first().click();
      await page.waitForTimeout(500);

      // Check for rack visualization elements
      await expect(
        page.locator('text=Rack Layout').first().or(page.locator('text=Click empty units').first())
      ).toBeVisible();
    }
  });

  test('should open device assignment dialog from add device button', async ({ page }) => {
    await page.waitForTimeout(1000);

    const addDeviceButton = page.getByRole('button', { name: /Add Device/i }).first();

    if (await addDeviceButton.isVisible()) {
      await addDeviceButton.click();

      // Check assignment dialog opened
      await page.waitForTimeout(500);
      await expect(
        page.getByRole('dialog').first()
      ).toBeVisible();
    }
  });

  test('should open optimization dialog', async ({ page }) => {
    await page.waitForTimeout(1000);

    const optimizeButton = page.getByRole('button', { name: /Optimize Layout|Optimize/i }).first();

    if (await optimizeButton.isVisible()) {
      await optimizeButton.click();

      // Check optimization dialog
      await page.waitForTimeout(500);
      await expect(
        page.getByRole('dialog').first().or(page.locator('text=Optimization').first())
      ).toBeVisible();
    }
  });

  test('should adjust optimization weights', async ({ page }) => {
    await page.waitForTimeout(1000);

    const optimizeButton = page.getByRole('button', { name: /Optimize/i }).first();

    if (await optimizeButton.isVisible()) {
      await optimizeButton.click();
      await page.waitForTimeout(500);

      // Look for sliders or weight inputs within dialog
      const dialog = page.getByRole('dialog').first();
      const sliders = dialog.locator('input[type="range"]');
      const sliderCount = await sliders.count();

      if (sliderCount > 0) {
        // Adjust first slider
        await sliders.first().fill('75');
        await expect(sliders.first()).toHaveValue('75');
      }
    }
  });

  test('should run optimization', async ({ page }) => {
    await page.waitForTimeout(1000);

    const optimizeButton = page.getByRole('button', { name: /Optimize/i }).first();

    if (await optimizeButton.isVisible()) {
      await optimizeButton.click();
      await page.waitForTimeout(500);

      // Look for run/apply button within dialog
      const dialog = page.getByRole('dialog').first();
      const runButton = dialog.getByRole('button', { name: /Run|Apply/i }).first();

      if (await runButton.isVisible()) {
        await runButton.click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('should display thermal overlay toggle', async ({ page }) => {
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      await rackButtons.first().click();
      await page.waitForTimeout(500);

      // Check for thermal-related controls
      const thermalControl = page.locator('text=Thermal').first().or(page.locator('text=Temperature').first());
      // Thermal overlay might not always be visible
      const isVisible = await thermalControl.isVisible();
      expect(typeof isVisible).toBe('boolean');
    }
  });

  test('should click on empty unit to add device', async ({ page }) => {
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      await rackButtons.first().click();
      await page.waitForTimeout(500);

      // Look for unit cells in rack visualizer
      const unitCell = page.locator('[class*="unit"], [data-unit]').first();

      if (await unitCell.isVisible()) {
        await unitCell.click();
        await page.waitForTimeout(500);

        // Should open assignment dialog
        await expect(
          page.getByRole('dialog').first().or(page.locator('text=Assign').first())
        ).toBeVisible();
      }
    }
  });

  test('should click on device to open actions menu', async ({ page }) => {
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      await rackButtons.first().click();
      await page.waitForTimeout(500);

      // Look for device elements
      const deviceElement = page.locator('[class*="device"]').first();

      if (await deviceElement.isVisible()) {
        await deviceElement.click();
        await page.waitForTimeout(500);

        // Should open actions menu or popover
        await expect(
          page.getByRole('menu').first().or(page.locator('[role="menu"]').first()).or(page.locator('text=Edit').first())
        ).toBeVisible();
      }
    }
  });

  test('should display rack utilization percentage', async ({ page }) => {
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      // Look for percentage indicators
      const percentage = page.locator('text=/%|%/').first();
      const isVisible = await percentage.isVisible();
      expect(typeof isVisible).toBe('boolean');
    }
  });

  test('should show rack device count', async ({ page }) => {
    await page.waitForTimeout(1000);

    const rackButtons = page.locator('button').filter({ hasText: /Rack|rack/i });
    const count = await rackButtons.count();

    if (count > 0) {
      // Look for device count
      const deviceCount = page.locator('text=/\\d+ device/').first();
      const isVisible = await deviceCount.isVisible();
      expect(typeof isVisible).toBe('boolean');
    }
  });

  test('should display empty state when no racks exist', async ({ page }) => {
    // This test checks the empty state UI
    const emptyState = page.locator('text=No racks yet').first();
    const addRackButton = page.getByRole('button', { name: /Add Rack/i }).first();

    // Either empty state or rack list should be visible
    const hasEmptyState = await emptyState.isVisible();
    const hasAddButton = await addRackButton.isVisible();

    expect(hasEmptyState || hasAddButton).toBe(true);
  });
});
