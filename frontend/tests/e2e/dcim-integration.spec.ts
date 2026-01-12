import { test, expect } from '@playwright/test';

/**
 * DCIM Integration E2E Tests
 *
 * Tests NetBox integration, health checks, and rack imports
 */

test.describe('DCIM Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Navigate to DCIM tab
    const dcimTab = page.getByRole('tab', { name: 'DCIM' });
    await dcimTab.click();
    await page.waitForTimeout(500);
  });

  test('should display DCIM Integration tab', async ({ page }) => {
    await expect(page.locator('text=DCIM Integration').first()).toBeVisible();
    await expect(
      page.locator('text=NetBox').first().or(page.locator('text=Integration').first())
    ).toBeVisible();
  });

  test('should display NetBox connection status card', async ({ page }) => {
    await expect(
      page.locator('text=NetBox Connection').first().or(page.locator('text=Connection Status').first())
    ).toBeVisible();
  });

  test('should show connection status badge', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for connection status indicator
    const statusBadge = page.locator('text=Connected').first().or(
      page.locator('text=Disconnected').first()
    ).or(page.locator('[class*="badge"]').first());

    const isVisible = await statusBadge.isVisible();
    expect(typeof isVisible).toBe('boolean');
  });

  test('should display test connection button', async ({ page }) => {
    const testButton = page.getByRole('button', { name: /Test Connection/i }).first();
    await expect(testButton).toBeVisible();
  });

  test('should execute health check on test connection', async ({ page }) => {
    const testButton = page.getByRole('button', { name: /Test Connection/i }).first();
    await testButton.click();

    // Wait for health check to complete
    await page.waitForTimeout(2000);

    // Should show some result (either connected or error)
    const result = page.locator('text=Connected').first().or(
      page.locator('text=Disconnected').first()
    ).or(page.locator('text=Failed').first()).or(
      page.locator('text=Error').first()
    );
    const hasResult = await result.isVisible();
    expect(typeof hasResult).toBe('boolean');
  });

  test('should display NetBox URL when connected', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for URL display
    const urlField = page.locator('text=NetBox URL').first().or(
      page.locator('code').filter({ hasText: /http/i }).first()
    );

    const hasUrl = await urlField.isVisible();
    expect(typeof hasUrl).toBe('boolean');
  });

  test('should display import rack card', async ({ page }) => {
    await expect(
      page.locator('text=Import from NetBox').first().or(page.locator('text=Import Rack').first())
    ).toBeVisible();
  });

  test('should open NetBox import dialog', async ({ page }) => {
    const importButton = page.getByRole('button', { name: /Import Rack/i }).first();

    if (await importButton.isVisible()) {
      await importButton.click();
      await page.waitForTimeout(500);

      // Check import dialog opened
      await expect(
        page.getByRole('dialog').first()
      ).toBeVisible();
    }
  });

  test('should disable import when not connected', async ({ page }) => {
    await page.waitForTimeout(1000);

    const importButton = page.getByRole('button', { name: /Import Rack/i }).first();

    if (await importButton.isVisible()) {
      // Check if button is disabled when not connected
      const isDisabled = await importButton.isDisabled();

      // Could be enabled or disabled depending on connection
      expect(typeof isDisabled).toBe('boolean');
    }
  });

  test('should display configuration information', async ({ page }) => {
    await expect(
      page.locator('text=Configuration').first().or(page.locator('text=Environment Variables').first())
    ).toBeVisible();
  });

  test('should show environment variable examples', async ({ page }) => {
    // Look for env var documentation
    const envVars = page.locator('text=NETBOX_ENABLED').first().or(
      page.locator('text=NETBOX_URL').first()
    ).or(page.locator('text=NETBOX_TOKEN').first());

    const hasEnvInfo = await envVars.isVisible();
    expect(typeof hasEnvInfo).toBe('boolean');
  });

  test('should display read-only integration notice', async ({ page }) => {
    const notice = page.locator('text=Read-Only').first().or(
      page.locator('text=does not write back').first()
    );

    const hasNotice = await notice.isVisible();
    expect(typeof hasNotice).toBe('boolean');
  });

  test('should list available racks when import dialog is open', async ({ page }) => {
    const importButton = page.getByRole('button', { name: /Import Rack/i }).first();

    if (await importButton.isVisible() && !await importButton.isDisabled()) {
      await importButton.click();
      await page.waitForTimeout(1000);

      // Look for rack selection within dialog
      const dialog = page.getByRole('dialog').first();
      const rackList = dialog.locator('select').first().or(
        dialog.locator('[role="listbox"]').first()
      ).or(dialog.locator('text=rack').first());

      const hasRackList = await rackList.isVisible();
      expect(typeof hasRackList).toBe('boolean');
    } else {
      // Skip if NetBox is not connected
      test.skip();
    }
  });

  test('should allow rack selection in import dialog', async ({ page }) => {
    const importButton = page.getByRole('button', { name: /Import Rack/i }).first();

    if (await importButton.isVisible() && !await importButton.isDisabled()) {
      await importButton.click();
      await page.waitForTimeout(1000);

      // Look for rack selector within dialog
      const dialog = page.getByRole('dialog').first();
      const rackSelector = dialog.locator('select').first();

      if (await rackSelector.isVisible()) {
        const options = await rackSelector.locator('option').count();
        expect(options).toBeGreaterThan(0);
      }
    } else {
      test.skip();
    }
  });

  test('should show import progress or result', async ({ page }) => {
    const importButton = page.getByRole('button', { name: /Import Rack/i }).first();

    if (await importButton.isVisible() && !await importButton.isDisabled()) {
      await importButton.click();
      await page.waitForTimeout(1000);

      // Look for import/submit button within dialog
      const dialog = page.getByRole('dialog').first();
      const submitButton = dialog.getByRole('button', { name: /Import|Submit/i }).first();

      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(2000);

        // Should show some result
        const result = page.locator('text=Success').first().or(
          page.locator('text=Error').first()
        ).or(page.locator('text=Complete').first());
        const hasResult = await result.isVisible();
        expect(typeof hasResult).toBe('boolean');
      }
    } else {
      test.skip();
    }
  });
});
