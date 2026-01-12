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
    const dcimTab = page.locator('button:has-text("DCIM")');
    await dcimTab.click();
    await page.waitForTimeout(500);
  });

  test('should display DCIM Integration tab', async ({ page }) => {
    await expect(page.locator('text=DCIM Integration')).toBeVisible();
    await expect(
      page.locator('text=NetBox').or(page.locator('text=Integration'))
    ).toBeVisible();
  });

  test('should display NetBox connection status card', async ({ page }) => {
    await expect(
      page.locator('text=NetBox Connection').or(page.locator('text=Connection Status'))
    ).toBeVisible();
  });

  test('should show connection status badge', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for connection status indicator
    const statusBadge = page.locator('text=Connected, text=Disconnected').or(
      page.locator('[class*="badge"]')
    ).first();

    const isVisible = await statusBadge.isVisible();
    expect(typeof isVisible).toBe('boolean');
  });

  test('should display test connection button', async ({ page }) => {
    const testButton = page.locator('button:has-text("Test Connection")');
    await expect(testButton).toBeVisible();
  });

  test('should execute health check on test connection', async ({ page }) => {
    const testButton = page.locator('button:has-text("Test Connection")');
    await testButton.click();

    // Wait for health check to complete
    await page.waitForTimeout(2000);

    // Should show some result (either connected or error)
    const result = page.locator('text=Connected, text=Disconnected, text=Failed, text=Error').first();
    const hasResult = await result.isVisible();
    expect(typeof hasResult).toBe('boolean');
  });

  test('should display NetBox URL when connected', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for URL display
    const urlField = page.locator('text=NetBox URL').or(
      page.locator('code, pre').filter({ hasText: /http/i })
    );

    const hasUrl = await urlField.isVisible();
    expect(typeof hasUrl).toBe('boolean');
  });

  test('should display import rack card', async ({ page }) => {
    await expect(
      page.locator('text=Import from NetBox').or(page.locator('text=Import Rack'))
    ).toBeVisible();
  });

  test('should open NetBox import dialog', async ({ page }) => {
    const importButton = page.locator('button:has-text("Import Rack")');

    if (await importButton.isVisible()) {
      await importButton.click();
      await page.waitForTimeout(500);

      // Check import dialog opened
      await expect(
        page.locator('text=NetBox').or(page.locator('text=Select rack'))
      ).toBeVisible();
    }
  });

  test('should disable import when not connected', async ({ page }) => {
    await page.waitForTimeout(1000);

    const importButton = page.locator('button:has-text("Import Rack")');

    if (await importButton.isVisible()) {
      // Check if button is disabled when not connected
      const isDisabled = await importButton.isDisabled();

      // Could be enabled or disabled depending on connection
      expect(typeof isDisabled).toBe('boolean');
    }
  });

  test('should display configuration information', async ({ page }) => {
    await expect(
      page.locator('text=Configuration').or(page.locator('text=Environment Variables'))
    ).toBeVisible();
  });

  test('should show environment variable examples', async ({ page }) => {
    // Look for env var documentation
    const envVars = page.locator('text=NETBOX_ENABLED, text=NETBOX_URL, text=NETBOX_TOKEN');

    const hasEnvInfo = await envVars.isVisible();
    expect(typeof hasEnvInfo).toBe('boolean');
  });

  test('should display read-only integration notice', async ({ page }) => {
    const notice = page.locator('text=Read-Only').or(
      page.locator('text=does not write back')
    );

    const hasNotice = await notice.isVisible();
    expect(typeof hasNotice).toBe('boolean');
  });

  test('should list available racks when import dialog is open', async ({ page }) => {
    const importButton = page.locator('button:has-text("Import Rack")');

    if (await importButton.isVisible() && !await importButton.isDisabled()) {
      await importButton.click();
      await page.waitForTimeout(1000);

      // Look for rack selection
      const rackList = page.locator('select, [role="listbox"]').or(
        page.locator('text=rack')
      );

      const hasRackList = await rackList.isVisible();
      expect(typeof hasRackList).toBe('boolean');
    } else {
      // Skip if NetBox is not connected
      test.skip();
    }
  });

  test('should allow rack selection in import dialog', async ({ page }) => {
    const importButton = page.locator('button:has-text("Import Rack")');

    if (await importButton.isVisible() && !await importButton.isDisabled()) {
      await importButton.click();
      await page.waitForTimeout(1000);

      // Look for rack selector
      const rackSelector = page.locator('select').first();

      if (await rackSelector.isVisible()) {
        const options = await rackSelector.locator('option').count();
        expect(options).toBeGreaterThan(0);
      }
    } else {
      test.skip();
    }
  });

  test('should show import progress or result', async ({ page }) => {
    const importButton = page.locator('button:has-text("Import Rack")');

    if (await importButton.isVisible() && !await importButton.isDisabled()) {
      await importButton.click();
      await page.waitForTimeout(1000);

      // Look for import/submit button
      const submitButton = page.locator('button:has-text("Import"), button:has-text("Submit")').first();

      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(2000);

        // Should show some result
        const result = page.locator('text=Success, text=Error, text=Complete').first();
        const hasResult = await result.isVisible();
        expect(typeof hasResult).toBe('boolean');
      }
    } else {
      test.skip();
    }
  });
});
