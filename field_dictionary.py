# Excel模板字段字典
FIELD_DICTIONARY = {
    # 基本信息字段
    '企业名称': 'company_name',
    '统一社会信用代码': 'social_credit_code',
    '注册资本（万元）': 'registered_capital',
    '成立日期': 'establishment_date',
    '行业类别': 'industry_category',
    '法定代表人': 'legal_representative',
    '法定代表人持股比例': 'legal_rep_shareholding',
    '注册地址': 'registered_address',
    '注册资本币种': 'registered_capital_currency',
    '登记状态': 'registration_status',
    '登记机关': 'registration_authority',
    '企业类型': 'company_type',
    '经营范围': 'business_scope',
    
    # 2023年资产负债表
    '总资产_2023': 'total_assets_2023',
    '流动资产_2023': 'current_assets_2023',
    '非流动资产_2023': 'non_current_assets_2023',
    '总负债_2023': 'total_liabilities_2023',
    '流动负债_2023': 'current_liabilities_2023',
    '非流动负债_2023': 'non_current_liabilities_2023',
    '所有者权益_2023': 'owners_equity_2023',
    
    # 2022年资产负债表
    '总资产_2022': 'total_assets_2022',
    '流动资产_2022': 'current_assets_2022',
    '非流动资产_2022': 'non_current_assets_2022',
    '总负债_2022': 'total_liabilities_2022',
    '流动负债_2022': 'current_liabilities_2022',
    '非流动负债_2022': 'non_current_liabilities_2022',
    '所有者权益_2022': 'owners_equity_2022',
    
    # 2023年利润表
    '营业收入_2023': 'operating_revenue_2023',
    '营业成本_2023': 'operating_costs_2023',
    '营业利润_2023': 'operating_profit_2023',
    '利润总额_2023': 'total_profit_2023',
    '净利润_2023': 'net_profit_2023',
    
    # 2022年利润表
    '营业收入_2022': 'operating_revenue_2022',
    '营业成本_2022': 'operating_costs_2022',
    '营业利润_2022': 'operating_profit_2022',
    '利润总额_2022': 'total_profit_2022',
    '净利润_2022': 'net_profit_2022',
    
    # 2023年现金流量表
    '经营活动现金流量净额_2023': 'operating_cash_flow_2023',
    '投资活动现金流量净额_2023': 'investing_cash_flow_2023',
    '筹资活动现金流量净额_2023': 'financing_cash_flow_2023',
    '现金及现金等价物净增加额_2023': 'net_cash_increase_2023',
    
    # 2022年现金流量表
    '经营活动现金流量净额_2022': 'operating_cash_flow_2022',
    '投资活动现金流量净额_2022': 'investing_cash_flow_2022',
    '筹资活动现金流量净额_2022': 'financing_cash_flow_2022',
    '现金及现金等价物净增加额_2022': 'net_cash_increase_2022'
}

# 字段分类字典
FIELD_CATEGORIES = {
    'basic_info': ['企业名称', '统一社会信用代码', '注册资本（万元）', '成立日期', '行业类别', '法定代表人',
                   '法定代表人持股比例', '注册地址', '注册资本币种', '登记状态', '登记机关', '企业类型', '经营范围'],
    
    'balance_sheet_2023': [
        '总资产_2023', '流动资产_2023', '非流动资产_2023',
        '总负债_2023', '流动负债_2023', '非流动负债_2023',
        '所有者权益_2023'
    ],
    
    'balance_sheet_2022': [
        '总资产_2022', '流动资产_2022', '非流动资产_2022',
        '总负债_2022', '流动负债_2022', '非流动负债_2022',
        '所有者权益_2022'
    ],
    
    'income_statement_2023': [
        '营业收入_2023', '营业成本_2023', '营业利润_2023',
        '利润总额_2023', '净利润_2023'
    ],
    
    'income_statement_2022': [
        '营业收入_2022', '营业成本_2022', '营业利润_2022',
        '利润总额_2022', '净利润_2022'
    ],
    
    'cash_flow_2023': [
        '经营活动现金流量净额_2023', '投资活动现金流量净额_2023',
        '筹资活动现金流量净额_2023', '现金及现金等价物净增加额_2023'
    ],
    
    'cash_flow_2022': [
        '经营活动现金流量净额_2022', '投资活动现金流量净额_2022',
        '筹资活动现金流量净额_2022', '现金及现金等价物净增加额_2022'
    ]
}

# 数据类型字典
FIELD_TYPES = {
    '企业名称': 'string',
    '统一社会信用代码': 'string',
    '注册资本（万元）': 'numeric',
    '成立日期': 'date',
    '行业类别': 'string',
    '法定代表人': 'string',
    '法定代表人持股比例': 'string',
    '注册地址': 'string',
    '注册资本币种': 'string',
    '登记状态': 'string',
    '登记机关': 'string',
    '企业类型': 'string',
    '经营范围': 'string'
}

# 为所有财务字段添加numeric类型
for field in FIELD_DICTIONARY.keys():
    if field not in FIELD_TYPES:
        FIELD_TYPES[field] = 'numeric'

# 使用示例
def get_english_field_name(chinese_field):
    """获取中文字段对应的英文字段名"""
    return FIELD_DICTIONARY.get(chinese_field, chinese_field)

def get_fields_by_category(category):
    """根据分类获取字段列表"""
    return FIELD_CATEGORIES.get(category, [])

def get_field_type(field):
    """获取字段数据类型"""
    return FIELD_TYPES.get(field, 'string')

if __name__ == "__main__":
    print("字段字典已创建")
    print(f"总字段数: {len(FIELD_DICTIONARY)}")
    print(f"基本信息字段: {FIELD_CATEGORIES['basic_info']}")