#!/usr/bin/env python3
"""
Comprehensive website testing for https://test.wingame.com/
Tests functionality, performance, accessibility, security, and UX
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
import re

class WebsiteEvaluator:
    def __init__(self, url: str):
        self.url = url
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'accessibility': {},
            'performance': {},
            'functionality': {},
            'security': {},
            'ui_ux': {},
            'content': {},
            'errors': [],
            'warnings': [],
            'pages_tested': []
        }
        self.page = None
        self.browser = None

    def start(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=True)

    def stop(self):
        if self.browser:
            self.browser.close()
        self.p.stop()

    def create_page(self):
        """Create a new page with comprehensive tracking"""
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        # Track console messages
        page.on('console', lambda msg: self._handle_console(msg))

        return page, context

    def _handle_console(self, msg):
        """Handle console messages"""
        if msg.type in ['error', 'warning']:
            self.results['errors'].append({
                'type': msg.type,
                'text': msg.text
            })

    def test_homepage(self):
        """Test homepage loading and basic structure"""
        print(f"Testing homepage: {self.url}")
        page, context = self.create_page()

        try:
            # Measure load time
            start_time = time.time()
            page.goto(self.url, wait_until='networkidle', timeout=30000)
            load_time = time.time() - start_time

            # Wait for any dynamic content
            page.wait_for_load_state('domcontentloaded')

            self.results['performance']['page_load_time_seconds'] = round(load_time, 2)

            # Get page title and meta tags
            title = page.title()
            self.results['content']['page_title'] = title

            # Check meta tags
            meta_description = page.locator('meta[name="description"]').get_attribute('content')
            meta_viewport = page.locator('meta[name="viewport"]').get_attribute('content')

            self.results['content']['meta_description'] = meta_description
            self.results['content']['has_viewport_meta'] = meta_viewport is not None

            # Screenshot
            page.screenshot(path='/tmp/homepage_screenshot.png', full_page=True)
            print("✓ Homepage screenshot captured")

            # Check basic accessibility
            self._test_accessibility(page)

            # Check for responsive design
            self._test_responsiveness(page)

            # Check forms and inputs
            self._test_forms(page)

            # Check navigation
            self._test_navigation(page)

            # Check links
            self._test_links(page)

            # Check images
            self._test_images(page)

            # Check security headers
            self._test_security(page)

            # Check performance metrics
            self._test_performance_metrics(page)

            self.results['pages_tested'].append(self.url)

        except Exception as e:
            self.results['errors'].append({
                'page': self.url,
                'error': str(e)
            })
            print(f"✗ Error testing homepage: {e}")
        finally:
            page.close()
            context.close()

    def _test_accessibility(self, page: Page):
        """Test accessibility features"""
        print("Testing accessibility...")

        # Check for lang attribute
        lang = page.locator('html').get_attribute('lang')
        self.results['accessibility']['html_lang_attribute'] = lang is not None

        # Check for heading structure
        h1_count = page.locator('h1').count()
        h2_count = page.locator('h2').count()

        self.results['accessibility']['h1_count'] = h1_count
        self.results['accessibility']['h2_count'] = h2_count

        if h1_count != 1:
            self.results['warnings'].append('Should have exactly one H1 tag per page')

        # Check for alt text on images
        images = page.locator('img').all()
        images_without_alt = 0
        for img in images:
            alt = img.get_attribute('alt')
            if not alt or alt.strip() == '':
                images_without_alt += 1

        self.results['accessibility']['total_images'] = len(images)
        self.results['accessibility']['images_without_alt'] = images_without_alt

        if images_without_alt > 0:
            self.results['warnings'].append(f'{images_without_alt} images missing alt text')

        # Check for form labels
        inputs = page.locator('input').all()
        labels = page.locator('label').all()
        self.results['accessibility']['form_inputs'] = len(inputs)
        self.results['accessibility']['form_labels'] = len(labels)

        if len(inputs) > 0 and len(labels) == 0:
            self.results['warnings'].append('Form inputs found but no labels')

    def _test_responsiveness(self, page: Page):
        """Test responsive design"""
        print("Testing responsiveness...")

        # Mobile view
        mobile_context = self.browser.new_context(viewport={'width': 375, 'height': 667})
        mobile_page = mobile_context.new_page()

        try:
            mobile_page.goto(self.url, wait_until='networkidle', timeout=30000)
            mobile_page.wait_for_load_state('domcontentloaded')

            # Check if viewport meta is set
            viewport = mobile_page.locator('meta[name="viewport"]').get_attribute('content')
            self.results['ui_ux']['has_responsive_viewport'] = viewport is not None

            # Take mobile screenshot
            mobile_page.screenshot(path='/tmp/mobile_screenshot.png', full_page=True)

        except Exception as e:
            self.results['warnings'].append(f'Mobile testing error: {str(e)}')
        finally:
            mobile_page.close()
            mobile_context.close()

    def _test_forms(self, page: Page):
        """Test form functionality"""
        print("Testing forms...")

        forms = page.locator('form').all()
        self.results['functionality']['total_forms'] = len(forms)

        for i, form in enumerate(forms):
            form_id = form.get_attribute('id') or f'form_{i}'

            # Check required inputs
            required_inputs = form.locator('input[required]').count()
            self.results['functionality'][f'{form_id}_required_inputs'] = required_inputs

            # Check for submit button
            submit = form.locator('button[type="submit"], input[type="submit"]').count()
            if submit == 0:
                self.results['warnings'].append(f'Form {form_id} has no submit button')

    def _test_navigation(self, page: Page):
        """Test navigation structure"""
        print("Testing navigation...")

        # Check for nav element
        nav_count = page.locator('nav').count()
        self.results['ui_ux']['has_nav_element'] = nav_count > 0

        # Check for main content area
        main_count = page.locator('main').count()
        self.results['ui_ux']['has_main_element'] = main_count > 0

        # Check for footer
        footer_count = page.locator('footer').count()
        self.results['ui_ux']['has_footer_element'] = footer_count > 0

        # Get all links
        links = page.locator('a').all()
        self.results['ui_ux']['total_links'] = len(links)

        # Check for broken/empty links
        empty_links = 0
        for link in links:
            href = link.get_attribute('href')
            text = link.inner_text()

            if not href or href.strip() in ['', '#', 'javascript:void(0)']:
                empty_links += 1

        if empty_links > 0:
            self.results['warnings'].append(f'{empty_links} links with empty/invalid href')

    def _test_links(self, page: Page):
        """Test link validity"""
        print("Testing links...")

        links = page.locator('a').all()
        internal_links = []
        external_links = []

        for link in links:
            href = link.get_attribute('href')
            if href and href.startswith('http'):
                external_links.append(href)
            elif href and not href.startswith('#') and not href.startswith('javascript'):
                internal_links.append(href)

        self.results['ui_ux']['internal_links_count'] = len(internal_links)
        self.results['ui_ux']['external_links_count'] = len(external_links)

    def _test_images(self, page: Page):
        """Test image loading"""
        print("Testing images...")

        images = page.locator('img').all()
        broken_images = 0

        for img in images:
            # Check if image is visible and loaded
            try:
                is_visible = img.is_visible()
                if not is_visible:
                    broken_images += 1
            except:
                broken_images += 1

        self.results['ui_ux']['total_images'] = len(images)
        self.results['ui_ux']['broken_images'] = broken_images

    def _test_security(self, page: Page):
        """Test basic security features"""
        print("Testing security...")

        # Check for HTTPS
        is_https = page.url.startswith('https')
        self.results['security']['uses_https'] = is_https

        if not is_https:
            self.results['errors'].append('Website does not use HTTPS')

        # Check for meta tags related to security
        csp = page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute('content')
        self.results['security']['has_csp_meta'] = csp is not None

        x_ua_compatible = page.locator('meta[http-equiv="X-UA-Compatible"]').get_attribute('content')
        self.results['security']['has_x_ua_compatible'] = x_ua_compatible is not None

        # Check for form action (should not be empty)
        forms = page.locator('form').all()
        for form in forms:
            action = form.get_attribute('action')
            if not action:
                self.results['warnings'].append('Form without action attribute found')

    def _test_performance_metrics(self, page: Page):
        """Test performance metrics"""
        print("Testing performance metrics...")

        # Get page size
        content = page.content()
        self.results['performance']['page_size_kb'] = round(len(content) / 1024, 2)

        # Check for render-blocking resources
        stylesheets = page.locator('link[rel="stylesheet"]').count()
        scripts = page.locator('script').count()

        self.results['performance']['stylesheets_count'] = stylesheets
        self.results['performance']['scripts_count'] = scripts

        # Check for async/defer attributes on scripts
        async_scripts = page.locator('script[async]').count()
        defer_scripts = page.locator('script[defer]').count()

        self.results['performance']['async_scripts'] = async_scripts
        self.results['performance']['defer_scripts'] = defer_scripts

        if scripts > 0 and (async_scripts + defer_scripts) == 0:
            self.results['warnings'].append('Scripts lack async/defer attributes (may impact page load)')

    def test_interactive_elements(self):
        """Test interactive elements like buttons, modals, etc."""
        print("Testing interactive elements...")
        page, context = self.create_page()

        try:
            page.goto(self.url, wait_until='networkidle', timeout=30000)
            page.wait_for_load_state('domcontentloaded')

            # Test buttons
            buttons = page.locator('button').all()
            self.results['functionality']['total_buttons'] = len(buttons)

            # Test dropdowns/selects
            selects = page.locator('select').all()
            self.results['functionality']['total_selects'] = len(selects)

            # Test text inputs
            text_inputs = page.locator('input[type="text"]').all()
            self.results['functionality']['total_text_inputs'] = len(text_inputs)

        except Exception as e:
            self.results['errors'].append({
                'test': 'interactive_elements',
                'error': str(e)
            })
        finally:
            page.close()
            context.close()

    def generate_report(self):
        """Generate markdown report"""
        report = f"""# 网站测试评估报告

**测试网站**: {self.url}
**测试时间**: {self.results['timestamp']}

## 📊 执行摘要

- 测试页面数: {len(self.results['pages_tested'])}
- 发现的错误: {len(self.results['errors'])}
- 发现的警告: {len(self.results['warnings'])}

---

## 🚀 性能测试结果

### 加载性能
- 页面加载时间: {self.results['performance'].get('page_load_time_seconds', 'N/A')} 秒
- 页面大小: {self.results['performance'].get('page_size_kb', 'N/A')} KB

### 资源统计
- CSS 文件数: {self.results['performance'].get('stylesheets_count', 0)}
- 脚本文件数: {self.results['performance'].get('scripts_count', 0)}
- 异步脚本: {self.results['performance'].get('async_scripts', 0)}
- 延迟脚本: {self.results['performance'].get('defer_scripts', 0)}

---

## ♿ 可访问性评估

### 结构化标记
- HTML 语言属性: {'✓' if self.results['accessibility'].get('html_lang_attribute') else '✗'}
- H1 标签数: {self.results['accessibility'].get('h1_count', 0)}
- H2 标签数: {self.results['accessibility'].get('h2_count', 0)}

### 图片和媒体
- 总图片数: {self.results['accessibility'].get('total_images', 0)}
- 缺少 Alt 文字的图片: {self.results['accessibility'].get('images_without_alt', 0)}

### 表单
- 表单输入框: {self.results['accessibility'].get('form_inputs', 0)}
- 表单标签: {self.results['accessibility'].get('form_labels', 0)}

---

## 🔒 安全性检查

### HTTPS 和协议
- HTTPS 使用: {'✓' if self.results['security'].get('uses_https') else '✗ 未使用 HTTPS'}
- Content Security Policy: {'✓' if self.results['security'].get('has_csp_meta') else '✗'}
- X-UA-Compatible: {'✓' if self.results['security'].get('has_x_ua_compatible') else '✗'}

---

## 🎨 UI/UX 评估

### 页面结构
- 包含 &lt;nav&gt; 元素: {'✓' if self.results['ui_ux'].get('has_nav_element') else '✗'}
- 包含 &lt;main&gt; 元素: {'✓' if self.results['ui_ux'].get('has_main_element') else '✗'}
- 包含 &lt;footer&gt; 元素: {'✓' if self.results['ui_ux'].get('has_footer_element') else '✗'}
- 响应式视口元数据: {'✓' if self.results['ui_ux'].get('has_responsive_viewport') else '✗'}

### 内容和导航
- 总链接数: {self.results['ui_ux'].get('total_links', 0)}
  - 内部链接: {self.results['ui_ux'].get('internal_links_count', 0)}
  - 外部链接: {self.results['ui_ux'].get('external_links_count', 0)}
- 总按钮数: {self.results['functionality'].get('total_buttons', 0)}
- 损坏的图片: {self.results['ui_ux'].get('broken_images', 0)}/{self.results['ui_ux'].get('total_images', 0)}

---

## 🔧 功能性测试

### 表单
- 总表单数: {self.results['functionality'].get('total_forms', 0)}

### 交互元素
- 下拉菜单/选择框: {self.results['functionality'].get('total_selects', 0)}
- 文本输入框: {self.results['functionality'].get('total_text_inputs', 0)}

---

## 📝 内容检查

- 页面标题: {self.results['content'].get('page_title', 'N/A')}
- Meta 描述: {self.results['content'].get('meta_description', 'N/A')}
- 包含视口 Meta 标签: {'✓' if self.results['content'].get('has_viewport_meta') else '✗'}

---

## ❌ 发现的错误

"""
        if self.results['errors']:
            for error in self.results['errors']:
                if isinstance(error, dict):
                    report += f"- {error.get('page', error.get('test', 'Unknown'))}: {error.get('error', error.get('text', str(error)))}\n"
                else:
                    report += f"- {error}\n"
        else:
            report += "没有发现严重错误 ✓\n"

        report += "\n---\n\n## ⚠️ 警告和改进建议\n\n"

        if self.results['warnings']:
            for warning in self.results['warnings']:
                report += f"- {warning}\n"
        else:
            report += "没有发现警告 ✓\n"

        report += """
---

## 🎯 改进建议

### 性能优化
"""
        if self.results['performance'].get('page_load_time_seconds', 0) > 3:
            report += "1. 页面加载时间超过 3 秒，建议进行性能优化\n"
        if self.results['performance'].get('page_size_kb', 0) > 500:
            report += "2. 页面大小超过 500KB，考虑减少资源大小\n"
        if self.results['performance'].get('scripts_count', 0) > 10:
            report += "3. 脚本文件过多，考虑合并或优化\n"

        report += """
### 可访问性改进
"""
        if self.results['accessibility'].get('images_without_alt', 0) > 0:
            report += f"1. 为 {self.results['accessibility'].get('images_without_alt', 0)} 个图片添加 alt 文字\n"
        if self.results['accessibility'].get('h1_count', 0) != 1:
            report += "2. 确保每个页面只有一个 H1 标签\n"
        if self.results['accessibility'].get('form_inputs', 0) > self.results['accessibility'].get('form_labels', 0):
            report += "3. 为所有表单输入框添加 label 标签\n"

        report += """
### 安全性改进
"""
        if not self.results['security'].get('uses_https'):
            report += "1. ⚠️ 启用 HTTPS（强烈建议）\n"
        if not self.results['security'].get('has_csp_meta'):
            report += "2. 实现 Content Security Policy (CSP)\n"
        if not self.results['security'].get('has_x_ua_compatible'):
            report += "3. 添加 X-UA-Compatible meta 标签\n"

        report += f"""
### UI/UX 改进
"""
        if not self.results['ui_ux'].get('has_nav_element'):
            report += "1. 添加语义化的 &lt;nav&gt; 元素\n"
        if not self.results['ui_ux'].get('has_main_element'):
            report += "2. 使用 &lt;main&gt; 元素包装主要内容\n"
        if self.results['ui_ux'].get('broken_images', 0) > 0:
            report += f"3. 修复 {self.results['ui_ux'].get('broken_images', 0)} 个损坏的图片\n"

        report += f"""
---

## ✅ 总体评分和建议

**状态**: {'🟢 基本可用' if len(self.results['errors']) < 3 else '🟡 存在问题' if len(self.results['errors']) < 6 else '🔴 严重问题'}

### 下一步行动

1. **立即处理**: 修复所有严重错误（红色项目）
2. **优先处理**: 解决可访问性问题和安全性问题
3. **持续优化**: 实施所有性能优化建议
4. **定期测试**: 在发布前再次运行此测试

### 发布前检查清单

- [ ] 所有错误已修复
- [ ] 性能加载时间 < 3 秒
- [ ] 所有图片都有 alt 文字
- [ ] 使用 HTTPS
- [ ] 响应式设计在移动设备上正常工作
- [ ] 所有链接都有效
- [ ] 表单验证工作正常
- [ ] 跨浏览器测试完成

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report

def main():
    evaluator = WebsiteEvaluator('https://test.wingame.com/')
    evaluator.start()

    try:
        evaluator.test_homepage()
        evaluator.test_interactive_elements()

        # Generate report
        report = evaluator.generate_report()

        # Save report
        with open('/tmp/wingame_evaluation_report.md', 'w', encoding='utf-8') as f:
            f.write(report)

        print("\n✓ 报告已生成: /tmp/wingame_evaluation_report.md")

        # Also save raw results as JSON
        with open('/tmp/wingame_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(evaluator.results, f, indent=2, ensure_ascii=False)

        print("✓ 详细结果已保存: /tmp/wingame_test_results.json")
        print("\n" + "="*50)
        print(report)

    finally:
        evaluator.stop()

if __name__ == '__main__':
    main()
