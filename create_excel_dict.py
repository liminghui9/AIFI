import pandas as pd

# 导入字典
from field_dictionary import FIELD_DICTIONARY, FIELD_CATEGORIES, FIELD_TYPES

def create_excel_dictionary():
    # 1. 字段映射表
    field_mapping = []
    for chinese, english in FIELD_DICTIONARY.items():
        field_mapping.append({
            '中文字段名': chinese,
            '英文字段名': english,
            '数据类型': FIELD_TYPES.get(chinese, 'string')
        })
    
    df_mapping = pd.DataFrame(field_mapping)
    
    # 2. 字段分类表
    category_data = []
    category_names = {
        'basic_info': '基本信息',
        'balance_sheet_2023': '2023年资产负债表',
        'balance_sheet_2022': '2022年资产负债表', 
        'income_statement_2023': '2023年利润表',
        'income_statement_2022': '2022年利润表',
        'cash_flow_2023': '2023年现金流量表',
        'cash_flow_2022': '2022年现金流量表'
    }
    
    for category, fields in FIELD_CATEGORIES.items():
        for field in fields:
            category_data.append({
                '分类代码': category,
                '分类名称': category_names.get(category, category),
                '字段名': field,
                '英文名': FIELD_DICTIONARY.get(field, ''),
                '数据类型': FIELD_TYPES.get(field, 'string')
            })
    
    df_categories = pd.DataFrame(category_data)
    
    # 3. 分类统计表
    category_stats = []
    for category, fields in FIELD_CATEGORIES.items():
        category_stats.append({
            '分类代码': category,
            '分类名称': category_names.get(category, category),
            '字段数量': len(fields)
        })
    
    df_stats = pd.DataFrame(category_stats)
    
    # 写入Excel文件
    with pd.ExcelWriter('字段字典_新版.xlsx', engine='openpyxl') as writer:
        df_mapping.to_excel(writer, sheet_name='字段映射表', index=False)
        df_categories.to_excel(writer, sheet_name='字段分类表', index=False)
        df_stats.to_excel(writer, sheet_name='分类统计', index=False)
    
    print('Excel文件已创建: 字段字典.xlsx')
    print(f'- 字段映射表: {len(df_mapping)} 条记录')
    print(f'- 字段分类表: {len(df_categories)} 条记录')  
    print(f'- 分类统计表: {len(df_stats)} 条记录')

if __name__ == "__main__":
    create_excel_dictionary()