"""
财税票数据适配器
负责将财税票数据库的窄表格式转换为AIFI项目所需的宽表格式
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class TaxDataAdapter:
    """财税票数据适配器"""
    
    # 资产负债表项目名称映射
    BALANCE_SHEET_MAPPING = {
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
    
    # 利润表项目名称映射
    PROFIT_MAPPING = {
        '营业收入': '营业收入',
        '营业成本': '营业成本',
        '营业利润': '营业利润',
        '利润总额': '利润总额',
        '净利润': '净利润',
    }
    
    # 现金流量表项目名称映射
    CASHFLOW_MAPPING = {
        '经营活动现金流量净额': '经营活动产生的现金流量净额',
        '投资活动现金流量净额': '投资活动产生的现金流量净额',
        '筹资活动现金流量净额': '筹资活动产生的现金流量净额',
        '现金及现金等价物净增加额': '现金及现金等价物净增加额',
    }
    
    def __init__(self, db_connection=None):
        """
        初始化适配器
        
        Args:
            db_connection: 数据库连接对象（如果使用数据库）
        """
        self.db_connection = db_connection
    
    def load_from_database(self, taxpayer_id: str, years: List[int] = None) -> Dict:
        """
        从数据库加载企业数据
        
        Args:
            taxpayer_id: 纳税人识别号
            years: 年份列表，默认为最近两年
            
        Returns:
            Dict: 标准格式的企业数据
        """
        if years is None:
            current_year = datetime.now().year
            years = [current_year - 1, current_year - 2]  # 默认最近两年
        
        try:
            # 1. 加载基本信息
            basic_info = self._load_basic_info(taxpayer_id)
            
            # 2. 加载财务数据
            financial_data = {}
            for year in years:
                financial_data[year] = {
                    '资产负债表': self._load_balance_sheet(taxpayer_id, year),
                    '利润表': self._load_profit_statement(taxpayer_id, year),
                    '现金流量表': self._load_cashflow_statement(taxpayer_id, year)
                }
            
            return {
                'basic_info': basic_info,
                'financial_data': financial_data,
                'years': sorted(years, reverse=True)
            }
            
        except Exception as e:
            raise Exception(f"从数据库加载数据失败: {str(e)}")
    
    def _load_basic_info(self, taxpayer_id: str) -> Dict[str, any]:
        """
        加载企业基础信息
        
        Args:
            taxpayer_id: 纳税人识别号
            
        Returns:
            Dict: 企业基本信息
        """
        if self.db_connection is None:
            raise Exception("未配置数据库连接")
        
        # SQL查询
        sql = """
        SELECT 
            taxpayer_name AS 企业名称,
            taxpayer_id AS 统一社会信用代码,
            register_capital AS 注册资本,
            COALESCE(registered_date, start_business_date) AS 成立日期,
            industry_type AS 行业类别,
            legal_person_name AS 法定代表人,
            -- 额外字段
            hydm AS 行业代码,
            register_province AS 登记省份,
            register_city AS 登记城市,
            register_county AS 登记区域,
            employees_number AS 从业人数,
            taxpayer_type AS 纳税人资格类型,
            business_scope AS 经营范围
        FROM syx_enterprise_info
        WHERE taxpayer_id = %s
        LIMIT 1
        """
        
        cursor = self.db_connection.cursor(dictionary=True)
        cursor.execute(sql, (taxpayer_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result is None:
            raise Exception(f"未找到纳税人识别号为 {taxpayer_id} 的企业信息")
        
        # 处理注册资本单位（转换为万元）
        if result.get('注册资本'):
            result['注册资本（万元）'] = float(result['注册资本'])
            del result['注册资本']
        
        # 处理日期格式
        if result.get('成立日期'):
            result['成立日期'] = result['成立日期'].strftime('%Y-%m-%d')
        
        # 处理None值
        for key, value in result.items():
            if value is None:
                result[key] = "【数据缺失】"
        
        return result
    
    def _load_balance_sheet(self, taxpayer_id: str, year: int) -> Dict[str, float]:
        """
        加载资产负债表数据
        
        Args:
            taxpayer_id: 纳税人识别号
            year: 年份
            
        Returns:
            Dict: 资产负债表数据
        """
        if self.db_connection is None:
            raise Exception("未配置数据库连接")
        
        # SQL查询：获取指定年度的资产负债表数据
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
        
        cursor = self.db_connection.cursor()
        cursor.execute(sql, (taxpayer_id, year))
        results = cursor.fetchall()
        cursor.close()
        
        # 转换为字典
        data = {}
        reverse_mapping = {v: k for k, v in self.BALANCE_SHEET_MAPPING.items()}
        
        for row in results:
            project_name, value = row
            # 查找映射
            standard_name = reverse_mapping.get(project_name)
            if standard_name:
                data[standard_name] = float(value) if value is not None else None
        
        # 确保所有必需字段都存在
        for standard_name in self.BALANCE_SHEET_MAPPING.keys():
            if standard_name not in data:
                data[standard_name] = None
        
        return data
    
    def _load_profit_statement(self, taxpayer_id: str, year: int) -> Dict[str, float]:
        """
        加载利润表数据
        
        Args:
            taxpayer_id: 纳税人识别号
            year: 年份
            
        Returns:
            Dict: 利润表数据
        """
        if self.db_connection is None:
            raise Exception("未配置数据库连接")
        
        # SQL查询
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
        
        cursor = self.db_connection.cursor()
        cursor.execute(sql, (taxpayer_id, year))
        results = cursor.fetchall()
        cursor.close()
        
        # 转换为字典
        data = {}
        reverse_mapping = {v: k for k, v in self.PROFIT_MAPPING.items()}
        
        for row in results:
            project_name, value = row
            standard_name = reverse_mapping.get(project_name)
            if standard_name:
                data[standard_name] = float(value) if value is not None else None
        
        # 确保所有必需字段都存在
        for standard_name in self.PROFIT_MAPPING.keys():
            if standard_name not in data:
                data[standard_name] = None
        
        return data
    
    def _load_cashflow_statement(self, taxpayer_id: str, year: int) -> Dict[str, float]:
        """
        加载现金流量表数据
        
        Args:
            taxpayer_id: 纳税人识别号
            year: 年份
            
        Returns:
            Dict: 现金流量表数据
        """
        if self.db_connection is None:
            raise Exception("未配置数据库连接")
        
        # SQL查询
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
        
        cursor = self.db_connection.cursor()
        cursor.execute(sql, (taxpayer_id, year))
        results = cursor.fetchall()
        cursor.close()
        
        # 转换为字典
        data = {}
        reverse_mapping = {v: k for k, v in self.CASHFLOW_MAPPING.items()}
        
        for row in results:
            project_name, value = row
            standard_name = reverse_mapping.get(project_name)
            if standard_name:
                data[standard_name] = float(value) if value is not None else None
        
        # 确保所有必需字段都存在
        for standard_name in self.CASHFLOW_MAPPING.keys():
            if standard_name not in data:
                data[standard_name] = None
        
        return data
    
    def export_to_excel_template(self, taxpayer_id: str, output_path: str, years: List[int] = None):
        """
        将数据库数据导出为AIFI项目所需的Excel模板格式
        
        Args:
            taxpayer_id: 纳税人识别号
            output_path: 输出文件路径
            years: 年份列表
        """
        # 加载数据
        data = self.load_from_database(taxpayer_id, years)
        
        # 构建DataFrame
        row_data = {}
        
        # 基本信息
        for key, value in data['basic_info'].items():
            row_data[key] = value
        
        # 财务数据
        for year in data['years']:
            year_data = data['financial_data'].get(year, {})
            
            # 资产负债表
            for field, value in year_data.get('资产负债表', {}).items():
                row_data[f"{field}_{year}"] = value
            
            # 利润表
            for field, value in year_data.get('利润表', {}).items():
                row_data[f"{field}_{year}"] = value
            
            # 现金流量表
            for field, value in year_data.get('现金流量表', {}).items():
                row_data[f"{field}_{year}"] = value
        
        # 创建DataFrame
        df = pd.DataFrame([row_data])
        
        # 导出Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"✓ 数据已导出到: {output_path}")
    
    def create_database_view(self):
        """
        在数据库中创建宽表视图（可选）
        
        这个方法会在数据库中创建视图，将窄表转换为宽表格式
        """
        if self.db_connection is None:
            raise Exception("未配置数据库连接")
        
        # 资产负债表视图
        balance_view_sql = """
        CREATE OR REPLACE VIEW v_balance_sheet_wide AS
        SELECT 
            taxpayer_id,
            YEAR(end_date) AS year,
            period,
            MAX(CASE WHEN project_name = '资产总计' THEN ending_balance END) AS total_assets,
            MAX(CASE WHEN project_name = '流动资产合计' THEN ending_balance END) AS current_assets,
            MAX(CASE WHEN project_name = '非流动资产合计' THEN ending_balance END) AS non_current_assets,
            MAX(CASE WHEN project_name = '负债合计' THEN ending_balance END) AS total_liabilities,
            MAX(CASE WHEN project_name = '流动负债合计' THEN ending_balance END) AS current_liabilities,
            MAX(CASE WHEN project_name = '非流动负债合计' THEN ending_balance END) AS non_current_liabilities,
            MAX(CASE WHEN project_name = '所有者权益合计' THEN ending_balance END) AS owners_equity,
            MAX(CASE WHEN project_name = '应收账款' THEN ending_balance END) AS accounts_receivable,
            MAX(CASE WHEN project_name = '存货' THEN ending_balance END) AS inventory
        FROM syx_tax_finance_balance_year
        WHERE invalid_mark IS NULL OR invalid_mark = ''
        GROUP BY taxpayer_id, YEAR(end_date), period
        """
        
        # 利润表视图
        profit_view_sql = """
        CREATE OR REPLACE VIEW v_profit_statement_wide AS
        SELECT 
            taxpayer_id,
            YEAR(end_date) AS year,
            period,
            MAX(CASE WHEN project_name = '营业收入' THEN current_year_accumulative_amount END) AS operating_revenue,
            MAX(CASE WHEN project_name = '营业成本' THEN current_year_accumulative_amount END) AS operating_costs,
            MAX(CASE WHEN project_name = '营业利润' THEN current_year_accumulative_amount END) AS operating_profit,
            MAX(CASE WHEN project_name = '利润总额' THEN current_year_accumulative_amount END) AS total_profit,
            MAX(CASE WHEN project_name = '净利润' THEN current_year_accumulative_amount END) AS net_profit
        FROM syx_tax_finance_profit_year
        WHERE invalid_mark IS NULL OR invalid_mark = ''
        GROUP BY taxpayer_id, YEAR(end_date), period
        """
        
        # 现金流量表视图
        cashflow_view_sql = """
        CREATE OR REPLACE VIEW v_cashflow_statement_wide AS
        SELECT 
            taxpayer_id,
            YEAR(end_date) AS year,
            period,
            MAX(CASE WHEN project_name = '经营活动产生的现金流量净额' THEN bnljje END) AS operating_cashflow,
            MAX(CASE WHEN project_name = '投资活动产生的现金流量净额' THEN bnljje END) AS investing_cashflow,
            MAX(CASE WHEN project_name = '筹资活动产生的现金流量净额' THEN bnljje END) AS financing_cashflow,
            MAX(CASE WHEN project_name = '现金及现金等价物净增加额' THEN bnljje END) AS net_cash_increase
        FROM syx_cash_flow
        WHERE invalid_mark IS NULL OR invalid_mark = ''
        GROUP BY taxpayer_id, YEAR(end_date), period
        """
        
        cursor = self.db_connection.cursor()
        try:
            cursor.execute(balance_view_sql)
            print("✓ 资产负债表视图创建成功")
            
            cursor.execute(profit_view_sql)
            print("✓ 利润表视图创建成功")
            
            cursor.execute(cashflow_view_sql)
            print("✓ 现金流量表视图创建成功")
            
            self.db_connection.commit()
        except Exception as e:
            self.db_connection.rollback()
            raise Exception(f"创建视图失败: {str(e)}")
        finally:
            cursor.close()


# 使用示例
if __name__ == "__main__":
    """
    使用示例
    """
    # 方式1: 连接数据库并导出Excel
    try:
        import mysql.connector
        
        # 配置数据库连接
        db_config = {
            'host': 'localhost',
            'user': 'your_username',
            'password': 'your_password',
            'database': 'your_database'
        }
        
        # 创建连接
        connection = mysql.connector.connect(**db_config)
        
        # 创建适配器
        adapter = TaxDataAdapter(db_connection=connection)
        
        # 导出企业数据
        taxpayer_id = '91XXXXXXXXXXXXXXXX'
        adapter.export_to_excel_template(
            taxpayer_id=taxpayer_id,
            output_path=f'exports/{taxpayer_id}_财务数据.xlsx',
            years=[2023, 2022]
        )
        
        # 关闭连接
        connection.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")
    
    # 方式2: 创建数据库视图
    # adapter.create_database_view()




