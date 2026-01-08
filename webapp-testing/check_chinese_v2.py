from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 访问网站
    page.goto('https://test.wingame.com/')
    page.wait_for_load_state('networkidle')

    # 从截图看，右上角应该有一个设置按钮（齿轮图标）
    # 尝试直接访问带 zh locale 的 URL
    page.goto('https://test.wingame.com/?lang=zh')
    page.wait_for_load_state('networkidle')

    # 或尝试通过 cookie 或其他方式
    page.evaluate('localStorage.setItem("language", "zh")')
    page.reload()
    page.wait_for_load_state('networkidle')

    # 获取当前文本内容
    all_text = page.evaluate('() => document.body.innerText')

    print("=" * 60)
    print("【尝试切换后的内容】:")
    print("=" * 60)
    print(all_text[:2000])

    # 截图
    page.screenshot(path='/tmp/wingame_try_zh.png', full_page=True)

    browser.close()

print("\n✓ 完成")
