#!/usr/bin/env python3
"""
Extended testing for interactive elements and accessibility
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def test_interactive_elements(url="https://www.planx.io/"):
    """Test interactive elements on the page"""
    print("\n" + "=" * 50)
    print("INTERACTIVE ELEMENTS & ACCESSIBILITY TEST")
    print("=" * 50)

    output_dir = Path("/tmp/planx_test_results")
    output_dir.mkdir(exist_ok=True, parents=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(3000)

            print("\n[Interactive Elements]")
            print("-" * 50)

            # Get all interactive elements
            buttons = page.locator('button').all()
            links = page.locator('a').all()
            inputs = page.locator('input').all()
            forms = page.locator('form').all()

            print(f"✓ Buttons: {len(buttons)}")
            print(f"✓ Links: {len(links)}")
            print(f"✓ Inputs: {len(inputs)}")
            print(f"✓ Forms: {len(forms)}")

            # Sample buttons
            print("\nSample Buttons:")
            for i, btn in enumerate(buttons[:10]):
                try:
                    text = btn.text_content()
                    if text and text.strip():
                        print(f"  {i+1}. {text[:60]}")
                except:
                    pass

            # Sample links
            print("\nSample Links:")
            for i, link in enumerate(links[:10]):
                try:
                    href = link.get_attribute('href')
                    text = link.text_content()
                    if text and text.strip():
                        print(f"  {i+1}. {text[:60]} -> {href[:60]}")
                except:
                    pass

            print("\n[Accessibility Check]")
            print("-" * 50)

            # Check images without alt
            images = page.locator('img').all()
            images_without_alt = []
            for img in images:
                alt = img.get_attribute('alt')
                if not alt or alt.strip() == '':
                    src = img.get_attribute('src')
                    images_without_alt.append(src)

            print(f"✓ Total images: {len(images)}")
            print(f"✓ Images without alt: {len(images_without_alt)}")

            # Check heading structure
            headings = {
                "h1": page.locator('h1').count(),
                "h2": page.locator('h2').count(),
                "h3": page.locator('h3').count(),
                "h4": page.locator('h4').count(),
                "h5": page.locator('h5').count(),
                "h6": page.locator('h6').count()
            }
            print(f"✓ Heading structure: {headings}")

            # Check for main sections
            nav = page.locator('nav').count()
            main = page.locator('main').count()
            footer = page.locator('footer').count()
            header = page.locator('header').count()

            print(f"✓ Semantic elements:")
            print(f"  - Nav: {nav}")
            print(f"  - Main: {main}")
            print(f"  - Header: {header}")
            print(f"  - Footer: {footer}")

            # Save detailed data
            interactive_file = output_dir / "detailed_interactive.json"
            interactive_data = {
                "buttons": {
                    "count": len(buttons),
                    "sample": [btn.text_content()[:100] for btn in buttons[:10] if btn.text_content()]
                },
                "links": {
                    "count": len(links),
                    "sample": [{"text": link.text_content()[:100], "href": link.get_attribute('href')[:100]}
                              for link in links[:10] if link.text_content()]
                },
                "images": {
                    "total": len(images),
                    "without_alt": len(images_without_alt),
                    "without_alt_examples": images_without_alt[:5]
                },
                "headings": headings,
                "semantic": {
                    "nav": nav,
                    "main": main,
                    "header": header,
                    "footer": footer
                }
            }

            with open(interactive_file, 'w') as f:
                json.dump(interactive_data, f, indent=2)
            print(f"\n✓ Detailed data saved to: {interactive_file}")

            print("\n" + "=" * 50)
            print("EXTENDED TEST COMPLETED")
            print("=" * 50)

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()


if __name__ == "__main__":
    test_interactive_elements()
