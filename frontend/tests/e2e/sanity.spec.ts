import { test, expect } from '@playwright/test';

test('homepage has correct title and content', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: /Translate Technical Work into/i })).toBeVisible();

    await expect(page.getByRole('link', { name: /Start Chatting/i })).toBeVisible();
});
