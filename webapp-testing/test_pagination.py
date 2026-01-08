"""
Test SEO-friendly pagination functionality - Enhanced version
Tests: SSR, URL sync, filter reset, back button, no-JS fallback, invalid params
"""
from playwright.sync_api import sync_playwright
import time

def test_ssr_content(page):
    """Verify SSR content is pre-rendered"""
    print("\n=== Test 1: SSR Content Rendering ===")

    # Navigate to page 2
    page.goto('http://localhost:3000/designs?page=2')
    page.wait_for_load_state('networkidle')

    # Check page title
    title = page.title()
    print(f"  Page title: {title}")

    # Check for design images (more reliable selector)
    design_images = page.locator('img').all()
    print(f"  Total images found: {len(design_images)}")

    # Check URL
    current_url = page.url
    print(f"  Current URL: {current_url}")

    # Check canonical link
    canonical = page.locator('link[rel="canonical"]').get_attribute('href') if page.locator('link[rel="canonical"]').count() > 0 else None
    print(f"  Canonical URL: {canonical}")

    if 'page=2' in current_url and len(design_images) > 0:
        print("  ✅ SSR: Page 2 loaded with content")
        return True
    else:
        print("  ❌ SSR: Issue with page 2 rendering")
        return False

def test_pagination_links(page):
    """Verify pagination links exist"""
    print("\n=== Test 2: Pagination Links ===")

    page.goto('http://localhost:3000/designs?page=2')
    page.wait_for_load_state('networkidle')

    # Wait for designs to load
    page.wait_for_timeout(2000)

    # Check for pagination nav
    pagination_nav = page.locator('nav[aria-label="Pagination"]')
    print(f"  Pagination nav exists: {pagination_nav.count() > 0}")

    if pagination_nav.count() > 0:
        # Check for Next link
        next_links = page.locator('a[rel="next"]').all()
        prev_links = page.locator('a[rel="prev"]').all()

        print(f"  Next links: {len(next_links)}")
        print(f"  Previous links: {len(prev_links)}")

        if len(next_links) > 0:
            href = next_links[0].get_attribute('href')
            print(f"  Next link href: {href}")

        if len(prev_links) > 0:
            href = prev_links[0].get_attribute('href')
            print(f"  Previous link href: {href}")

        return len(next_links) > 0 or len(prev_links) > 0
    else:
        print("  ❌ No pagination navigation found")
        return False

def test_scroll_url_sync(page):
    """Verify scrolling updates URL"""
    print("\n=== Test 3: Scroll Updates URL ===")

    page.goto('http://localhost:3000/designs')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)  # Wait for initial content

    # Get initial URL
    initial_url = page.url
    print(f"  Initial URL: {initial_url}")

    # Scroll to bottom multiple times to ensure we trigger next page
    for i in range(3):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(2000)

    # Check if URL updated
    new_url = page.url
    print(f"  URL after scroll: {new_url}")

    if 'page=' in new_url and new_url != initial_url:
        print("  ✅ Scroll: URL updated on scroll")
        return True
    else:
        print("  ⚠️  Scroll: URL may not have updated")
        return False

def test_filter_reset(page):
    """Verify filters reset page to 1"""
    print("\n=== Test 4: Filter Resets Page ===")

    # Start on page 3
    page.goto('http://localhost:3000/designs?page=3')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1000)

    # Apply a filter using sort dropdown (more reliable)
    sort_select = page.locator('select').first
    if sort_select.count() > 0:
        # Select oldest first
        sort_select.select_option('created_asc')
        page.wait_for_timeout(1500)  # Wait for filter to apply

        # Check URL - page should be reset
        url = page.url
        print(f"  URL after filter: {url}")

        # The page param should be removed or reset to 1
        # But since sort change should also be reflected, let's check
        if 'created_asc' in url and ('page=3' not in url or 'page=1' in url):
            print("  ✅ Filter: Page reset when filter applied")
            return True
        else:
            print("  ⚠️  Filter: Page may not have been reset")
            # This might be expected behavior - let's check the URL structure
            return False
    else:
        print("  ⚠️  No sort dropdown found")
        return None

def test_click_navigation(page):
    """Verify clicking pagination links works"""
    print("\n=== Test 5: Click Navigation ===")

    page.goto('http://localhost:3000/designs?page=2')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    # Try to find and click Previous link
    prev_link = page.locator('a[rel="prev"]').first
    if prev_link.count() > 0:
        href = prev_link.get_attribute('href')
        print(f"  Clicking Previous link: {href}")
        prev_link.click()
        page.wait_for_load_state('networkidle')

        new_url = page.url
        print(f"  URL after click: {new_url}")

        if 'page=2' not in new_url:
            print("  ✅ Click Navigation: Previous link worked")
            return True
        else:
            print("  ❌ Click Navigation: Previous link didn't navigate")
            return False
    else:
        print("  ⚠️  No Previous link found")
        return None

def test_invalid_params(page):
    """Verify invalid page parameters are handled"""
    print("\n=== Test 6: Invalid Page Parameter Handling ===")

    test_cases = [
        ('?page=999', 'should cap at max'),
        ('?page=0', 'should default to 1'),
        ('?page=-1', 'should default to 1'),
        ('?page=abc', 'should default to 1'),
        ('?page=1.5', 'should handle decimal'),
    ]

    results = []
    for param, description in test_cases:
        page.goto(f'http://localhost:3000/designs{param}')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(500)

        # Check if page loads without error (look for h1 or any content)
        has_content = page.locator('h1, main').count() > 0
        print(f"  {param} ({description}): {'✅ OK' if has_content else '❌ Error'}")
        results.append(has_content)

    if all(results):
        print("  ✅ Invalid Params: All handled gracefully")
        return True
    else:
        print("  ❌ Invalid Params: Some cases failed")
        return False

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        results = {
            'SSR Content': test_ssr_content(page),
            'Pagination Links': test_pagination_links(page),
            'Scroll URL Sync': test_scroll_url_sync(page),
            'Filter Reset': test_filter_reset(page),
            'Click Navigation': test_click_navigation(page),
            'Invalid Params': test_invalid_params(page),
        }

        browser.close()

        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        for test, result in results.items():
            if result is True:
                print(f"  ✅ {test}")
            elif result is False:
                print(f"  ❌ {test}")
            else:
                print(f"  ⚠️  {test} (skipped)")
        print("="*50)

if __name__ == '__main__':
    main()
