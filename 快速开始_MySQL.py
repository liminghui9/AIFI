"""
AIFI财报系统 - 财税票MySQL数据快速导出
基于实际的建表语句编写，可直接使用

使用方法：
1. 修改下面的数据库配置
2. 运行: python 快速开始_MySQL.py <纳税人识别号>
"""

import mysql.connector
import pandas as pd
import sys
from datetime import datetime
import os

# ============================================================================
# 数据库配置 - 请修改为您的实际配置
# ============================================================================
DB_CONFIG = {
    'host': 'localhost',      # MySQL主机地址
    'port': 3306,             # MySQL端口
    'user': 'root',           # 数据库用户名
    'password': '123456',     # 数据库密码
    'database': 'bill_tax_fusion_dwd_standrad',  # 数据库名称（从建表语句中看到的）
}

# ============================================================================
# 字段映射配置
# ============================================================================

# 资产负债表项目映射
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

# 利润表项目映射
PROFIT_PROJECTS = {
    '营业收入': '营业收入',
    '营业成本': '营业成本',
    '营业利润': '营业利润',
    '利润总额': '利润总额',
    '净利润': '净利润',
}

# 现金流量表项目映射
CASHFLOW_PROJECTS = {
    '经营活动现金流量净额': '经营活动产生的现金流量净额',
    '投资活动现金流量净额': '投资活动产生的现金流量净额',
    '筹资活动现金流量净额': '筹资活动产生的现金流量净额',
    '现金及现金等价物净增加额': '现金及现金等价物净增加额',
}


def test_connection(config):
    """测试数据库连接"""
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✓ 数据库连接成功！MySQL版本: {version}")
        cursor.close()
        return conn
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return None


def get_basic_info(conn, taxpayer_id):
    """获取企业基本信息"""
    cursor = conn.cursor(dictionary=True)
    
    sql = """
    SELECT 
        taxpayer_name AS '企业名称',
        taxpayer_id AS '统一社会信用代码',
        register_capital AS '注册资本（万元）',
        COALESCE(registered_date, start_business_date) AS '成立日期',
        industry_type AS '行业类别',
        legal_person_name AS '法定代表人',
        -- 额外信息
        hydm AS '行业代码',
        register_province AS '登记省份',
        register_city AS '登记城市',
        employees_number AS '从业人数'
    FROM syx_enterprise_info
    WHERE taxpayer_id = %s
    LIMIT 1
    """
    
    cursor.execute(sql, (taxpayer_id,))
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        return None
    
    # 处理注册资本（已经是万元）
    if result.get('注册资本（万元）'):
        result['注册资本（万元）'] = float(result['注册资本（万元）'])
    
    # 处理日期格式
    if result.get('成立日期'):
        result['成立日期'] = result['成立日期'].strftime('%Y-%m-%d')
    
    # 处理None值
    for key in result:
        if result[key] is None:
            result[key] = "【数据缺失】"
    
    return result


def get_balance_sheet(conn, taxpayer_id, year):
    """获取资产负债表数据"""
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        project_name,
        ending_balance
    FROM syx_tax_finance_balance_year
    WHERE taxpayer_id = %s
      AND YEAR(end_date) = %s
      AND (invalid_mark IS NULL OR invalid_mark = '')
    ORDER BY sequence
    """
    
    cursor.execute(sql, (taxpayer_id, year))
    results = cursor.fetchall()
    cursor.close()
    
    data = {}
    for project_name, value in results:
        # 查找标准名称
        for std_name, tax_name in BALANCE_SHEET_PROJECTS.items():
            if project_name == tax_name:
                data[f"{std_name}_{year}"] = float(value) if value else None
                break
    
    return data


def get_profit_statement(conn, taxpayer_id, year):
    """获取利润表数据"""
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        project_name,
        current_year_accumulative_amount
    FROM syx_tax_finance_profit_year
    WHERE taxpayer_id = %s
      AND YEAR(end_date) = %s
      AND (invalid_mark IS NULL OR invalid_mark = '')
    ORDER BY sequence
    """
    
    cursor.execute(sql, (taxpayer_id, year))
    results = cursor.fetchall()
    cursor.close()
    
    data = {}
    for project_name, value in results:
        for std_name, tax_name in PROFIT_PROJECTS.items():
            if project_name == tax_name:
                data[f"{std_name}_{year}"] = float(value) if value else None
                break
    
    return data


def get_cashflow_statement(conn, taxpayer_id, year):
    """获取现金流量表数据"""
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        project_name,
        bnljje
    FROM syx_cash_flow
    WHERE taxpayer_id = %s
      AND YEAR(end_date) = %s
      AND (invalid_mark IS NULL OR invalid_mark = '')
    ORDER BY sequence
    """
    
    cursor.execute(sql, (taxpayer_id, year))
    results = cursor.fetchall()
    cursor.close()
    
    data = {}
    for project_name, value in results:
        for std_name, tax_name in CASHFLOW_PROJECTS.items():
            if project_name == tax_name:
                data[f"{std_name}_{year}"] = float(value) if value else None
                break
    
    return data


def export_to_excel(taxpayer_id, years=[2023, 2022]):
    """导出企业数据到Excel"""
    
    print("=" * 80)
    print("AIFI财报系统 - 财税票数据导出工具")
    print("=" * 80)
    
    # 连接数据库
    print(f"\n1. 连接数据库...")
    conn = test_connection(DB_CONFIG)
    if not conn:
        return False
    
    # 获取企业基本信息
    print(f"\n2. 读取企业基本信息...")
    basic_info = get_basic_info(conn, taxpayer_id)
    if not basic_info:
        print(f"✗ 未找到纳税人识别号为 {taxpayer_id} 的企业")
        conn.close()
        return False
    
    company_name = basic_info.get('企业名称', '未知企业')
    print(f"✓ 找到企业: {company_name}")
    
    # 组装数据
    row_data = basic_info.copy()
    
    # 获取财务数据
    print(f"\n3. 读取财务数据...")
    for year in years:
        print(f"  - {year}年数据...")
        
        # 资产负债表
        balance_data = get_balance_sheet(conn, taxpayer_id, year)
        row_data.update(balance_data)
        print(f"    ✓ 资产负债表: {len(balance_data)} 个科目")
        
        # 利润表
        profit_data = get_profit_statement(conn, taxpayer_id, year)
        row_data.update(profit_data)
        print(f"    ✓ 利润表: {len(profit_data)} 个科目")
        
        # 现金流量表
        cashflow_data = get_cashflow_statement(conn, taxpayer_id, year)
        row_data.update(cashflow_data)
        print(f"    ✓ 现金流量表: {len(cashflow_data)} 个科目")
    
    # 创建DataFrame
    df = pd.DataFrame([row_data])
    
    # 导出Excel
    output_dir = 'uploads'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = f"{output_dir}/{taxpayer_id}_财务数据.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"\n4. 导出完成！")
    print("=" * 80)
    print(f"✓ 文件位置: {output_file}")
    print(f"✓ 企业名称: {company_name}")
    print(f"✓ 数据年份: {', '.join(map(str, years))}")
    print(f"✓ 字段数量: {len(row_data)}")
    print("=" * 80)
    
    print(f"\n下一步:")
    print(f"1. 启动AIFI系统: python app.py")
    print(f"2. 访问: http://localhost:5000")
    print(f"3. 上传文件: {output_file}")
    print(f"4. 查看财务分析报告")
    
    conn.close()
    return True


def find_companies(limit=10):
    """查找可用的企业"""
    print("=" * 80)
    print("查找可用企业")
    print("=" * 80)
    
    conn = test_connection(DB_CONFIG)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 查找有财务数据的企业
    sql = """
    SELECT DISTINCT 
        e.taxpayer_id,
        e.taxpayer_name,
        e.industry_type,
        COUNT(DISTINCT YEAR(b.end_date)) as years_count
    FROM syx_enterprise_info e
    INNER JOIN syx_tax_finance_balance_year b ON e.taxpayer_id = b.taxpayer_id
    WHERE b.invalid_mark IS NULL OR b.invalid_mark = ''
    GROUP BY e.taxpayer_id, e.taxpayer_name, e.industry_type
    HAVING years_count >= 2
    LIMIT %s
    """
    
    cursor.execute(sql, (limit,))
    results = cursor.fetchall()
    
    if not results:
        print("✗ 未找到有完整财务数据的企业")
        conn.close()
        return
    
    print(f"\n找到 {len(results)} 个有完整财务数据的企业:\n")
    print(f"{'序号':<6}{'纳税人识别号':<22}{'企业名称':<35}{'行业':<20}{'年份数':<10}")
    print("-" * 100)
    
    for i, (tid, name, industry, years) in enumerate(results, 1):
        industry_str = industry or '未知'
        print(f"{i:<6}{tid:<22}{name:<35}{industry_str:<20}{years:<10}")
    
    print("\n使用方法:")
    print(f"  python {sys.argv[0]} <纳税人识别号>")
    print(f"\n示例:")
    if results:
        print(f"  python {sys.argv[0]} {results[0][0]}")
    
    conn.close()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
使用方法:
    python 快速开始_MySQL.py <纳税人识别号>         # 导出指定企业
    python 快速开始_MySQL.py --find              # 查找可用企业
    
示例:
    python 快速开始_MySQL.py 91110000000000000X
    python 快速开始_MySQL.py --find
        """)
        return
    
    if sys.argv[1] == '--find':
        find_companies()
    else:
        taxpayer_id = sys.argv[1]
        export_to_excel(taxpayer_id)


if __name__ == '__main__':
    main()

