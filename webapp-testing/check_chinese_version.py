from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 访问网站
    page.goto('https://test.wingame.com/')
    page.wait_for_load_state('networkidle')

    # 查找语言切换选项并点击设置按钮
    settings_button = page.locator('button').filter(has_text='设置').first

    # 尝试点击设置菜单中的齿轮图标
    gear_icon = page.locator('button[aria-label*="设置"], button[title*="设置"]').first

    # 或者直接找右上角的齿轮按钮
    all_buttons = page.locator('button').all()

    print(f"找到 {len(all_buttons)} 个按钮")

    # 尝试点击右上角的齿轮图标（通常在右上角）
    page.locator('button').last.click()
    page.wait_for_timeout(500)

    # 截图看当前状态
    page.screenshot(path='/tmp/settings_menu.png', full_page=True)

    # 查找语言选项
    language_links = page.locator('a, button').filter(has_text='简体中文')

    if language_links.count() > 0:
        print(f"找到 {language_links.count()} 个中文选项")
        # 点击中文选项
        language_links.first.click()
        page.wait_for_load_state('networkidle')

        # 获取中文版本的内容
        all_text = page.evaluate('() => document.body.innerText')
        print("\n" + "=" * 60)
        print("【中文版本内容】:")
        print("=" * 60)
        print(all_text)

        # 截图中文版本
        page.screenshot(path='/tmp/wingame_chinese.png', full_page=True)
    else:
        print("未找到直接的语言切换选项")
        # 显示当前页面内容
        all_text = page.evaluate('() => document.body.innerText')
        print(all_text)

    browser.close()

print("\n✓ 检查完成")
