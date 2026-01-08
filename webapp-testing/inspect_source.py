from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 访问网站
    page.goto('https://test.wingame.com/')
    page.wait_for_load_state('networkidle')

    # 获取完整 HTML 内容
    content = page.content()

    # 检查是否有中文翻译或 i18n 相关内容
    print("=" * 60)
    print("【检查中文翻译相关内容】:")
    print("=" * 60)

    # 检查 HTML 中的关键信息
    if '"zh"' in content or "'zh'" in content:
        print("✓ 发现中文语言标签")

    if '简体中文' in content:
        print("✓ 发现'简体中文'文本")

    if 'i18n' in content or 'i18next' in content or 'translation' in content:
        print("✓ 发现 i18n 相关内容")

    if 'Protection Fund' in content:
        print("✓ 英文文本 'Protection Fund' 存在")
    elif 'Protection Fun' in content:
        print("✗ 发现拼写错误：'Protection Fun'")

    # 搜索所有包含中文的内容
    lines_with_chinese = [line for line in content.split('\n') if any(ord(char) >= 0x4E00 and ord(char) <= 0x9FFF for char in line)]

    print(f"\n【HTML 中包含中文的行数】: {len(lines_with_chinese)}")
    if lines_with_chinese:
        print("\n【中文内容示例】:")
        for line in lines_with_chinese[:10]:
            # 只打印包含中文的部分，最多 200 字符
            print(line[:200])

    # 保存完整源代码用于后续分析
    with open('/tmp/wingame_source.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n✓ 完整源代码已保存到 /tmp/wingame_source.html")

    browser.close()
