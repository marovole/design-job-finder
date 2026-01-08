#!/usr/bin/env python3
"""
Comprehensive testing script for https://www.nail-designs.ai/
Tests all major functionality and generates a detailed report.
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser
from typing import Dict, List, Any

class NailDesignsTestSuite:
    def __init__(self):
        self.base_url = "https://www.nail-designs.ai"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": []
        }
        self.screenshots_dir = "/tmp/nail_designs_test_screenshots"

    def log_test(self, name: str, status: str, details: str = "", screenshot: str = ""):
        """Log test result"""
        result = {
            "name": name,
            "status": status,  # "PASS", "FAIL", "SKIP", "WARN"
            "details": details,
            "screenshot": screenshot,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results["tests"].append(result)

        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️",
            "WARN": "⚠️"
        }
        print(f"{status_icon.get(status, '•')} {name}: {status}")
        if details:
            print(f"   {details}")

    def take_screenshot(self, page: Page, name: str) -> str:
        """Take a screenshot and return the path"""
        import os
        os.makedirs(self.screenshots_dir, exist_ok=True)

        filename = f"{name.replace(' ', '_').lower()}_{int(time.time())}.png"
        filepath = f"{self.screenshots_dir}/{filename}"
        page.screenshot(path=filepath, full_page=True)
        return filepath

    def test_homepage_load(self, page: Page):
        """Test if homepage loads successfully"""
        try:
            page.goto(self.base_url, wait_until="networkidle", timeout=30000)
            screenshot = self.take_screenshot(page, "homepage")

            # Check if page loaded
            title = page.title()

            self.log_test(
                "Homepage Load",
                "PASS",
                f"Page title: {title}",
                screenshot
            )
        except Exception as e:
            self.log_test("Homepage Load", "FAIL", str(e))

    def test_feed_functionality(self, page: Page):
        """Test the design feed/gallery"""
        try:
            page.goto(self.base_url, wait_until="networkidle")

            # Wait for feed to load
            page.wait_for_timeout(2000)

            # Check for design cards
            design_cards = page.locator('[data-testid*="design"], .design-card, article, [class*="card"]').all()

            screenshot = self.take_screenshot(page, "feed")

            if len(design_cards) > 0:
                self.log_test(
                    "Feed Functionality",
                    "PASS",
                    f"Found {len(design_cards)} design items",
                    screenshot
                )
            else:
                self.log_test(
                    "Feed Functionality",
                    "WARN",
                    "No design cards found - feed might be empty or using different selectors",
                    screenshot
                )

        except Exception as e:
            self.log_test("Feed Functionality", "FAIL", str(e))

    def test_navigation_links(self, page: Page):
        """Test main navigation links"""
        try:
            page.goto(self.base_url, wait_until="networkidle")

            # Look for navigation links
            nav_links = page.locator('nav a, header a').all()

            links_found = []
            for link in nav_links[:10]:  # Check first 10 links
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text()
                    if href:
                        links_found.append(f"{text}: {href}")
                except:
                    continue

            screenshot = self.take_screenshot(page, "navigation")

            self.log_test(
                "Navigation Links",
                "PASS",
                f"Found {len(links_found)} navigation links",
                screenshot
            )

        except Exception as e:
            self.log_test("Navigation Links", "FAIL", str(e))

    def test_generator_page(self, page: Page):
        """Test the AI generator page"""
        try:
            page.goto(f"{self.base_url}/generator", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            screenshot = self.take_screenshot(page, "generator")

            # Check for form elements
            inputs = page.locator('input, select, textarea, button').all()

            # Look for generate button
            generate_buttons = page.locator('button:has-text("Generate"), button:has-text("生成")').all()

            self.log_test(
                "Generator Page Load",
                "PASS",
                f"Found {len(inputs)} form elements and {len(generate_buttons)} generate buttons",
                screenshot
            )

        except Exception as e:
            self.log_test("Generator Page Load", "FAIL", str(e))

    def test_tryon_page(self, page: Page):
        """Test the try-on page"""
        try:
            page.goto(f"{self.base_url}/try-on", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            screenshot = self.take_screenshot(page, "tryon")

            # Check for upload functionality
            upload_elements = page.locator('input[type="file"], button:has-text("Upload"), button:has-text("上传")').all()

            self.log_test(
                "Try-On Page Load",
                "PASS",
                f"Found {len(upload_elements)} upload elements",
                screenshot
            )

        except Exception as e:
            self.log_test("Try-On Page Load", "FAIL", str(e))

    def test_auth_pages(self, page: Page):
        """Test login and signup pages"""
        try:
            # Test login page
            page.goto(f"{self.base_url}/login", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            login_screenshot = self.take_screenshot(page, "login")

            login_inputs = page.locator('input[type="email"], input[type="password"]').all()

            self.log_test(
                "Login Page Load",
                "PASS",
                f"Found {len(login_inputs)} login inputs",
                login_screenshot
            )

            # Test signup page
            page.goto(f"{self.base_url}/signup", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            signup_screenshot = self.take_screenshot(page, "signup")

            signup_inputs = page.locator('input').all()

            self.log_test(
                "Signup Page Load",
                "PASS",
                f"Found {len(signup_inputs)} signup inputs",
                signup_screenshot
            )

        except Exception as e:
            self.log_test("Auth Pages", "FAIL", str(e))

    def test_dashboard_page(self, page: Page):
        """Test dashboard page (may require auth)"""
        try:
            page.goto(f"{self.base_url}/dashboard", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            screenshot = self.take_screenshot(page, "dashboard")

            # Check if redirected to login or if dashboard loads
            current_url = page.url

            if "/login" in current_url or "/signin" in current_url:
                self.log_test(
                    "Dashboard Page",
                    "PASS",
                    "Dashboard correctly redirects to login for unauthenticated users",
                    screenshot
                )
            else:
                self.log_test(
                    "Dashboard Page",
                    "WARN",
                    "Dashboard loaded without auth - might be publicly accessible or auth check missing",
                    screenshot
                )

        except Exception as e:
            self.log_test("Dashboard Page", "FAIL", str(e))

    def test_help_page(self, page: Page):
        """Test help page"""
        try:
            page.goto(f"{self.base_url}/help", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            screenshot = self.take_screenshot(page, "help")

            # Check for content
            content = page.content()
            has_content = len(content) > 1000

            self.log_test(
                "Help Page Load",
                "PASS" if has_content else "WARN",
                f"Page content length: {len(content)} chars",
                screenshot
            )

        except Exception as e:
            self.log_test("Help Page Load", "FAIL", str(e))

    def test_api_health(self, page: Page):
        """Test API health endpoint"""
        try:
            response = page.request.get(f"{self.base_url}/api/health")

            status = response.status
            body = response.text()

            if status == 200:
                self.log_test(
                    "API Health Check",
                    "PASS",
                    f"Status: {status}, Response: {body[:200]}"
                )
            else:
                self.log_test(
                    "API Health Check",
                    "FAIL",
                    f"Status: {status}"
                )

        except Exception as e:
            self.log_test("API Health Check", "FAIL", str(e))

    def test_responsive_design(self, page: Page):
        """Test responsive design on different viewport sizes"""
        try:
            viewports = [
                {"name": "Desktop", "width": 1920, "height": 1080},
                {"name": "Tablet", "width": 768, "height": 1024},
                {"name": "Mobile", "width": 375, "height": 667}
            ]

            for viewport in viewports:
                page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                page.goto(self.base_url, wait_until="networkidle")
                page.wait_for_timeout(1000)

                screenshot = self.take_screenshot(page, f"responsive_{viewport['name'].lower()}")

                self.log_test(
                    f"Responsive Design - {viewport['name']}",
                    "PASS",
                    f"Rendered at {viewport['width']}x{viewport['height']}",
                    screenshot
                )

        except Exception as e:
            self.log_test("Responsive Design", "FAIL", str(e))

    def test_performance(self, page: Page):
        """Test basic performance metrics"""
        try:
            start_time = time.time()
            page.goto(self.base_url, wait_until="networkidle", timeout=30000)
            load_time = time.time() - start_time

            # Get performance metrics
            metrics = page.evaluate("""() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                    loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                    responseTime: perfData.responseEnd - perfData.requestStart
                };
            }""")

            status = "PASS" if load_time < 5 else "WARN"

            self.log_test(
                "Performance Test",
                status,
                f"Total load time: {load_time:.2f}s, DOM: {metrics.get('domContentLoaded', 0):.0f}ms"
            )

        except Exception as e:
            self.log_test("Performance Test", "FAIL", str(e))

    def test_console_errors(self, page: Page):
        """Check for console errors"""
        console_messages = []

        def handle_console(msg):
            if msg.type in ['error', 'warning']:
                console_messages.append(f"{msg.type.upper()}: {msg.text}")

        page.on("console", handle_console)

        try:
            page.goto(self.base_url, wait_until="networkidle")
            page.wait_for_timeout(3000)

            if len(console_messages) == 0:
                self.log_test(
                    "Console Errors Check",
                    "PASS",
                    "No console errors or warnings found"
                )
            else:
                self.log_test(
                    "Console Errors Check",
                    "WARN",
                    f"Found {len(console_messages)} console messages: {console_messages[:3]}"
                )

        except Exception as e:
            self.log_test("Console Errors Check", "FAIL", str(e))

    def test_search_functionality(self, page: Page):
        """Test search functionality if available"""
        try:
            page.goto(self.base_url, wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Look for search input
            search_inputs = page.locator('input[type="search"], input[placeholder*="search"], input[placeholder*="搜索"]').all()

            screenshot = self.take_screenshot(page, "search")

            if len(search_inputs) > 0:
                self.log_test(
                    "Search Functionality",
                    "PASS",
                    f"Found {len(search_inputs)} search inputs",
                    screenshot
                )
            else:
                self.log_test(
                    "Search Functionality",
                    "SKIP",
                    "No search input found on homepage"
                )

        except Exception as e:
            self.log_test("Search Functionality", "FAIL", str(e))

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 Starting Comprehensive Test Suite for nail-designs.ai")
        print("="*60 + "\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = context.new_page()

            try:
                # Run all tests
                self.test_homepage_load(page)
                self.test_feed_functionality(page)
                self.test_navigation_links(page)
                self.test_generator_page(page)
                self.test_tryon_page(page)
                self.test_auth_pages(page)
                self.test_dashboard_page(page)
                self.test_help_page(page)
                self.test_api_health(page)
                self.test_responsive_design(page)
                self.test_performance(page)
                self.test_console_errors(page)
                self.test_search_functionality(page)

            finally:
                browser.close()

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60 + "\n")

        total = len(self.test_results["tests"])
        passed = sum(1 for t in self.test_results["tests"] if t["status"] == "PASS")
        failed = sum(1 for t in self.test_results["tests"] if t["status"] == "FAIL")
        warned = sum(1 for t in self.test_results["tests"] if t["status"] == "WARN")
        skipped = sum(1 for t in self.test_results["tests"] if t["status"] == "SKIP")

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"\nSuccess Rate: {(passed/total*100):.1f}%")

        # Save detailed results to JSON
        report_path = "/tmp/nail_designs_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")
        print(f"📸 Screenshots saved to: {self.screenshots_dir}")

        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    suite = NailDesignsTestSuite()
    suite.run_all_tests()
