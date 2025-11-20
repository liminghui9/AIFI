"""
数据处理模块
负责Excel数据的读取、解析和验证
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional

class DataProcessor:
    """财务数据处理器"""
    
    # 定义必需的基本信息字段
    BASIC_INFO_FIELDS = [
        '企业名称',
        '统一社会信用代码',
        '注册资本（万元）',
        '成立日期',
        '行业类别',
        '法定代表人',
        '法定代表人持股比例',
        '注册地址',
        '注册资本币种',
        '登记状态',
        '登记机关',
        '企业类型',
        '经营范围'
    ]
    
    # 定义财务报表字段（需要两年数据）
    FINANCIAL_FIELDS = {
        '资产负债表': [
            '总资产', '流动资产', '非流动资产',
            '总负债', '流动负债', '非流动负债',
            '所有者权益'
        ],
        '利润表': [
            '营业收入', '营业成本', '营业利润',
            '利润总额', '净利润'
        ],
        '现金流量表': [
            '经营活动现金流量净额',
            '投资活动现金流量净额',
            '筹资活动现金流量净额',
            '现金及现金等价物净增加额'
        ]
    }
    
    def __init__(self):
        self.data = None
        self.years = []  # 存储数据年份
    
    def load_excel(self, file_path: str) -> bool:
        """
        加载Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.data = pd.read_excel(file_path)
            # 检测年份
            self._detect_years()
            return True
        except Exception as e:
            print(f"加载Excel文件失败: {str(e)}")
            return False
    
    def _detect_years(self):
        """自动检测数据中的年份"""
        # 从列名中提取年份
        years_set = set()
        for col in self.data.columns:
            if '_' in str(col):
                parts = str(col).split('_')
                if len(parts) > 1 and parts[-1].isdigit():
                    years_set.add(int(parts[-1]))
        
        self.years = sorted(list(years_set), reverse=True)[:2]  # 取最近两年
        if not self.years:
            # 如果没有检测到年份，使用默认值
            self.years = [2023, 2022]
    
    def get_basic_info(self) -> Dict[str, any]:
        """
        提取企业基本信息
        
        Returns:
            Dict: 企业基本信息字典
        """
        basic_info = {}
        
        for field in self.BASIC_INFO_FIELDS:
            if field in self.data.columns:
                value = self.data[field].iloc[0]
                # 处理缺失值
                if pd.isna(value):
                    basic_info[field] = "【数据缺失】"
                else:
                    basic_info[field] = value
            else:
                basic_info[field] = "【数据缺失】"
        
        return basic_info
    
    def get_financial_data(self, year: int, table_name: str) -> Dict[str, float]:
        """
        获取指定年份的财务数据
        
        Args:
            year: 年份
            table_name: 报表名称（资产负债表/利润表/现金流量表）
            
        Returns:
            Dict: 财务数据字典
        """
        financial_data = {}
        
        if table_name not in self.FINANCIAL_FIELDS:
            return financial_data
        
        fields = self.FINANCIAL_FIELDS[table_name]
        
        for field in fields:
            col_name = f"{field}_{year}"
            if col_name in self.data.columns:
                value = self.data[col_name].iloc[0]
                # 处理缺失值
                if pd.isna(value):
                    financial_data[field] = None
                else:
                    try:
                        financial_data[field] = float(value)
                    except:
                        financial_data[field] = None
            else:
                financial_data[field] = None
        
        return financial_data
    
    def get_two_year_financial_data(self) -> Dict[int, Dict[str, Dict[str, float]]]:
        """
        获取最近两年的完整财务数据
        
        Returns:
            Dict: {年份: {报表名称: {字段: 值}}}
        """
        result = {}
        
        for year in self.years:
            result[year] = {}
            for table_name in self.FINANCIAL_FIELDS.keys():
                result[year][table_name] = self.get_financial_data(year, table_name)
        
        return result
    
    def validate_data(self) -> Tuple[bool, List[str]]:
        """
        验证数据完整性
        
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        if self.data is None:
            errors.append("未加载数据")
            return False, errors
        
        if self.data.empty:
            errors.append("数据为空")
            return False, errors
        
        # 验证基本信息字段（警告性质，不阻止流程）
        missing_basic = [f for f in self.BASIC_INFO_FIELDS if f not in self.data.columns]
        if missing_basic:
            errors.append(f"缺少基本信息字段: {', '.join(missing_basic)}")
        
        # 验证财务数据字段（至少要有一些数据）
        financial_cols_count = 0
        for table_fields in self.FINANCIAL_FIELDS.values():
            for field in table_fields:
                for year in self.years:
                    col_name = f"{field}_{year}"
                    if col_name in self.data.columns:
                        financial_cols_count += 1
        
        if financial_cols_count == 0:
            errors.append("未找到任何财务数据字段")
            return False, errors
        
        # 即使有警告也返回True，允许生成报告
        return True, errors
    
    def get_years(self) -> List[int]:
        """获取数据年份列表"""
        return self.years


