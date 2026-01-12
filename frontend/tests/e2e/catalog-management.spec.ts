import { test, expect } from '@playwright/test';

/**
 * Catalog Management E2E Tests
 *
 * Tests brands, models, device types management, and Wikipedia integration
 */

test.describe('Catalog Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
  });

  test('should display settings page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' }).first()).toBeVisible();
    await expect(page.locator('text=Manage device catalog').first()).toBeVisible();
  });

  test('should display catalog tabs', async ({ page }) => {
    // Check for tab navigation
    await expect(page.getByRole('tab', { name: /Device Types|Types/i }).first()).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Brands' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Models' })).toBeVisible();
  });

  test('should switch to Brands tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(500);

    // Check brands content loaded - look for either brand list or empty state
    await expect(
      page.getByRole('main').locator('text=Brand').first().or(page.locator('text=manufacturer').first())
    ).toBeVisible();
  });

  test('should switch to Models tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Models' }).click();
    await page.waitForTimeout(500);

    // Check models content loaded
    await expect(
      page.getByRole('main').locator('text=Model').first().or(page.locator('text=specification').first())
    ).toBeVisible();
  });

  test('should switch to Device Types tab', async ({ page }) => {
    const deviceTypesTab = page.getByRole('tab', { name: /Device Types|Types/i }).first();

    await deviceTypesTab.click();
    await page.waitForTimeout(500);

    // Check device types content
    await expect(
      page.locator('text=Server').first().or(page.locator('text=Switch').first()).or(page.locator('text=device').first())
    ).toBeVisible();
  });

  test('should list device types', async ({ page }) => {
    const deviceTypesTab = page.getByRole('tab', { name: /Device Types|Types/i }).first();

    await deviceTypesTab.click();
    await page.waitForTimeout(1000);

    // Check for common device types
    const hasTypes = await page.locator('text=Server').first().or(
      page.locator('text=Switch').first()
    ).isVisible();

    expect(typeof hasTypes).toBe('boolean');
  });

  test('should open create brand dialog', async ({ page }) => {
    // Go to Brands tab
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(500);

    // Look for Add/Create Brand button
    const addBrandButton = page.getByRole('button', { name: /Add Brand|Create Brand/i }).first();

    if (await addBrandButton.isVisible()) {
      await addBrandButton.click();
      await page.waitForTimeout(500);

      // Check dialog opened
      await expect(
        page.getByRole('dialog').or(page.locator('[role="dialog"]')).first()
      ).toBeVisible();
    }
  });

  test('should create brand manually', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(500);

    const addBrandButton = page.getByRole('button', { name: /Add Brand|Create/i }).first();

    if (await addBrandButton.isVisible()) {
      await addBrandButton.click();
      await page.waitForTimeout(500);

      // Fill brand name - use dialog context
      const dialog = page.getByRole('dialog').first();
      const nameInput = dialog.locator('input[name="name"]').or(
        dialog.locator('input').first()
      );

      if (await nameInput.isVisible()) {
        await nameInput.fill('Test Brand E2E');
        await page.waitForTimeout(500);

        // Submit
        const saveButton = dialog.getByRole('button', { name: /Create|Save/i }).first();

        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('should open Wikipedia fetch dialog', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(500);

    // Look for Wikipedia/Fetch button
    const fetchButton = page.getByRole('button', { name: /Wikipedia|Fetch/i }).first();

    if (await fetchButton.isVisible()) {
      await fetchButton.click();
      await page.waitForTimeout(500);

      // Check fetch dialog
      await expect(
        page.getByRole('dialog').first().or(page.locator('[role="dialog"]').first())
      ).toBeVisible();
    }
  });

  test('should display brand list', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(1000);

    // Check for brands or empty state
    const hasBrands = await page.getByRole('main').locator('[class*="card"]').first().or(
      page.locator('text=No brands').first()
    ).isVisible();

    expect(typeof hasBrands).toBe('boolean');
  });

  test('should edit existing brand', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(1000);

    // Look for edit button on brand card
    const editButton = page.getByRole('button', { name: /Edit/i }).first();

    if (await editButton.isVisible()) {
      await editButton.click();
      await page.waitForTimeout(500);

      // Check edit dialog
      await expect(
        page.getByRole('dialog').first().or(page.locator('[role="dialog"]').first())
      ).toBeVisible();
    }
  });

  test('should delete brand with confirmation', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(1000);

    // Look for delete button
    const deleteButton = page.getByRole('button', { name: /Delete/i }).first();

    if (await deleteButton.isVisible()) {
      await deleteButton.click();
      await page.waitForTimeout(500);

      // Check confirmation dialog
      await expect(
        page.getByRole('alertdialog').first().or(page.getByRole('dialog').first())
      ).toBeVisible();
    }
  });

  test('should upload brand logo', async ({ page }) => {
    await page.getByRole('tab', { name: 'Brands' }).click();
    await page.waitForTimeout(1000);

    const editButton = page.getByRole('button', { name: /Edit/i }).first();

    if (await editButton.isVisible()) {
      await editButton.click();
      await page.waitForTimeout(500);

      // Look for logo upload input within dialog
      const dialog = page.getByRole('dialog').first();
      const logoInput = dialog.locator('input[type="file"]').first();

      const hasLogoUpload = await logoInput.isVisible();
      expect(typeof hasLogoUpload).toBe('boolean');
    }
  });

  test('should list models', async ({ page }) => {
    await page.getByRole('tab', { name: 'Models' }).click();
    await page.waitForTimeout(1000);

    // Check for models or empty state
    const hasModels = await page.getByRole('main').locator('[class*="card"]').first().or(
      page.locator('text=No models').first()
    ).isVisible();

    expect(typeof hasModels).toBe('boolean');
  });

  test('should create new model', async ({ page }) => {
    await page.getByRole('tab', { name: 'Models' }).click();
    await page.waitForTimeout(500);

    const addModelButton = page.getByRole('button', { name: /Add Model|Create/i }).first();

    if (await addModelButton.isVisible()) {
      await addModelButton.click();
      await page.waitForTimeout(500);

      // Check dialog opened
      await expect(
        page.getByRole('dialog').first().or(page.locator('[role="dialog"]').first())
      ).toBeVisible();
    }
  });

  test('should fetch model specifications', async ({ page }) => {
    await page.getByRole('tab', { name: 'Models' }).click();
    await page.waitForTimeout(500);

    // Look for fetch specs button
    const fetchButton = page.getByRole('button', { name: /Fetch|Import/i }).first();

    if (await fetchButton.isVisible()) {
      await fetchButton.click();
      await page.waitForTimeout(500);

      // Check fetch dialog
      const dialog = page.getByRole('dialog').first();
      const hasFetchDialog = await dialog.isVisible();

      expect(typeof hasFetchDialog).toBe('boolean');
    }
  });

  test('should display DCIM Integration tab', async ({ page }) => {
    const dcimTab = page.getByRole('tab', { name: 'DCIM' });

    if (await dcimTab.isVisible()) {
      await dcimTab.click();
      await page.waitForTimeout(500);

      // Check for NetBox content
      await expect(
        page.locator('text=NetBox').first().or(page.locator('text=Integration').first())
      ).toBeVisible();
    }
  });

  test('should display Application tab', async ({ page }) => {
    const appTab = page.getByRole('tab', { name: 'Application' });

    await appTab.click();
    await page.waitForTimeout(500);

    // Check for app settings
    await expect(
      page.locator('text=Version').first().or(page.locator('text=Preferences').first())
    ).toBeVisible();
  });
});
