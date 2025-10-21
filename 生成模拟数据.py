"""
生成模拟企业财务数据
用于测试AIFI财报分析系统
"""

import mysql.connector
from datetime import datetime
import random
import hashlib

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'jinrongai',
}

# 行业类别
INDUSTRIES = [
    '软件和信息技术服务业',
    '互联网和相关服务',
    '制造业',
    '批发和零售业',
    '建筑业',
    '房地产业',
    '租赁和商务服务业',
    '科学研究和技术服务业',
    '交通运输、仓储和邮政业',
    '住宿和餐饮业',
    '文化、体育和娱乐业',
    '电子商务',
    '金融服务',
    '教育培训',
    '医疗健康'
]

# 企业类型
COMPANY_TYPES = [
    '有限责任公司',
    '股份有限公司',
    '个人独资企业',
    '合伙企业',
    '其他有限责任公司'
]

# 省份
PROVINCES = [
    '北京', '上海', '广东', '浙江', '江苏',
    '四川', '湖北', '湖南', '河南', '山东',
    '陕西', '重庆', '天津', '福建', '安徽'
]

def generate_hash(text):
    """生成MD5哈希"""
    return hashlib.md5(text.encode()).hexdigest()

def generate_test_companies(count=20):
    """生成测试企业数据"""
    print("=" * 80)
    print(f"生成 {count} 个测试企业数据")
    print("=" * 80)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        success_count = 0
        
        for i in range(1, count + 1):
            try:
                # 生成企业基本信息
                company_num = f"{i:03d}"
                taxpayer_id = generate_hash(f"TEST_COMPANY_{company_num}")
                industry = random.choice(INDUSTRIES)
                company_type = random.choice(COMPANY_TYPES)
                province = random.choice(PROVINCES)
                
                # 注册资本（100万-5000万）
                register_capital = random.randint(100, 5000) * 10000
                
                # 注册日期（2010-2020年间）
                year = random.randint(2010, 2020)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                registered_date = f"{year}-{month:02d}-{day:02d}"
                
                print(f"\n{i}. 生成企业: {industry} ({company_num})")
                
                # 插入企业信息
                sql_enterprise = """
                INSERT INTO syx_enterprise_info 
                (taxpayer_id, taxpayer_name, industry_type, registered_type, 
                 register_capital, registered_date, start_business_date,
                 register_currencies, taxpayer_type, nsrztmc, bureau, 
                 register_province, create_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE industry_type = VALUES(industry_type)
                """
                
                cursor.execute(sql_enterprise, (
                    taxpayer_id,
                    generate_hash(f"{industry}_{company_num}"),
                    industry,
                    company_type,
                    register_capital / 10000,  # 转换为万元
                    registered_date,
                    registered_date,
                    '人民币',
                    '增值税一般纳税人',
                    '正常',
                    f'{province}税务局',
                    province
                ))
                
                # 为每个企业生成2-4年的财务数据
                years_count = random.randint(2, 4)
                years = list(range(2024 - years_count, 2024))
                
                print(f"   生成 {years_count} 年财务数据: {years}")
                
                for year in years:
                    # 基础规模（随机）
                    base_scale = random.uniform(0.5, 2.0)
                    year_growth = (year - years[0]) * 0.15 + 1  # 年增长15%
                    scale = base_scale * year_growth
                    
                    # 生成资产负债表
                    generate_balance_sheet(cursor, taxpayer_id, year, scale)
                    
                    # 生成利润表
                    generate_profit_statement(cursor, taxpayer_id, year, scale)
                    
                    # 生成现金流量表
                    generate_cashflow_statement(cursor, taxpayer_id, year, scale)
                
                conn.commit()
                success_count += 1
                print(f"   ✓ 成功")
                
            except Exception as e:
                print(f"   ✗ 失败: {e}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print(f"完成！成功生成 {success_count}/{count} 个企业数据")
        print("=" * 80)
        print("\n现在可以刷新浏览器查看新增的企业了！")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


def generate_balance_sheet(cursor, taxpayer_id, year, scale=1.0):
    """生成资产负债表数据"""
    end_date = f'{year}-12-31'
    
    # 生成合理的财务数据（带随机波动）
    total_assets = random.randint(5000000, 50000000) * scale
    
    # 资产项
    current_assets = total_assets * random.uniform(0.5, 0.7)
    non_current_assets = total_assets - current_assets
    receivables = current_assets * random.uniform(0.2, 0.4)
    inventory = current_assets * random.uniform(0.15, 0.35)
    
    # 负债项
    total_liabilities = total_assets * random.uniform(0.4, 0.7)
    current_liabilities = total_liabilities * random.uniform(0.6, 0.8)
    non_current_liabilities = total_liabilities - current_liabilities
    
    # 权益
    equity = total_assets - total_liabilities
    
    balance_sheet = [
        ('资产总计', total_assets),
        ('流动资产合计', current_assets),
        ('非流动资产合计', non_current_assets),
        ('负债合计', total_liabilities),
        ('流动负债合计', current_liabilities),
        ('非流动负债合计', non_current_liabilities),
        ('所有者权益合计', equity),
        ('应收账款', receivables),
        ('存货', inventory),
    ]
    
    for idx, (project_name, value) in enumerate(balance_sheet, 1):
        sql = """
        INSERT INTO syx_tax_finance_balance_year
        (taxpayer_id, end_date, project_name, ending_balance, sequence, create_time, invalid_mark)
        VALUES (%s, %s, %s, %s, %s, NOW(), '未作废')
        ON DUPLICATE KEY UPDATE ending_balance = VALUES(ending_balance)
        """
        cursor.execute(sql, (taxpayer_id, end_date, project_name, value, idx))


def generate_profit_statement(cursor, taxpayer_id, year, scale=1.0):
    """生成利润表数据"""
    end_date = f'{year}-12-31'
    
    # 生成合理的利润数据
    revenue = random.randint(8000000, 80000000) * scale
    cost = revenue * random.uniform(0.55, 0.75)
    operating_profit = revenue - cost - revenue * random.uniform(0.05, 0.15)
    total_profit = operating_profit * random.uniform(0.9, 1.1)
    net_profit = total_profit * random.uniform(0.75, 0.95)
    
    profit_statement = [
        ('营业收入', revenue),
        ('营业成本', cost),
        ('营业利润', operating_profit),
        ('利润总额', total_profit),
        ('净利润', net_profit),
    ]
    
    for idx, (project_name, value) in enumerate(profit_statement, 1):
        sql = """
        INSERT INTO syx_tax_finance_profit_year
        (taxpayer_id, end_date, project_name, current_year_accumulative_amount, sequence, create_time, invalid_mark)
        VALUES (%s, %s, %s, %s, %s, NOW(), '未作废')
        ON DUPLICATE KEY UPDATE current_year_accumulative_amount = VALUES(current_year_accumulative_amount)
        """
        cursor.execute(sql, (taxpayer_id, end_date, project_name, value, idx))


def generate_cashflow_statement(cursor, taxpayer_id, year, scale=1.0):
    """生成现金流量表数据"""
    end_date = f'{year}-12-31'
    
    # 生成合理的现金流数据
    operating_cf = random.randint(1000000, 15000000) * scale * random.choice([1, -1])
    investing_cf = random.randint(-5000000, -500000) * scale
    financing_cf = random.randint(-2000000, 5000000) * scale
    net_increase = operating_cf + investing_cf + financing_cf
    
    cashflow_statement = [
        ('经营活动产生的现金流量净额', operating_cf),
        ('投资活动产生的现金流量净额', investing_cf),
        ('筹资活动产生的现金流量净额', financing_cf),
        ('现金及现金等价物净增加额', net_increase),
    ]
    
    for idx, (project_name, value) in enumerate(cashflow_statement, 1):
        sql = """
        INSERT INTO syx_cash_flow
        (taxpayer_id, end_date, project_name, bnljje, sequence, create_time, invalid_mark)
        VALUES (%s, %s, %s, %s, %s, NOW(), '未作废')
        ON DUPLICATE KEY UPDATE bnljje = VALUES(bnljje)
        """
        cursor.execute(sql, (taxpayer_id, end_date, project_name, value, idx))


if __name__ == '__main__':
    print("\n请选择要生成的企业数量:")
    print("1. 10个企业")
    print("2. 20个企业（推荐）")
    print("3. 50个企业")
    print("4. 自定义数量")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    count_map = {
        '1': 10,
        '2': 20,
        '3': 50
    }
    
    if choice in count_map:
        count = count_map[choice]
    elif choice == '4':
        count = int(input("请输入企业数量: "))
    else:
        print("无效选项，使用默认值20")
        count = 20
    
    generate_test_companies(count)



