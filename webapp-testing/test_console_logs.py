"""
Test to capture console logs
"""
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Collect console messages
        console_messages = []
        def on_console(msg):
            if msg.type == 'log':
                console_messages.append(msg.text)

        page.on('console', on_console)

        print("\n=== Capturing Console Logs ===")

        # Navigate to page 2
        page.goto('http://localhost:3000/designs?page=2')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)

        print("\nConsole Logs:")
        for msg in console_messages:
            if 'useInfiniteFeed' in msg:
                print(f"  {msg}")

        browser.close()

if __name__ == '__main__':
    main()
