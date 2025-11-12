"""修复已存在报告的HTML标签问题"""
import json
import os
import re

def strip_html_tags(text):
    """移除HTML标签"""
    if not text:
        return text
    
    # 将<br>转换为换行
    text = re.sub(r'<br\s*/?>', '\n', text)
    
    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 清理多余的空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def fix_reports():
    """修复所有报告"""
    storage_file = 'data/reports_storage.json'
    
    if not os.path.exists(storage_file):
        print("未找到报告文件")
        return
    
    with open(storage_file, 'r', encoding='utf-8') as f:
        reports = json.load(f)
    
    print(f"找到 {len(reports)} 个报告，开始修复...")
    
    for report_id, report in reports.items():
        # 添加PDF版本的dimension_analyses
        if 'dimension_analyses' in report and 'dimension_analyses_pdf' not in report:
            report['dimension_analyses_pdf'] = {}
            for dimension, analysis in report['dimension_analyses'].items():
                report['dimension_analyses_pdf'][dimension] = strip_html_tags(analysis)
            print(f"✓ 修复报告 {report_id} 的dimension_analyses")
        
        # 添加PDF版本的overall_assessment
        if 'overall_assessment' in report and 'overall_assessment_pdf' not in report:
            report['overall_assessment_pdf'] = strip_html_tags(report['overall_assessment'])
            print(f"✓ 修复报告 {report_id} 的overall_assessment")
    
    # 保存
    with open(storage_file, 'w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    
    print(f"\n修复完成！已处理 {len(reports)} 个报告")
    print("现在可以重新导出PDF了")

if __name__ == '__main__':
    fix_reports()



