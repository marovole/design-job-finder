"""
Debug pagination links issue
"""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("\n=== Debug: Pagination Links ===")

        # Navigate to page 2
        page.goto('http://localhost:3000/designs?page=2')
        page.wait_for_load_state('networkidle')

        # Wait for data to load
        page.wait_for_timeout(3000)

        # Check page content
        print(f"Current URL: {page.url}")

        # Look for pagination nav
        pagination_nav = page.locator('nav[aria-label="Pagination"]')
        print(f"Pagination nav count: {pagination_nav.count()}")

        if pagination_nav.count() > 0:
            print("✅ Pagination nav exists")

            # Get the inner HTML of the pagination nav
            nav_html = pagination_nav.inner_html()
            print(f"\nPagination HTML:")
            print(nav_html[:500])

            # Check for links
            all_links = page.locator('nav[aria-label="Pagination"] a').all()
            print(f"\nTotal links in pagination: {len(all_links)}")

            for i, link in enumerate(all_links):
                href = link.get_attribute('href')
                rel = link.get_attribute('rel')
                text = link.inner_text()
                print(f"  Link {i+1}: href={href}, rel={rel}, text='{text}'")

        else:
            print("❌ No pagination nav found")

            # Debug: check if there are any designs loaded
            design_images = page.locator('img').all()
            print(f"Images on page: {len(design_images)}")

            # Check for loading state
            loading_indicators = page.locator('[class*="loading"], [class*="spinner"]').all()
            print(f"Loading indicators: {len(loading_indicators)}")

        browser.close()

if __name__ == '__main__':
    main()
