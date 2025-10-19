from tax_dict_generator import TaxDictGenerator
import pandas as pd

# 初始化生成器
generator = TaxDictGenerator(r'C:\Users\21437\Downloads\财税票数据字典-20250417.xlsx')

print("="*80)
print("AIFI 智能财报系统 - 项目字段字典生成")
print("="*80)

# 根据需求文档，定义需要的字段
project_fields = {
    '企业基础信息': [
        'taxpayer_name',           # 纳税人名称（企业名称）
        'taxpayer_id',             # 纳税人识别号（统一社会信用代码）
        'industry',                 # 行业类别
        'registered_date',          # 注册日期（成立日期）
        'register_capital',         # 注册资本
    ],
    '企业资产负债表（年度）': [
        'total_assets',             # 总资产
        'current_assets',           # 流动资产
        'non_current_assets',       # 非流动资产
        'total_liabilities',        # 总负债
        'current_liabilities',      # 流动负债
        'non_current_liabilities',  # 非流动负债
        'owners_equity',            # 所有者权益
        'accounts_receivable',      # 应收账款（用于计算周转率）
        'inventory',                # 存货（用于计算周转率）
    ],
    '企业利润表（年度）': [
        'operating_revenue',        # 营业收入
        'operating_costs',          # 营业成本
        'operating_profit',         # 营业利润
        'total_profit',             # 利润总额
        'net_profit',               # 净利润
    ],
    '企业现金流量表': [
        'operating_cash_flow',      # 经营活动现金流量净额
        'investing_cash_flow',      # 投资活动现金流量净额
        'financing_cash_flow',      # 筹资活动现金流量净额
        'net_cash_increase',        # 现金及现金等价物净增加额
    ]
}

# 先搜索关键字段，确认它们的实际字段名
print("\n1. 搜索企业基础信息字段...")
print("-" * 80)
basic_keywords = ['纳税人名称', '纳税人识别号', '行业', '注册日期', '注册资本']
basic_results = generator.search_fields(basic_keywords)
print(basic_results[['表名', '字段名', '字段中文名']].to_string())

print("\n2. 搜索资产负债表字段...")
print("-" * 80)
balance_keywords = ['总资产', '流动资产', '非流动资产', '总负债', '流动负债', 
                   '非流动负债', '所有者权益', '应收账款', '存货']
balance_results = generator.search_fields(balance_keywords)
if len(balance_results) > 0:
    print(balance_results[['表名', '字段名', '字段中文名']].to_string())
else:
    print("未找到相关字段")

print("\n3. 搜索利润表字段...")
print("-" * 80)
profit_keywords = ['营业收入', '营业成本', '营业利润', '利润总额', '净利润']
profit_results = generator.search_fields(profit_keywords)
if len(profit_results) > 0:
    print(profit_results[['表名', '字段名', '字段中文名']].to_string())
else:
    print("未找到相关字段")

print("\n4. 搜索现金流量表字段...")
print("-" * 80)
cashflow_keywords = ['经营活动', '投资活动', '筹资活动', '现金净增加']
cashflow_results = generator.search_fields(cashflow_keywords)
if len(cashflow_results) > 0:
    print(cashflow_results[['表名', '字段名', '字段中文名']].to_string())
else:
    print("未找到相关字段")

print("\n" + "="*80)
print("请根据上述搜索结果，确认字段英文名后，我将生成最终的字段字典")
print("="*80)
