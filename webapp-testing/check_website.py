from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 访问网站
    page.goto('https://test.wingame.com/')
    page.wait_for_load_state('networkidle')

    # 截图以查看整体内容
    page.screenshot(path='/tmp/wingame_screenshot.png', full_page=True)

    # 获取页面内容
    content = page.content()
    text_content = page.locator('body').text_content()

    # 提取所有可见文本
    all_text = page.evaluate('() => document.body.innerText')

    print("=" * 60)
    print("网站文本内容检查")
    print("=" * 60)
    print("\n【提取的所有可见文本】:\n")
    print(all_text)

    print("\n" + "=" * 60)
    print("【HTML 片段（前 2000 字符）】:\n")
    print(content[:2000])

    browser.close()

print("\n✓ 截图已保存到 /tmp/wingame_screenshot.png")
