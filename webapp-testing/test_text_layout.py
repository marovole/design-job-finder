#!/usr/bin/env python3
"""
文本规范和布局优化检查
检查所有文本的规范性、排版、布局等问题
"""

import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from typing import List, Dict, Tuple

class TextLayoutAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'text_issues': {
                'spelling': [],
                'grammar': [],
                'punctuation': [],
                'consistency': [],
                'length': [],
                'encoding': [],
                'duplicates': []
            },
            'layout_issues': {
                'spacing': [],
                'alignment': [],
                'typography': [],
                'responsive': [],
                'contrast': [],
                'readability': [],
                'line_height': [],
                'orphans_widows': []
            },
            'text_metrics': {
                'total_text_elements': 0,
                'total_headings': 0,
                'total_paragraphs': 0,
                'total_lists': 0,
                'avg_paragraph_length': 0,
                'avg_line_length': 0,
                'font_sizes_used': [],
                'font_families_used': [],
                'color_combinations': []
            },
            'summary': {}
        }
        self.page = None
        self.browser = None
        self.p = None

    def start(self):
        """启动浏览器"""
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=True)

    def stop(self):
        """停止浏览器"""
        if self.browser:
            self.browser.close()
        if self.p:
            self.p.stop()

    def analyze_page(self):
        """分析页面文本和布局"""
        print(f"分析页面: {self.url}")

        context = self.browser.new_context(viewport={'width': 1920, 'height': 1080})
        self.page = context.new_page()

        try:
            self.page.goto(self.url, wait_until='networkidle', timeout=30000)
            self.page.wait_for_load_state('domcontentloaded')

            # 收集所有文本
            print("✓ 页面已加载，开始分析...")
            self._extract_all_text()
            self._analyze_typography()
            self._analyze_layout()
            self._analyze_readability()
            self._check_text_issues()
            self._analyze_responsive_text()
            self._generate_metrics()

            # 截图
            self.page.screenshot(path='/tmp/text_layout_desktop.png', full_page=True)
            print("✓ 桌面版截图已保存")

            # 移动视图
            mobile_context = self.browser.new_context(viewport={'width': 375, 'height': 667})
            mobile_page = mobile_context.new_page()
            mobile_page.goto(self.url, wait_until='networkidle', timeout=30000)
            mobile_page.wait_for_load_state('domcontentloaded')
            mobile_page.screenshot(path='/tmp/text_layout_mobile.png', full_page=True)
            mobile_page.close()
            mobile_context.close()
            print("✓ 移动版截图已保存")

        except Exception as e:
            self.results['summary']['error'] = str(e)
            print(f"✗ 分析出错: {e}")
        finally:
            self.page.close()
            context.close()

    def _extract_all_text(self):
        """提取页面所有文本"""
        print("提取文本内容...")

        # 获取所有文本元素
        headings = self.page.locator('h1, h2, h3, h4, h5, h6').all()
        paragraphs = self.page.locator('p').all()
        spans = self.page.locator('span').all()
        buttons = self.page.locator('button, a').all()
        lists = self.page.locator('li').all()

        all_text_elements = {
            'headings': [],
            'paragraphs': [],
            'spans': [],
            'buttons': [],
            'list_items': []
        }

        # 收集标题
        for h in headings:
            text = h.inner_text()
            tag = h.evaluate('el => el.tagName')
            if text.strip():
                all_text_elements['headings'].append({
                    'tag': tag,
                    'text': text.strip(),
                    'length': len(text.strip())
                })

        # 收集段落
        for p in paragraphs:
            text = p.inner_text()
            if text.strip() and len(text.strip()) > 10:
                all_text_elements['paragraphs'].append({
                    'text': text.strip(),
                    'length': len(text.strip()),
                    'lines': len(text.strip().split('\n'))
                })

        # 收集按钮和链接文本
        for btn in buttons:
            text = btn.inner_text()
            if text.strip() and len(text.strip()) < 100:
                all_text_elements['buttons'].append(text.strip())

        # 收集列表项
        for li in lists:
            text = li.inner_text()
            if text.strip():
                all_text_elements['list_items'].append(text.strip())

        self.results['text_metrics']['total_text_elements'] = len(headings) + len(paragraphs) + len(buttons)
        self.results['text_metrics']['total_headings'] = len(headings)
        self.results['text_metrics']['total_paragraphs'] = len(paragraphs)
        self.results['text_metrics']['total_lists'] = len(lists)

        if all_text_elements['paragraphs']:
            total_length = sum(p['length'] for p in all_text_elements['paragraphs'])
            self.results['text_metrics']['avg_paragraph_length'] = round(total_length / len(all_text_elements['paragraphs']), 1)

        return all_text_elements

    def _analyze_typography(self):
        """分析排版"""
        print("分析排版...")

        # 获取所有使用的字体
        fonts = self.page.locator('*').evaluate_all(
            '''elements => {
                const fonts = new Set();
                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const font = style.fontFamily;
                    const size = style.fontSize;
                    if (font && font !== 'serif' && font !== 'sans-serif') {
                        fonts.add(font + ' (' + size + ')');
                    }
                });
                return Array.from(fonts).slice(0, 20);
            }'''
        )

        self.results['text_metrics']['font_families_used'] = list(set(fonts))

        # 检查字体大小的一致性
        headings = self.page.locator('h1, h2, h3, h4, h5, h6').all()
        heading_sizes = []

        for h in headings:
            size = h.evaluate('el => window.getComputedStyle(el).fontSize')
            heading_sizes.append(size)

        if heading_sizes:
            unique_sizes = len(set(heading_sizes))
            if unique_sizes > 4:
                self.results['layout_issues']['typography'].append(
                    f'标题大小不一致，使用了 {unique_sizes} 种不同的字体大小'
                )

    def _analyze_layout(self):
        """分析布局问题"""
        print("分析布局...")

        # 检查文本对齐
        paragraphs = self.page.locator('p').all()
        alignment_count = {}

        for p in paragraphs:
            text_align = p.evaluate('el => window.getComputedStyle(el).textAlign')
            alignment_count[text_align] = alignment_count.get(text_align, 0) + 1

        if len(alignment_count) > 2:
            self.results['layout_issues']['alignment'].append(
                f'文本对齐方式不统一: {alignment_count}'
            )

        # 检查行高
        elements = self.page.locator('p, div, span').all()
        line_heights = []

        for el in elements[:20]:  # 仅检查前20个元素以提高性能
            try:
                line_height = el.evaluate('el => window.getComputedStyle(el).lineHeight')
                if line_height and line_height != 'normal':
                    line_heights.append(line_height)
            except:
                pass

        if line_heights:
            avg_line_height = ', '.join(set(line_heights))
            self.results['text_metrics']['avg_line_height'] = avg_line_height

        # 检查间距
        self._check_spacing()

    def _check_spacing(self):
        """检查间距问题"""
        paragraphs = self.page.locator('p').all()

        for p in paragraphs[:5]:
            try:
                margin_bottom = p.evaluate('el => window.getComputedStyle(el).marginBottom')
                margin_top = p.evaluate('el => window.getComputedStyle(el).marginTop')
                padding = p.evaluate('el => window.getComputedStyle(el).padding')

                if margin_bottom == '0px' and margin_top == '0px':
                    self.results['layout_issues']['spacing'].append(
                        '某些元素的上下间距为0，可能影响可读性'
                    )
                    break
            except:
                pass

    def _analyze_readability(self):
        """分析可读性"""
        print("分析可读性...")

        # 获取字体大小和行长度
        paragraphs = self.page.locator('p').all()

        for p in paragraphs[:10]:
            try:
                font_size = p.evaluate('el => window.getComputedStyle(el).fontSize')
                # 提取数字
                size_px = int(re.findall(r'\d+', font_size)[0])

                # 推荐的最小字体大小是14px
                if size_px < 14:
                    self.results['layout_issues']['readability'].append(
                        f'字体过小: {font_size}（建议最少14px）'
                    )
                    break

                # 获取行宽度
                width = p.evaluate('el => el.offsetWidth')

                # 理想的行长度是50-80个字符（大约600-900px）
                if width > 900:
                    self.results['layout_issues']['readability'].append(
                        f'行长度过长: {width}px（建议600-900px）'
                    )
                elif width < 300:
                    self.results['layout_issues']['readability'].append(
                        f'行长度过短: {width}px（建议600-900px）'
                    )
            except:
                pass

    def _check_text_issues(self):
        """检查文本问题"""
        print("检查文本问题...")

        # 获取所有文本
        text_elements = self.page.locator('h1, h2, h3, h4, h5, h6, p, span, button, a').all()
        seen_texts = {}

        for el in text_elements:
            text = el.inner_text()
            if text and len(text.strip()) > 5:
                text_clean = text.strip()

                # 检查重复
                if text_clean in seen_texts:
                    seen_texts[text_clean] += 1
                else:
                    seen_texts[text_clean] = 1

                # 检查文本问题
                self._check_text_quality(text_clean)

        # 报告重复文本
        for text, count in seen_texts.items():
            if count > 2:
                self.results['text_issues']['duplicates'].append({
                    'text': text[:100] + ('...' if len(text) > 100 else ''),
                    'count': count
                })

    def _check_text_quality(self, text: str):
        """检查单个文本的质量"""

        # 检查中英文混合的标点符号
        if re.search(r'[\u4e00-\u9fff]。', text) or re.search(r'[\u4e00-\u9fff]，', text):
            pass  # 这是正确的
        elif re.search(r'[\u4e00-\u9fff]\.', text) or re.search(r'[\u4e00-\u9fff],', text):
            self.results['text_issues']['punctuation'].append(
                f'标点符号不规范: "{text[:50]}..." (应使用中文标点)'
            )

        # 检查多余空格
        if '  ' in text:
            if 'spacing' not in self.results['text_issues']:
                self.results['text_issues']['spacing'] = []
            self.results['text_issues']['spacing'].append(
                f'存在多余空格: "{text[:50]}..."'
            )

        # 检查特殊字符
        if re.search(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', text):
            self.results['text_issues']['encoding'].append(
                f'存在不可见字符: "{text[:50]}..."'
            )

        # 检查连续大写字母（可能是缩写）
        if re.search(r'[A-Z]{5,}', text):
            pass  # 某些缩写可能是正常的

    def _analyze_responsive_text(self):
        """分析响应式文本"""
        print("分析响应式设计...")

        # 测试移动视图
        mobile_context = self.browser.new_context(viewport={'width': 375, 'height': 667})
        mobile_page = mobile_context.new_page()

        try:
            mobile_page.goto(self.url, wait_until='networkidle', timeout=30000)
            mobile_page.wait_for_load_state('domcontentloaded')

            # 检查移动设备上的字体大小
            paragraphs = mobile_page.locator('p').all()

            for p in paragraphs[:5]:
                try:
                    font_size = p.evaluate('el => window.getComputedStyle(el).fontSize')
                    size_px = int(re.findall(r'\d+', font_size)[0])

                    if size_px < 12:
                        self.results['layout_issues']['responsive'].append(
                            f'移动设备字体过小: {font_size}'
                        )
                        break
                except:
                    pass

        except Exception as e:
            self.results['layout_issues']['responsive'].append(f'无法测试响应式设计: {str(e)}')
        finally:
            mobile_page.close()
            mobile_context.close()

    def _generate_metrics(self):
        """生成汇总指标"""
        print("生成汇总指标...")

        total_issues = (
            len(self.results['text_issues']['spelling']) +
            len(self.results['text_issues']['grammar']) +
            len(self.results['text_issues']['punctuation']) +
            len(self.results['layout_issues']['spacing']) +
            len(self.results['layout_issues']['alignment']) +
            len(self.results['layout_issues']['typography'])
        )

        self.results['summary'] = {
            'total_issues': total_issues,
            'text_issues_count': sum(len(v) for v in self.results['text_issues'].values()),
            'layout_issues_count': sum(len(v) for v in self.results['layout_issues'].values()),
            'priority_level': self._calculate_priority(total_issues),
            'overall_score': self._calculate_score()
        }

    def _calculate_priority(self, issue_count: int) -> str:
        """计算优先级"""
        if issue_count > 20:
            return '🔴 严重'
        elif issue_count > 10:
            return '🟡 中等'
        elif issue_count > 5:
            return '🟠 轻微'
        else:
            return '🟢 良好'

    def _calculate_score(self) -> int:
        """计算总体评分(0-100)"""
        total_issues = sum(
            len(v) for k, v in self.results['text_issues'].items()
        ) + sum(
            len(v) for k, v in self.results['layout_issues'].items()
        )

        score = max(0, 100 - (total_issues * 2))
        return score

    def generate_report(self) -> str:
        """生成Markdown报告"""
        report = f"""# PLANX 网站文本规范和布局优化报告

**网站**: {self.url}
**测试日期**: {self.results['timestamp']}
**总体评分**: {self.results['summary'].get('overall_score', 0)}/100
**优先级**: {self.results['summary'].get('priority_level', '未知')}

---

## 📊 执行摘要

本报告对 PLANX 网站的文本规范性、排版、布局等方面进行了全面检查。

- 发现的文本问题: {self.results['summary'].get('text_issues_count', 0)}
- 发现的布局问题: {self.results['summary'].get('layout_issues_count', 0)}
- 总计问题数: {self.results['summary'].get('total_issues', 0)}

---

## 📐 文本指标

| 指标 | 数值 |
|------|------|
| 文本元素总数 | {self.results['text_metrics']['total_text_elements']} |
| 标题总数 | {self.results['text_metrics']['total_headings']} |
| 段落总数 | {self.results['text_metrics']['total_paragraphs']} |
| 列表项总数 | {self.results['text_metrics']['total_lists']} |
| 平均段落长度 | {self.results['text_metrics']['avg_paragraph_length']} 字符 |
| 行高设置 | {self.results['text_metrics'].get('avg_line_height', '未检测')} |

### 使用的字体

```
{chr(10).join(self.results['text_metrics']['font_families_used'][:10]) if self.results['text_metrics']['font_families_used'] else '未检测'}
```

---

## 🔴 文本规范问题

### 标点符号不规范

"""
        if self.results['text_issues']['punctuation']:
            for issue in self.results['text_issues']['punctuation'][:5]:
                report += f"- {issue}\n"
        else:
            report += "✅ 未发现问题\n"

        report += "\n### 重复文本\n\n"
        if self.results['text_issues']['duplicates']:
            for dup in self.results['text_issues']['duplicates'][:5]:
                report += f"- \"{dup['text']}\" 出现 {dup['count']} 次\n"
        else:
            report += "✅ 未发现重复文本\n"

        report += "\n### 其他文本问题\n\n"
        if 'spacing' in self.results['text_issues'] and self.results['text_issues']['spacing']:
            report += "**空格问题**:\n"
            for issue in self.results['text_issues']['spacing'][:3]:
                report += f"- {issue}\n"
        else:
            report += "✅ 未发现其他问题\n"

        report += "\n---\n\n## 📐 布局问题\n\n### 字体和排版\n\n"
        if self.results['layout_issues']['typography']:
            for issue in self.results['layout_issues']['typography']:
                report += f"- {issue}\n"
        else:
            report += "✅ 排版一致\n"

        report += "\n### 文本对齐\n\n"
        if self.results['layout_issues']['alignment']:
            for issue in self.results['layout_issues']['alignment']:
                report += f"- {issue}\n"
        else:
            report += "✅ 对齐规范\n"

        report += "\n### 间距\n\n"
        if self.results['layout_issues']['spacing']:
            for issue in self.results['layout_issues']['spacing']:
                report += f"- {issue}\n"
        else:
            report += "✅ 间距合理\n"

        report += "\n### 可读性\n\n"
        if self.results['layout_issues']['readability']:
            for issue in self.results['layout_issues']['readability']:
                report += f"- ⚠️ {issue}\n"
        else:
            report += "✅ 可读性良好\n"

        report += "\n### 响应式设计\n\n"
        if self.results['layout_issues']['responsive']:
            for issue in self.results['layout_issues']['responsive']:
                report += f"- ⚠️ {issue}\n"
        else:
            report += "✅ 响应式设计良好\n"

        report += """

---

## ✅ 优化建议

### 文本规范建议

1. **标点符号规范化**
   - 使用正确的中文标点（。，！？等）
   - 避免混合使用中英文标点符号
   - 中文句子后使用中文标点符号

2. **避免文本重复**
   - 检查是否有重复内容可以合并
   - 对于必须重复的内容，考虑使用引用或链接

3. **空格处理**
   - 删除多余的空格
   - 确保单词间正确的空格数
   - 中英文之间保持一致的间距

### 排版优化建议

1. **字体选择**
   - 使用不超过 2-3 个主要字体
   - 标题和正文字体应有对比
   - 确保字体在所有设备上都能正确加载

2. **字体大小层次**
   - H1: 32-40px
   - H2: 24-28px
   - H3: 20-24px
   - 正文: 14-16px
   - 辅助文本: 12px

3. **行高设置**
   - 正文行高: 1.5-1.8
   - 标题行高: 1.2-1.3
   - 列表项行高: 1.6-1.8

4. **行长优化**
   - 桌面: 600-900px (60-80个字符)
   - 平板: 400-600px
   - 手机: 280-400px

5. **间距规范**
   - 段落间距: 1.5-2em
   - 字母间距(letter-spacing): 0-0.05em
   - 单词间距: 正常

### 响应式文本建议

1. **移动设备优化**
   - 基础字体大小: 16px（防止自动放大）
   - 最小字体: 12px
   - 标题字体可适当缩小: 24-28px

2. **媒体查询建议**
```
/* 平板 */
@media (max-width: 768px) {
  body { font-size: 15px; }
  h1 { font-size: 28px; }
}

/* 手机 */
@media (max-width: 480px) {
  body { font-size: 14px; }
  h1 { font-size: 24px; }
  p { line-height: 1.6; }
}
```

---

## 🎯 改进优先级

### 🔴 立即修复
- 标点符号规范化
- 删除重复文本或合并内容
- 修复任何可见的文本错误

### 🟡 重要优化
- 统一字体选择
- 优化行长度和间距
- 改进响应式文本设置

### 🟢 持续优化
- A/B 测试不同的字体
- 监测用户的可读性反馈
- 根据分析数据微调排版

---

## 📋 逐项检查清单

### 文本规范
- [ ] 所有标点符号使用规范
- [ ] 无重复或冗余内容
- [ ] 文本编码正确
- [ ] 无多余空格或制表符
- [ ] 拼写检查完成

### 排版设计
- [ ] 字体选择统一（≤3种）
- [ ] 字体大小层次清晰
- [ ] 行高设置合理（正文1.5-1.8）
- [ ] 段落间距一致
- [ ] 文本对齐规范

### 响应式设计
- [ ] 移动设备字体≥12px
- [ ] 平板设备显示正常
- [ ] 行长度适合各设备
- [ ] 没有文本溢出或截断
- [ ] 触摸设备上的可点击元素足够大

### 可访问性
- [ ] 字体对比度≥4.5:1
- [ ] 行高≥1.5
- [ ] 无孤立字或寡妇字
- [ ] 重要信息不仅依靠颜色表达

---

## 📸 测试截图

- 桌面版: /tmp/text_layout_desktop.png
- 移动版: /tmp/text_layout_mobile.png

---

**报告生成时间**: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """

**建议**: 根据以上检查清单逐项修复，确保网站的文本规范性和布局优化。
"""
        return report

def main():
    analyzer = TextLayoutAnalyzer('https://test.wingame.com/')
    analyzer.start()

    try:
        analyzer.analyze_page()

        # 生成报告
        report = analyzer.generate_report()

        # 保存报告
        with open('/tmp/text_layout_report.md', 'w', encoding='utf-8') as f:
            f.write(report)

        print("\n✓ 文本和布局报告已生成: /tmp/text_layout_report.md")

        # 保存详细数据
        with open('/tmp/text_layout_results.json', 'w', encoding='utf-8') as f:
            json.dump(analyzer.results, f, indent=2, ensure_ascii=False)

        print("✓ 详细结果已保存: /tmp/text_layout_results.json")
        print("\n" + "="*60)
        print(report)

    finally:
        analyzer.stop()

if __name__ == '__main__':
    main()
