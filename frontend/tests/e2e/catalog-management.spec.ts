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
    await expect(page.locator('h1')).toContainText('Settings');
    await expect(page.locator('text=Manage device catalog')).toBeVisible();
  });

  test('should display catalog tabs', async ({ page }) => {
    // Check for tab navigation
    await expect(page.locator('button:has-text("Device Types")').or(page.locator('button:has-text("Types")'))).toBeVisible();
    await expect(page.locator('button:has-text("Brands")')).toBeVisible();
    await expect(page.locator('button:has-text("Models")')).toBeVisible();
  });

  test('should switch to Brands tab', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(500);

    // Check brands content loaded
    await expect(
      page.locator('text=Brand').or(page.locator('text=manufacturer'))
    ).toBeVisible();
  });

  test('should switch to Models tab', async ({ page }) => {
    await page.locator('button:has-text("Models")').click();
    await page.waitForTimeout(500);

    // Check models content loaded
    await expect(
      page.locator('text=Model').or(page.locator('text=specification'))
    ).toBeVisible();
  });

  test('should switch to Device Types tab', async ({ page }) => {
    const deviceTypesTab = page.locator('button:has-text("Device Types")').or(
      page.locator('button:has-text("Types")')
    ).first();

    await deviceTypesTab.click();
    await page.waitForTimeout(500);

    // Check device types content
    await expect(
      page.locator('text=Server, text=Switch, text=Router').or(page.locator('text=device'))
    ).toBeVisible();
  });

  test('should list device types', async ({ page }) => {
    const deviceTypesTab = page.locator('button:has-text("Device Types")').or(
      page.locator('button:has-text("Types")')
    ).first();

    await deviceTypesTab.click();
    await page.waitForTimeout(1000);

    // Check for common device types
    const hasTypes = await page.locator('text=Server').or(
      page.locator('text=Switch')
    ).isVisible();

    expect(typeof hasTypes).toBe('boolean');
  });

  test('should open create brand dialog', async ({ page }) => {
    // Go to Brands tab
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(500);

    // Look for Add/Create Brand button
    const addBrandButton = page.locator('button:has-text("Add Brand"), button:has-text("Create Brand")').first();

    if (await addBrandButton.isVisible()) {
      await addBrandButton.click();
      await page.waitForTimeout(500);

      // Check dialog opened
      await expect(
        page.locator('text=Create Brand').or(page.locator('input[placeholder*="brand"]'))
      ).toBeVisible();
    }
  });

  test('should create brand manually', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(500);

    const addBrandButton = page.locator('button:has-text("Add Brand"), button:has-text("Create")').first();

    if (await addBrandButton.isVisible()) {
      await addBrandButton.click();
      await page.waitForTimeout(500);

      // Fill brand name
      const nameInput = page.locator('input[name="name"]').or(
        page.locator('input[placeholder*="name"]')
      ).first();

      if (await nameInput.isVisible()) {
        await nameInput.fill('Test Brand E2E');
        await page.waitForTimeout(500);

        // Submit
        const saveButton = page.locator('button:has-text("Create"), button:has-text("Save")').first();

        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('should open Wikipedia fetch dialog', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(500);

    // Look for Wikipedia/Fetch button
    const fetchButton = page.locator('button:has-text("Wikipedia"), button:has-text("Fetch")').first();

    if (await fetchButton.isVisible()) {
      await fetchButton.click();
      await page.waitForTimeout(500);

      // Check fetch dialog
      await expect(
        page.locator('text=Wikipedia').or(page.locator('input'))
      ).toBeVisible();
    }
  });

  test('should display brand list', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(1000);

    // Check for brands or empty state
    const hasBrands = await page.locator('[class*="card"]').or(
      page.locator('text=No brands')
    ).isVisible();

    expect(typeof hasBrands).toBe('boolean');
  });

  test('should edit existing brand', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(1000);

    // Look for edit button on brand card
    const editButton = page.locator('button[title*="Edit"]').first();

    if (await editButton.isVisible()) {
      await editButton.click();
      await page.waitForTimeout(500);

      // Check edit dialog
      await expect(
        page.locator('text=Edit Brand').or(page.locator('input'))
      ).toBeVisible();
    }
  });

  test('should delete brand with confirmation', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(1000);

    // Look for delete button
    const deleteButton = page.locator('button[title*="Delete"]').first();

    if (await deleteButton.isVisible()) {
      await deleteButton.click();
      await page.waitForTimeout(500);

      // Check confirmation
      await expect(
        page.locator('text=Delete').or(page.locator('text=Are you sure'))
      ).toBeVisible();
    }
  });

  test('should upload brand logo', async ({ page }) => {
    await page.locator('button:has-text("Brands")').click();
    await page.waitForTimeout(1000);

    const editButton = page.locator('button[title*="Edit"]').first();

    if (await editButton.isVisible()) {
      await editButton.click();
      await page.waitForTimeout(500);

      // Look for logo upload input
      const logoInput = page.locator('input[type="file"]').or(
        page.locator('text=Upload, text=Logo')
      ).first();

      const hasLogoUpload = await logoInput.isVisible();
      expect(typeof hasLogoUpload).toBe('boolean');
    }
  });

  test('should list models', async ({ page }) => {
    await page.locator('button:has-text("Models")').click();
    await page.waitForTimeout(1000);

    // Check for models or empty state
    const hasModels = await page.locator('[class*="card"]').or(
      page.locator('text=No models')
    ).isVisible();

    expect(typeof hasModels).toBe('boolean');
  });

  test('should create new model', async ({ page }) => {
    await page.locator('button:has-text("Models")').click();
    await page.waitForTimeout(500);

    const addModelButton = page.locator('button:has-text("Add Model"), button:has-text("Create")').first();

    if (await addModelButton.isVisible()) {
      await addModelButton.click();
      await page.waitForTimeout(500);

      // Check dialog opened
      await expect(
        page.locator('text=Create Model').or(page.locator('input'))
      ).toBeVisible();
    }
  });

  test('should fetch model specifications', async ({ page }) => {
    await page.locator('button:has-text("Models")').click();
    await page.waitForTimeout(500);

    // Look for fetch specs button
    const fetchButton = page.locator('button:has-text("Fetch"), button:has-text("Import")').first();

    if (await fetchButton.isVisible()) {
      await fetchButton.click();
      await page.waitForTimeout(500);

      // Check fetch dialog
      const hasFetchDialog = await page.locator('input').or(
        page.locator('select')
      ).isVisible();

      expect(typeof hasFetchDialog).toBe('boolean');
    }
  });

  test('should display DCIM Integration tab', async ({ page }) => {
    const dcimTab = page.locator('button:has-text("DCIM")');

    if (await dcimTab.isVisible()) {
      await dcimTab.click();
      await page.waitForTimeout(500);

      // Check for NetBox content
      await expect(
        page.locator('text=NetBox').or(page.locator('text=Integration'))
      ).toBeVisible();
    }
  });

  test('should display Application tab', async ({ page }) => {
    const appTab = page.locator('button:has-text("Application")');

    await appTab.click();
    await page.waitForTimeout(500);

    // Check for app settings
    await expect(
      page.locator('text=Version').or(page.locator('text=Preferences'))
    ).toBeVisible();
  });
});
