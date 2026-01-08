#!/usr/bin/env python3
"""
Comprehensive testing script for planx.io using Playwright with Chrome DevTools integration
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, ConsoleMessage
import traceback


class PlanxWebsiteTester:
    def __init__(self, url="https://www.planx.io/", output_dir="/tmp/planx_test_results"):
        self.url = url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "tests": {}
        }
        self.console_messages = []
        self.network_requests = []
        self.performance_metrics = {}

    def log_console(self, msg: ConsoleMessage):
        """Capture console messages"""
        self.console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        })

    def save_results(self):
        """Save test results to JSON file"""
        results_file = self.output_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ Results saved to: {results_file}")
        return results_file

    def take_screenshots(self, page, name):
        """Take full-page and viewport screenshots"""
        screenshots = {}

        # Full page screenshot
        full_page_path = self.output_dir / f"{name}_full_page.png"
        page.screenshot(path=str(full_page_path), full_page=True)
        screenshots['full_page'] = str(full_page_path)
        print(f"  ✓ Full page screenshot saved: {full_page_path}")

        # Viewport screenshot
        viewport_path = self.output_dir / f"{name}_viewport.png"
        page.screenshot(path=str(viewport_path), full_page=False)
        screenshots['viewport'] = str(viewport_path)
        print(f"  ✓ Viewport screenshot saved: {viewport_path}")

        return screenshots

    def test_basic_page_load(self, page):
        """Test 1: Basic page load"""
        print("\n[Test 1] Basic Page Load Test")
        print("-" * 50)

        try:
            # Navigate to page
            page.goto(self.url, wait_until='networkidle', timeout=60000)
            print(f"✓ Successfully loaded: {self.url}")

            # Wait for page to be fully rendered
            page.wait_for_timeout(3000)

            # Check if page has content
            title = page.title()
            print(f"✓ Page title: {title}")

            # Take screenshots
            screenshots = self.take_screenshots(page, "basic_load")

            # Check for main content
            body_text = page.text_content('body')
            has_content = len(body_text.strip()) > 100 if body_text else False
            print(f"✓ Page has substantial content: {has_content}")

            self.results['tests']['basic_load'] = {
                "status": "PASS",
                "title": title,
                "url_loaded": page.url,
                "has_content": has_content,
                "screenshots": screenshots
            }

            return True

        except Exception as e:
            print(f"✗ Failed to load page: {e}")
            traceback.print_exc()
            self.results['tests']['basic_load'] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False

    def test_console_logs(self, page):
        """Test 2: Console Errors and Warnings"""
        print("\n[Test 2] Console Logs Analysis")
        print("-" * 50)

        # Clear previous console messages
        self.console_messages = []

        # Set up console listener
        page.on('console', self.log_console)

        # Reload page to capture console logs
        page.reload(wait_until='networkidle')

        # Wait a bit for async logs
        page.wait_for_timeout(2000)

        # Analyze console messages
        errors = [msg for msg in self.console_messages if msg['type'] == 'error']
        warnings = [msg for msg in self.console_messages if msg['type'] == 'warning']

        print(f"✓ Total console messages: {len(self.console_messages)}")
        print(f"  - Errors: {len(errors)}")
        print(f"  - Warnings: {len(warnings)}")

        # Save console messages to file
        console_file = self.output_dir / "console_logs.json"
        with open(console_file, 'w') as f:
            json.dump(self.console_messages, f, indent=2)
        print(f"✓ Console logs saved to: {console_file}")

        # Show sample errors/warnings
        if errors:
            print("\nSample Errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error['text'][:100]}")

        self.results['tests']['console_logs'] = {
            "status": "PASS" if len(errors) == 0 else "WARN",
            "total_messages": len(self.console_messages),
            "errors": len(errors),
            "warnings": len(warnings),
            "console_file": str(console_file),
            "sample_errors": [msg['text'][:200] for msg in errors[:3]]
        }

    def test_network_requests(self, page):
        """Test 3: Network Analysis"""
        print("\n[Test 3] Network Requests Analysis")
        print("-" * 50)

        # Track responses
        responses = []

        def handle_response(response):
            responses.append({
                "url": response.url,
                "status": response.status,
                "content_type": response.headers.get('content-type', ''),
                "size": None  # Will be filled later
            })

        page.on('response', handle_response)

        # Reload page
        page.reload(wait_until='networkidle')
        page.wait_for_timeout(3000)

        # Get page size
        page_content = page.content()
        page_size = len(page_content.encode('utf-8'))

        # Analyze responses
        status_codes = {}
        resource_types = {}
        failed_requests = []

        for resp in responses:
            status = resp['status']
            status_codes[status] = status_codes.get(status, 0) + 1

            content_type = resp['content_type']
            if 'javascript' in content_type:
                resource_types['javascript'] = resource_types.get('javascript', 0) + 1
            elif 'css' in content_type:
                resource_types['css'] = resource_types.get('css', 0) + 1
            elif 'image' in content_type:
                resource_types['image'] = resource_types.get('image', 0) + 1
            elif 'font' in content_type:
                resource_types['font'] = resource_types.get('font', 0) + 1
            else:
                resource_types['other'] = resource_types.get('other', 0) + 1

            if status >= 400:
                failed_requests.append(resp)

        print(f"✓ Total requests: {len(responses)}")
        print(f"✓ Page HTML size: {page_size / 1024:.2f} KB")
        print(f"✓ Status codes: {status_codes}")
        print(f"✓ Resource types: {resource_types}")
        print(f"✓ Failed requests (4xx/5xx): {len(failed_requests)}")

        # Save network data
        network_file = self.output_dir / "network_requests.json"
        network_data = {
            "total_requests": len(responses),
            "status_codes": status_codes,
            "resource_types": resource_types,
            "failed_requests": len(failed_requests),
            "page_size_kb": round(page_size / 1024, 2),
            "responses": responses[:50]  # Save first 50 for analysis
        }

        with open(network_file, 'w') as f:
            json.dump(network_data, f, indent=2)
        print(f"✓ Network data saved to: {network_file}")

        self.results['tests']['network'] = {
            "status": "PASS" if len(failed_requests) == 0 else "WARN",
            "total_requests": len(responses),
            "status_codes": status_codes,
            "resource_types": resource_types,
            "failed_requests": len(failed_requests),
            "page_size_kb": round(page_size / 1024, 2),
            "network_file": str(network_file)
        }

    def test_performance(self, page):
        """Test 4: Performance Metrics"""
        print("\n[Test 4] Performance Metrics")
        print("-" * 50)

        # Reload page for fresh metrics
        page.reload(wait_until='networkidle')
        page.wait_for_timeout(3000)

        # Get Core Web Vitals and performance metrics
        metrics = page.evaluate("""
            () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                const fcp = paint.find(entry => entry.name === 'first-contentful-paint');

                return {
                    timing: navigation ? {
                        dns: navigation.domainLookupEnd - navigation.domainLookupStart,
                        tcp: navigation.connectEnd - navigation.connectStart,
                        ttfb: navigation.responseStart - navigation.requestStart,
                        download: navigation.responseEnd - navigation.responseStart,
                        dom_ready: navigation.domContentLoadedEventEnd - navigation.navigationStart,
                        load_complete: navigation.loadEventEnd - navigation.navigationStart
                    } : null,
                    paint: {
                        fcp: fcp ? fcp.startTime : null
                    },
                    memory: performance.memory ? {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    } : null
                };
            }
        """)

        print(f"✓ Navigation timing: {metrics.get('timing')}")
        print(f"✓ First Contentful Paint: {metrics.get('paint', {}).get('fcp')} ms")
        if metrics.get('memory'):
            memory_mb = metrics['memory']['used'] / (1024 * 1024)
            print(f"✓ Memory usage: {memory_mb:.2f} MB")

        # Save performance data
        perf_file = self.output_dir / "performance_metrics.json"
        with open(perf_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✓ Performance metrics saved to: {perf_file}")

        self.results['tests']['performance'] = {
            "status": "PASS",
            "metrics": metrics,
            "perf_file": str(perf_file)
        }

    def test_interactive_elements(self, page):
        """Test 5: Interactive Elements"""
        print("\n[Test 5] Interactive Elements Test")
        print("-" * 50)

        # Get all interactive elements
        buttons = page.locator('button').all()
        links = page.locator('a').all()
        inputs = page.locator('input').all()
        forms = page.locator('form').all()

        print(f"✓ Found {len(buttons)} buttons")
        print(f"✓ Found {len(links)} links")
        print(f"✓ Found {len(inputs)} inputs")
        print(f"✓ Found {len(forms)} forms")

        # Test some common elements
        tested_elements = []

        # Try to click a button (if exists and safe)
        if buttons:
            try:
                first_button = buttons[0]
                button_text = first_button.text_content()
                if button_text and len(button_text.strip()) > 0:
                    print(f"  - Testing button: {button_text[:50]}")
                    first_button.hover()
                    tested_elements.append({"type": "button", "text": button_text[:50]})
            except Exception as e:
                print(f"  - Note: Could not test button (may require interaction): {e}")

        # Test navigation (try a link if safe)
        if links:
            try:
                first_link = links[0]
                href = first_link.get_attribute('href')
                if href and not href.startswith('mailto:') and not href.startswith('javascript:'):
                    link_text = first_link.text_content() or href
                    print(f"  - Testing link: {link_text[:50]} -> {href[:50]}")
                    first_link.hover()
                    tested_elements.append({"type": "link", "text": link_text[:50], "href": href[:50]})
            except Exception as e:
                print(f"  - Note: Could not test link: {e}")

        # Save interactive elements data
        interactive_file = self.output_dir / "interactive_elements.json"
        interactive_data = {
            "buttons": len(buttons),
            "links": len(links),
            "inputs": len(inputs),
            "forms": len(forms),
            "tested_elements": tested_elements
        }

        with open(interactive_file, 'w') as f:
            json.dump(interactive_data, f, indent=2)
        print(f"✓ Interactive elements data saved to: {interactive_file}")

        self.results['tests']['interactive'] = {
            "status": "PASS",
            "counts": {
                "buttons": len(buttons),
                "links": len(links),
                "inputs": len(inputs),
                "forms": len(forms)
            },
            "interactive_file": str(interactive_file)
        }

    def test_accessibility(self, page):
        """Test 6: Basic Accessibility Checks"""
        print("\n[Test 6] Accessibility Checks")
        print("-" * 50)

        accessibility_issues = []

        # Check for alt attributes on images
        images = page.locator('img').all()
        images_without_alt = []
        for img in images:
            alt = img.get_attribute('alt')
            if not alt or alt.strip() == '':
                src = img.get_attribute('src')
                images_without_alt.append(src)

        if images_without_alt:
            accessibility_issues.append({
                "type": "images_without_alt",
                "count": len(images_without_alt),
                "examples": images_without_alt[:5]
            })
            print(f"⚠ Found {len(images_without_alt)} images without alt attributes")

        # Check for form inputs without labels
        inputs_without_labels = []
        inputs = page.locator('input').all()
        for inp in inputs:
            input_type = inp.get_attribute('type')
            if input_type not in ['hidden', 'submit', 'button']:
                # Check if has label
                has_label = False
                input_id = inp.get_attribute('id')
                if input_id:
                    label = page.locator(f'label[for="{input_id}"]').first
                    if label.count() > 0:
                        has_label = True

                if not has_label:
                    inputs_without_labels.append(input_id or "unknown")

        if inputs_without_labels:
            accessibility_issues.append({
                "type": "inputs_without_labels",
                "count": len(inputs_without_labels),
                "examples": inputs_without_labels[:5]
            })
            print(f"⚠ Found {len(inputs_without_labels)} inputs without labels")

        # Check for heading hierarchy
        headings = {
            "h1": page.locator('h1').count(),
            "h2": page.locator('h2').count(),
            "h3": page.locator('h3').count(),
            "h4": page.locator('h4').count(),
            "h5": page.locator('h5').count(),
            "h6": page.locator('h6').count()
        }
        print(f"✓ Heading structure: {headings}")

        # Save accessibility data
        a11y_file = self.output_dir / "accessibility_check.json"
        a11y_data = {
            "issues": accessibility_issues,
            "headings": headings,
            "images": {
                "total": len(images),
                "without_alt": len(images_without_alt)
            }
        }

        with open(a11y_file, 'w') as f:
            json.dump(a11y_data, f, indent=2)
        print(f"✓ Accessibility data saved to: {a11y_file}")

        self.results['tests']['accessibility'] = {
            "status": "PASS" if len(accessibility_issues) == 0 else "WARN",
            "issues_found": len(accessibility_issues),
            "issues": accessibility_issues,
            "a11y_file": str(a11y_file)
        }

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("PLANX.IO WEBSITE COMPREHENSIVE TEST")
        print("=" * 50)
        print(f"URL: {self.url}")
        print(f"Output Directory: {self.output_dir}")

        with sync_playwright() as p:
            # Launch browser with full DevTools capabilities
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Set up console logging
            page.on('console', self.log_console)

            try:
                # Run all tests
                self.test_basic_page_load(page)
                self.test_console_logs(page)
                self.test_network_requests(page)
                self.test_performance(page)
                self.test_interactive_elements(page)
                self.test_accessibility(page)

                print("\n" + "=" * 50)
                print("ALL TESTS COMPLETED")
                print("=" * 50)

            except Exception as e:
                print(f"\n✗ Fatal error during testing: {e}")
                traceback.print_exc()
                self.results['fatal_error'] = str(e)

            finally:
                browser.close()

        # Save all results
        results_file = self.save_results()
        return results_file


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.planx.io/"

    tester = PlanxWebsiteTester(url=url)
    results_file = tester.run_all_tests()

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    for test_name, test_result in tester.results['tests'].items():
        status = test_result.get('status', 'UNKNOWN')
        icon = "✓" if status == "PASS" else ("⚠" if status == "WARN" else "✗")
        print(f"{icon} {test_name}: {status}")

    print(f"\nDetailed results available at: {results_file}")
    print("\nTest completed successfully!")


if __name__ == "__main__":
    main()
