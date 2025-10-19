# AIFI 智能财报系统 - 字段字典
# 基于财税票数据字典生成

# ============================================================================
# 一、企业基础信息字段（来源：企业基础信息表 - 宽表格式）
# ============================================================================
BASIC_INFO_FIELDS = {
    '纳税人识别号': 'taxpayer_id',
    '纳税人名称': 'taxpayer_name',
    '行业类别': 'industry_type',
    '行业代码': 'hydm',
    '注册日期': 'registered_date',
    '注册资本': 'register_capital',
    '注册资本币种': 'register_currencies',
    '登记注册类型': 'registered_type',
    '登记注册类型代码': 'registered_type_code',
    '开业日期': 'start_business_date',
    '登记省份': 'register_province',
    '登记城市': 'register_city',
    '登记区域': 'register_county',
}

# ============================================================================
# 二、财务报表字段（来源：企业财务报表 - 窄表格式）
# 说明：财务报表数据以project_name字段区分不同的会计科目
# ============================================================================

# 2.1 资产负债表关键字段
# 表名：企业资产负债表（年度）
# 关键列：initial_balance (年初数), ending_balance (期末数)
BALANCE_SHEET_FIELDS = {
    '项目名称': 'project_name',
    '项目代码': 'project_name_code',
    '年初数': 'initial_balance',
    '期末数': 'ending_balance',
    '资产负债类型': 'type',
    '所属时期起': 'begin_date',
    '所属时期止': 'end_date',
    '报表时期': 'period',
}

# 资产负债表需要提取的项目（通过project_name筛选）
BALANCE_SHEET_PROJECTS = {
    '总资产': '资产总计',
    '流动资产': '流动资产合计',
    '非流动资产': '非流动资产合计',
    '总负债': '负债合计',
    '流动负债': '流动负债合计',
    '非流动负债': '非流动负债合计',
    '所有者权益': '所有者权益合计',
    '应收账款': '应收账款',
    '存货': '存货',
}

# 2.2 利润表关键字段
# 表名：企业利润表（年度）
# 关键列：current_year_accumulative_amount (本年累计数), last_year_accumulative_amount (上年累计数)
PROFIT_STATEMENT_FIELDS = {
    '项目名称': 'project_name',
    '项目代码': 'project_name_code',
    '本年累计数': 'current_year_accumulative_amount',
    '上年累计数': 'last_year_accumulative_amount',
    '所属时期起': 'begin_date',
    '所属时期止': 'end_date',
    '报表时期': 'period',
}

# 利润表需要提取的项目（通过project_name筛选）
PROFIT_STATEMENT_PROJECTS = {
    '营业收入': '营业收入',
    '营业成本': '营业成本',
    '营业利润': '营业利润',
    '利润总额': '利润总额',
    '净利润': '净利润',
}

# 2.3 现金流量表关键字段
# 表名：企业现金流量表
# 关键列：bqje (本期金额), sqje (上期金额), bnljje (本年金额)
CASH_FLOW_FIELDS = {
    '项目名称': 'project_name',
    '项目代码': 'project_name_code',
    '本期金额': 'bqje',
    '上期金额': 'sqje',
    '本年金额': 'bnljje',
    '所属时期起': 'begin_date',
    '所属时期止': 'end_date',
    '报表时期': 'period',
}

# 现金流量表需要提取的项目（通过project_name筛选）
CASH_FLOW_PROJECTS = {
    '经营活动现金流量净额': '经营活动产生的现金流量净额',
    '投资活动现金流量净额': '投资活动产生的现金流量净额',
    '筹资活动现金流量净额': '筹资活动产生的现金流量净额',
    '现金及现金等价物净增加额': '现金及现金等价物净增加额',
}

# ============================================================================
# 三、公共字段（所有表共有）
# ============================================================================
COMMON_FIELDS = {
    '主键ID': 'id',
    '订单来源渠道': 'channel_source',
    '采集订单号': 'order_no',
    '授权批次号': 'tax_no',
    '数据创建时间': 'create_time',
    '纳税人识别号': 'taxpayer_id',
}

# ============================================================================
# 四、财务指标计算所需字段映射
# ============================================================================
FINANCIAL_METRICS = {
    # 盈利能力指标
    '净利润率': {
        'formula': '净利润 / 营业收入',
        'fields': ['净利润', '营业收入']
    },
    '毛利率': {
        'formula': '(营业收入 - 营业成本) / 营业收入',
        'fields': ['营业收入', '营业成本']
    },
    '净资产收益率': {
        'formula': '净利润 / 所有者权益',
        'fields': ['净利润', '所有者权益']
    },
    
    # 偿债能力指标
    '资产负债率': {
        'formula': '总负债 / 总资产',
        'fields': ['总负债', '总资产']
    },
    '流动比率': {
        'formula': '流动资产 / 流动负债',
        'fields': ['流动资产', '流动负债']
    },
    '速动比率': {
        'formula': '(流动资产 - 存货) / 流动负债',
        'fields': ['流动资产', '存货', '流动负债']
    },
    
    # 运营能力指标
    '应收账款周转率': {
        'formula': '营业收入 / 应收账款',
        'fields': ['营业收入', '应收账款']
    },
    '存货周转率': {
        'formula': '营业成本 / 存货',
        'fields': ['营业成本', '存货']
    },
    '总资产周转率': {
        'formula': '营业收入 / 总资产',
        'fields': ['营业收入', '总资产']
    },
    
    # 现金流指标
    '现金利润比': {
        'formula': '经营活动现金流量净额 / 净利润',
        'fields': ['经营活动现金流量净额', '净利润']
    },
}

# ============================================================================
# 五、数据表信息
# ============================================================================
TABLE_INFO = {
    '企业基础信息': {
        'table_name': 'syx_enterprise_info',
        'description': '企业工商登记信息',
        'format': '宽表',
        'key_field': 'taxpayer_id'
    },
    '企业资产负债表（年度）': {
        'table_name': 'syx_tax_finance_balance_year',
        'description': '企业年度资产负债表',
        'format': '窄表',
        'key_field': 'taxpayer_id',
        'project_field': 'project_name',
        'value_fields': ['initial_balance', 'ending_balance']
    },
    '企业利润表（年度）': {
        'table_name': 'syx_tax_finance_profit_year',
        'description': '企业年度利润表',
        'format': '窄表',
        'key_field': 'taxpayer_id',
        'project_field': 'project_name',
        'value_fields': ['current_year_accumulative_amount', 'last_year_accumulative_amount']
    },
    '企业现金流量表': {
        'table_name': 't_syx_cash_flow',
        'description': '企业现金流量表',
        'format': '窄表',
        'key_field': 'taxpayer_id',
        'project_field': 'project_name',
        'value_fields': ['bqje', 'sqje', 'bnljje']
    }
}

# ============================================================================
# 六、辅助函数
# ============================================================================

def get_all_required_fields():
    """获取项目所需的所有字段清单"""
    all_fields = {}
    
    all_fields['基础信息'] = BASIC_INFO_FIELDS
    all_fields['资产负债表'] = BALANCE_SHEET_FIELDS
    all_fields['利润表'] = PROFIT_STATEMENT_FIELDS
    all_fields['现金流量表'] = CASH_FLOW_FIELDS
    
    return all_fields

def get_financial_projects():
    """获取需要提取的所有财务项目"""
    return {
        '资产负债表项目': BALANCE_SHEET_PROJECTS,
        '利润表项目': PROFIT_STATEMENT_PROJECTS,
        '现金流量表项目': CASH_FLOW_PROJECTS
    }

if __name__ == "__main__":
    print("="*80)
    print("AIFI 智能财报系统 - 字段字典")
    print("="*80)
    
    print("\n1. 企业基础信息字段:")
    for cn, en in BASIC_INFO_FIELDS.items():
        print(f"  {cn:20s} -> {en}")
    
    print("\n2. 资产负债表需要提取的项目:")
    for cn, project in BALANCE_SHEET_PROJECTS.items():
        print(f"  {cn:20s} -> 筛选 project_name = '{project}'")
    
    print("\n3. 利润表需要提取的项目:")
    for cn, project in PROFIT_STATEMENT_PROJECTS.items():
        print(f"  {cn:20s} -> 筛选 project_name = '{project}'")
    
    print("\n4. 现金流量表需要提取的项目:")
    for cn, project in CASH_FLOW_PROJECTS.items():
        print(f"  {cn:20s} -> 筛选 project_name = '{project}'")
    
    print("\n5. 财务指标计算公式:")
    for metric, info in FINANCIAL_METRICS.items():
        print(f"  {metric}: {info['formula']}")
