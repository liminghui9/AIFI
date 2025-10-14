"""
财务指标计算模块
负责计算各类财务风险指标
"""

from typing import Dict, Optional, List

class IndicatorCalculator:
    """财务指标计算器"""
    
    def __init__(self, financial_data: Dict[int, Dict[str, Dict[str, float]]]):
        """
        初始化计算器
        
        Args:
            financial_data: 财务数据字典 {年份: {报表名称: {字段: 值}}}
        """
        self.data = financial_data
        self.years = sorted(list(financial_data.keys()), reverse=True)
    
    def _safe_divide(self, numerator: Optional[float], denominator: Optional[float], 
                     multiply: float = 1.0) -> Optional[float]:
        """
        安全除法，处理None和除零情况
        
        Args:
            numerator: 分子
            denominator: 分母
            multiply: 乘数（用于百分比转换）
            
        Returns:
            计算结果或None
        """
        if numerator is None or denominator is None:
            return None
        if denominator == 0:
            return None
        try:
            return round((numerator / denominator) * multiply, 2)
        except:
            return None
    
    def calculate_profitability_indicators(self, year: int) -> Dict[str, Optional[float]]:
        """
        计算盈利能力指标
        
        Args:
            year: 年份
            
        Returns:
            Dict: 盈利指标字典
        """
        if year not in self.data:
            return {
                '净利润率': None,
                '毛利率': None,
                '净资产收益率': None
            }
        
        balance = self.data[year].get('资产负债表', {})
        income = self.data[year].get('利润表', {})
        
        # 净利润率 = 净利润 / 营业收入 * 100%
        net_profit_margin = self._safe_divide(
            income.get('净利润'),
            income.get('营业收入'),
            100
        )
        
        # 毛利率 = (营业收入 - 营业成本) / 营业收入 * 100%
        gross_profit = None
        if income.get('营业收入') is not None and income.get('营业成本') is not None:
            gross_profit = income.get('营业收入') - income.get('营业成本')
        gross_profit_margin = self._safe_divide(gross_profit, income.get('营业收入'), 100)
        
        # 净资产收益率 = 净利润 / 所有者权益 * 100%
        roe = self._safe_divide(
            income.get('净利润'),
            balance.get('所有者权益'),
            100
        )
        
        return {
            '净利润率': net_profit_margin,
            '毛利率': gross_profit_margin,
            '净资产收益率': roe
        }
    
    def calculate_solvency_indicators(self, year: int) -> Dict[str, Optional[float]]:
        """
        计算偿债能力指标
        
        Args:
            year: 年份
            
        Returns:
            Dict: 偿债指标字典
        """
        if year not in self.data:
            return {
                '资产负债率': None,
                '流动比率': None,
                '速动比率': None
            }
        
        balance = self.data[year].get('资产负债表', {})
        
        # 资产负债率 = 总负债 / 总资产 * 100%
        asset_liability_ratio = self._safe_divide(
            balance.get('总负债'),
            balance.get('总资产'),
            100
        )
        
        # 流动比率 = 流动资产 / 流动负债
        current_ratio = self._safe_divide(
            balance.get('流动资产'),
            balance.get('流动负债')
        )
        
        # 速动比率 = (流动资产 - 存货) / 流动负债
        # 注：此处简化处理，假设存货数据可能缺失，使用流动资产的80%作为速动资产
        quick_assets = balance.get('流动资产')
        if quick_assets is not None:
            quick_assets = quick_assets * 0.8  # 简化估算
        quick_ratio = self._safe_divide(quick_assets, balance.get('流动负债'))
        
        return {
            '资产负债率': asset_liability_ratio,
            '流动比率': current_ratio,
            '速动比率': quick_ratio
        }
    
    def calculate_operation_indicators(self, year: int) -> Dict[str, Optional[float]]:
        """
        计算运营能力指标
        
        Args:
            year: 年份
            
        Returns:
            Dict: 运营指标字典
        """
        if year not in self.data:
            return {
                '应收账款周转率': None,
                '存货周转率': None,
                '总资产周转率': None
            }
        
        balance = self.data[year].get('资产负债表', {})
        income = self.data[year].get('利润表', {})
        
        # 注：周转率指标需要平均值，此处简化使用期末值
        
        # 应收账款周转率 = 营业收入 / 应收账款
        # 假设应收账款约为流动资产的30%（简化估算）
        receivables = balance.get('流动资产')
        if receivables is not None:
            receivables = receivables * 0.3
        receivables_turnover = self._safe_divide(income.get('营业收入'), receivables)
        
        # 存货周转率 = 营业成本 / 存货
        # 假设存货约为流动资产的20%（简化估算）
        inventory = balance.get('流动资产')
        if inventory is not None:
            inventory = inventory * 0.2
        inventory_turnover = self._safe_divide(income.get('营业成本'), inventory)
        
        # 总资产周转率 = 营业收入 / 总资产
        total_asset_turnover = self._safe_divide(
            income.get('营业收入'),
            balance.get('总资产')
        )
        
        return {
            '应收账款周转率': receivables_turnover,
            '存货周转率': inventory_turnover,
            '总资产周转率': total_asset_turnover
        }
    
    def calculate_cashflow_indicators(self, year: int) -> Dict[str, Optional[float]]:
        """
        计算现金流指标
        
        Args:
            year: 年份
            
        Returns:
            Dict: 现金流指标字典
        """
        if year not in self.data:
            return {
                '现金利润比': None,
                '经营性净现金流': None,
                '现金净增加额': None
            }
        
        income = self.data[year].get('利润表', {})
        cashflow = self.data[year].get('现金流量表', {})
        
        # 现金利润比 = 经营活动现金流量净额 / 净利润
        cash_profit_ratio = self._safe_divide(
            cashflow.get('经营活动现金流量净额'),
            income.get('净利润')
        )
        
        # 经营性净现金流（直接取值，单位：万元）
        operating_cashflow = cashflow.get('经营活动现金流量净额')
        
        # 现金净增加额（直接取值，单位：万元）
        cash_increase = cashflow.get('现金及现金等价物净增加额')
        
        return {
            '现金利润比': cash_profit_ratio,
            '经营性净现金流': operating_cashflow,
            '现金净增加额': cash_increase
        }
    
    def calculate_all_indicators(self) -> Dict[int, Dict[str, Dict[str, Optional[float]]]]:
        """
        计算所有年份的全部指标
        
        Returns:
            Dict: {年份: {维度: {指标: 值}}}
        """
        result = {}
        
        for year in self.years:
            result[year] = {
                '盈利风险': self.calculate_profitability_indicators(year),
                '偿债风险': self.calculate_solvency_indicators(year),
                '运营风险': self.calculate_operation_indicators(year),
                '现金流风险': self.calculate_cashflow_indicators(year)
            }
        
        return result
    
    def format_indicator_value(self, value: Optional[float], unit: str = '') -> str:
        """
        格式化指标值用于显示
        
        Args:
            value: 指标值
            unit: 单位
            
        Returns:
            格式化后的字符串
        """
        if value is None:
            return "【数据缺失】"
        return f"{value}{unit}"


