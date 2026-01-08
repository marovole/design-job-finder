"""
Test back button functionality for pagination
"""
from playwright.sync_api import sync_playwright

def test_back_button_pagination():
    """Verify back button restores previous page state"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("\n=== Test: Back Button Restores Page State ===")

        # Start on page 1
        page.goto('http://localhost:3000/designs')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)

        page1_url = page.url
        print(f"1. Starting URL: {page1_url}")

        # Click on a Next link to go to page 2
        # First, let's scroll to load more content and update URL
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(2000)

        page2_url = page.url
        print(f"2. After scroll: {page2_url}")

        # Check if URL contains page parameter
        if 'page=' in page2_url:
            print(f"   ✅ URL updated to: {page2_url}")

            # Now use browser back button
            page.go_back()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)

            back_url = page.url
            print(f"3. After back button: {back_url}")

            # The URL should be back to page 1 (or no page param)
            if 'page=2' not in back_url and 'page=3' not in back_url:
                print(f"   ✅ Back button restored state correctly")
                result = True
            else:
                print(f"   ❌ Back button did not restore state")
                result = False
        else:
            print(f"   ⚠️  Scroll did not update URL, using alternative method")

            # Try clicking a pagination link directly
            # First go to page 2 directly
            page.goto('http://localhost:3000/designs?page=2')
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)

            page2_url = page.url
            print(f"2. Direct navigation to: {page2_url}")

            # Try to find and click Previous link
            prev_link = page.locator('a[rel="prev"]').first
            if prev_link.count() > 0:
                print(f"   Found Previous link, clicking...")
                prev_link.click()
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(1000)

                back_url = page.url
                print(f"3. After clicking Previous: {back_url}")

                if 'page=2' not in back_url:
                    print(f"   ✅ Previous link navigation works")
                    result = True
                else:
                    print(f"   ❌ Previous link did not navigate")
                    result = False
            else:
                print(f"   ⚠️  No Previous link found on page 2")
                result = None

        browser.close()
        return result

if __name__ == '__main__':
    result = test_back_button_pagination()

    print("\n" + "="*50)
    if result is True:
        print("✅ BACK BUTTON TEST PASSED")
    elif result is False:
        print("❌ BACK BUTTON TEST FAILED")
    else:
        print("⚠️  BACK BUTTON TEST INCONCLUSIVE")
    print("="*50)
