import { test, expect } from '@playwright/test';

/**
 * Page Navigation E2E Tests
 *
 * Tests navigation between pages, page load, and UI rendering
 */

test.describe('Page Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the base URL before each test
    await page.goto('/');
  });

  test('should load the dashboard page', async ({ page }) => {
    await expect(page).toHaveURL('/');

    // Check for welcome header (use more specific selector)
    await expect(page.getByRole('heading', { name: /Welcome to.*HomeRack/i })).toBeVisible();

    // Check for stats cards - use first() to avoid multiple matches
    await expect(page.locator('text=Total Racks').first()).toBeVisible();
    await expect(page.locator('text=Total Devices').first()).toBeVisible();
    await expect(page.locator('text=Active Devices').first()).toBeVisible();
    await expect(page.locator('text=Connections').first()).toBeVisible();
  });

  test('should display dashboard statistics', async ({ page }) => {
    // Wait for stats to load
    await page.waitForTimeout(1000);

    // Check Power Consumption card
    await expect(page.locator('text=Power Consumption').first()).toBeVisible();

    // Check Thermal Overview card
    await expect(page.locator('text=Thermal Overview').first()).toBeVisible();

    // Check Recent Devices card
    await expect(page.locator('text=Recent Devices').first()).toBeVisible();
  });

  test('should navigate to Racks page from sidebar', async ({ page }) => {
    // Click on Racks link in sidebar
    await page.locator('nav a[href="/racks"]').click();

    // Verify navigation
    await expect(page).toHaveURL('/racks');
    await expect(page.getByRole('main').getByRole('heading', { name: 'Rack Management' })).toBeVisible();
  });

  test('should navigate to Devices page from sidebar', async ({ page }) => {
    // Click on Devices link in sidebar
    await page.locator('nav a[href="/devices"]').click();

    // Verify navigation
    await expect(page).toHaveURL('/devices');
    await expect(page.getByRole('main').getByRole('heading', { name: 'Device Library' })).toBeVisible();
  });

  test('should navigate to Connections page from sidebar', async ({ page }) => {
    // Click on Connections link in sidebar
    await page.locator('nav a[href="/connections"]').click();

    // Verify navigation
    await expect(page).toHaveURL('/connections');
  });

  test('should navigate to Thermal Analysis page from sidebar', async ({ page }) => {
    // Click on Thermal Analysis link in sidebar
    await page.locator('nav a[href="/thermal"]').click();

    // Verify navigation
    await expect(page).toHaveURL('/thermal');
  });

  test('should navigate to Settings page from sidebar', async ({ page }) => {
    // Click on Settings link in sidebar
    await page.locator('nav a[href="/settings"]').click();

    // Verify navigation
    await expect(page).toHaveURL('/settings');
    await expect(page.getByRole('heading', { name: 'Settings' }).first()).toBeVisible();
  });

  test('should display correct page titles', async ({ page }) => {
    // Dashboard
    await expect(page.getByRole('heading', { name: /Welcome to.*HomeRack/i })).toBeVisible();

    // Racks
    await page.locator('nav a[href="/racks"]').click();
    await expect(page.getByRole('main').getByRole('heading', { name: 'Rack Management' })).toBeVisible();

    // Devices
    await page.locator('nav a[href="/devices"]').click();
    await expect(page.getByRole('main').getByRole('heading', { name: 'Device Library' })).toBeVisible();

    // Settings
    await page.locator('nav a[href="/settings"]').click();
    await expect(page.getByRole('heading', { name: 'Settings' }).first()).toBeVisible();
  });

  test('should highlight active nav item in sidebar', async ({ page }) => {
    // Check dashboard is active (look for the nav item with Dashboard text)
    const dashboardNav = page.locator('nav').getByRole('link', { name: 'Dashboard' });
    await expect(dashboardNav.locator('..')).toHaveClass(/bg-electric/);

    // Navigate to Racks and check active state
    await page.locator('nav a[href="/racks"]').click();
    await page.waitForTimeout(500);
    const racksNav = page.locator('nav').getByRole('link', { name: 'Racks' });
    await expect(racksNav.locator('..')).toHaveClass(/bg-electric/);
  });

  test('should display HomeRack branding in sidebar', async ({ page }) => {
    await expect(page.locator('aside').getByRole('heading', { name: 'HomeRack' })).toBeVisible();
    await expect(page.locator('aside').locator('text=Precision Engineering').first()).toBeVisible();
  });

  test('should navigate back to dashboard from logo', async ({ page }) => {
    // Navigate away from dashboard
    await page.locator('nav a[href="/devices"]').click();
    await expect(page).toHaveURL('/devices');

    // Click logo to return to dashboard
    await page.locator('aside a[href="/"]').first().click();
    await expect(page).toHaveURL('/');
  });
});
