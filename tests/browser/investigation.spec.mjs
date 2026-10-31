import {test,expect} from '@playwright/test';
test.use({deviceScaleFactor:2});

test('native problem cases preserve a frame between 2D/3D and restore language',async({page})=>{
  await page.goto('/701-investigation/?lang=pt');
  await expect(page.locator('#cases article')).toHaveCount(4);
  await page.locator('#cases article').nth(2).getByRole('link',{name:'2D',exact:true}).click();
  await page.waitForFunction(()=>window.nativeCaseView);
  await expect(page.locator('html')).toHaveAttribute('lang','pt');
  await expect(page.locator('#source-note')).toContainText('1 registo de colisão');
  await page.locator('#scrub').fill('92');
  const index=await page.evaluate(()=>window.nativeCaseView.index);
  await page.getByRole('button',{name:'3D',exact:true}).click();
  expect(await page.evaluate(()=>window.nativeCaseView.index)).toBe(index);
  expect(await page.evaluate(()=>window.nativeCaseView.dimension)).toBe('3d');
  await expect(page.locator('#three canvas')).toBeVisible();
  const extent=await page.locator('#viewer').boundingBox();
  const canvas=await page.locator('#three canvas').boundingBox();
  expect(canvas.width).toBeCloseTo(extent.width,0);
  expect(canvas.height).toBeCloseTo(extent.height,0);
  await page.getByRole('button',{name:'2D',exact:true}).click();
  expect(await page.evaluate(()=>window.nativeCaseView.index)).toBe(index);
  await page.locator('#lang').selectOption('en');
  await expect(page.locator('html')).toHaveAttribute('lang','en');
  await page.reload();
  await page.waitForFunction(()=>window.nativeCaseView);
  expect(await page.evaluate(()=>window.nativeCaseView.dimension)).toBe('2d');
  expect(await page.evaluate(()=>window.nativeCaseView.lang)).toBe('en');
  expect(await page.evaluate(()=>window.nativeCaseView.index)).toBe(index);
  expect(new URL(page.url()).searchParams.get('case')).toMatch(/^[a-f0-9]{64}$/);
});

test('a shared case cannot silently restore a different native execution',async({page})=>{
  await page.goto('/701-investigation/areosa-protected-turn/?case=old-execution');
  await expect(page.getByRole('alert')).toContainText('different native execution');
});

test('a changed recording is rejected before visual claims',async({page})=>{
  await page.route('**/frames.json.gz',route=>route.fulfill({body:'changed recording'}));
  await page.goto('/701-investigation/areosa-protected-turn/');
  await expect(page.getByRole('alert')).toContainText('Recording identity mismatch');
  expect(await page.evaluate(()=>Boolean(window.nativeCaseView))).toBe(false);
});
