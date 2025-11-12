"""
简单测试HTML标签移除
"""
import re

def strip_html_tags(text):
    """移除HTML标签"""
    # 先将<br>转换为换行
    text = re.sub(r'<br\s*/?>', '\n', text)
    
    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 清理多余的空白和换行
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    
    return text.strip()

# 测试文本
test_text = """整体财务健康状况评级：<span class="risk-low">良好</span>

理由：测试企业003号的净利润率<span class="highlight-number">22.15%</span>，毛利率<span class="highlight-number">42.97%</span>，净资产收益率<span class="highlight-number">28.12%</span>，均高于行业平均水平，显示出<span class="risk-low">良好</span>的盈利能力。<br>尽管资产负债率<span class="highlight-number">54.81%</span>略高于行业平均水平，但流动比率1.83和速动比率1.47表明企业的短期偿债能力尚可。"""

print("=" * 80)
print("原始文本：")
print("=" * 80)
print(test_text)
print("\n")

result = strip_html_tags(test_text)

print("=" * 80)
print("处理后文本：")
print("=" * 80)
print(result)
print("\n")

if '<span' in result or '<br>' in result or '<strong>' in result:
    print("❌ 失败：仍然包含HTML标签")
else:
    print("✅ 成功：所有HTML标签已移除")
