"""
报告生成模块
负责整合数据、指标、AI分析，生成完整报告
"""

from typing import Dict, List, Optional
from datetime import datetime
from .data_processor import DataProcessor
from .indicator_calculator import IndicatorCalculator
from .ai_analyzer import AIAnalyzer
from .chart_generator import ChartGenerator

class ReportGenerator:
    """财务报告生成器"""
    
    def __init__(self, ai_model: str = None):
        """
        初始化报告生成器
        
        Args:
            ai_model: 指定使用的AI模型，如果为None则使用配置文件中的默认模型
        """
        self.data_processor = None
        self.indicator_calculator = None
        self.ai_analyzer = AIAnalyzer(model=ai_model)
        self.chart_generator = ChartGenerator()
        self.report_data = {}
    
    def generate_report(self, excel_path: str) -> Dict:
        """
        生成完整的财务分析报告
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            Dict: 报告数据字典
        """
        # 1. 加载和验证数据
        self.data_processor = DataProcessor()
        if not self.data_processor.load_excel(excel_path):
            return {"error": "数据加载失败"}
        
        is_valid, errors = self.data_processor.validate_data()
        if not is_valid:
            return {"error": f"数据验证失败: {', '.join(errors)}"}
        
        # 2. 提取基本信息
        basic_info = self.data_processor.get_basic_info()
        
        # 3. 获取财务数据
        financial_data = self.data_processor.get_two_year_financial_data()
        years = self.data_processor.get_years()
        
        # 4. 计算财务指标
        self.indicator_calculator = IndicatorCalculator(financial_data)
        all_indicators = self.indicator_calculator.calculate_all_indicators()
        
        # 5. 生成各维度AI分析
        dimension_analyses = {}
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        
        for dimension in dimensions:
            current_year = years[0] if years else 2023
            indicators = all_indicators.get(current_year, {}).get(dimension, {})
            
            # 准备两年的数据用于趋势分析
            year_data = {}
            for year in years:
                year_data[year] = all_indicators.get(year, {}).get(dimension, {})
            
            # 生成AI分析
            analysis = self.ai_analyzer.analyze_dimension_risk(
                dimension, indicators, year_data, basic_info
            )
            dimension_analyses[dimension] = analysis
        
        # 6. 生成总体风险评估
        overall_assessment = self.ai_analyzer.generate_overall_risk_assessment(
            dimension_analyses, all_indicators.get(years[0] if years else 2023, {}), basic_info
        )
        
        # 7. 生成图表
        print("生成数据可视化图表...")
        charts = {}
        try:
            # 先组装基本报告数据用于图表生成
            temp_report_data = {
                'years': years,
                'indicators': all_indicators,
                'dimension_analyses': dimension_analyses,
                'basic_info': basic_info
            }
            charts = self.chart_generator.generate_all_charts(temp_report_data)
            print(f"成功生成 {len(charts)} 个图表")
        except Exception as e:
            print(f"图表生成失败: {str(e)}")
            charts = {}
        
        # 8. 为PDF生成纯文本版本的分析（移除HTML标签）
        dimension_analyses_pdf = {}
        for dimension, analysis in dimension_analyses.items():
            dimension_analyses_pdf[dimension] = self.ai_analyzer.format_for_pdf(analysis)
        
        overall_assessment_pdf = self.ai_analyzer.format_for_pdf(overall_assessment)
        
        # 9. 组装报告数据
        self.report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'basic_info': basic_info,
            'years': years,
            'financial_data': financial_data,
            'indicators': all_indicators,
            'dimension_analyses': dimension_analyses,  # 用于网页显示（带HTML标签）
            'dimension_analyses_pdf': dimension_analyses_pdf,  # 用于PDF导出（纯文本）
            'overall_assessment': overall_assessment,  # 用于网页显示（带HTML标签）
            'overall_assessment_pdf': overall_assessment_pdf,  # 用于PDF导出（纯文本）
            'validation_errors': errors if errors else [],
            'charts': charts  # 添加图表数据
        }
        
        return self.report_data
    
    def get_report_data(self) -> Dict:
        """获取当前报告数据"""
        return self.report_data
    
    def format_number(self, value: Optional[float], decimal_places: int = 2) -> str:
        """
        格式化数字显示
        
        Args:
            value: 数值
            decimal_places: 小数位数
            
        Returns:
            str: 格式化后的字符串
        """
        if value is None:
            return "【数据缺失】"
        
        # 如果是大数字，转换为万元显示
        if abs(value) >= 10000:
            return f"{value:,.{decimal_places}f}"
        else:
            return f"{value:.{decimal_places}f}"
    
    def get_indicator_unit(self, indicator_name: str) -> str:
        """
        获取指标单位
        
        Args:
            indicator_name: 指标名称
            
        Returns:
            str: 单位
        """
        percentage_indicators = [
            '净利润率', '毛利率', '净资产收益率', '资产负债率'
        ]
        
        ratio_indicators = [
            '流动比率', '速动比率', '应收账款周转率', 
            '存货周转率', '总资产周转率', '现金利润比'
        ]
        
        amount_indicators = [
            '经营性净现金流', '现金净增加额'
        ]
        
        if indicator_name in percentage_indicators:
            return '%'
        elif indicator_name in ratio_indicators:
            return ''
        elif indicator_name in amount_indicators:
            return '万元'
        else:
            return ''
    
    def extract_risk_level(self, analysis_text: str) -> str:
        """
        从分析文本中提取风险等级
        
        Args:
            analysis_text: 分析文本
            
        Returns:
            str: 风险等级
        """
        if '高风险' in analysis_text:
            return '高风险'
        elif '低风险' in analysis_text:
            return '低风险'
        elif '中等风险' in analysis_text:
            return '中等风险'
        else:
            return '待评估'
    
    def get_risk_level_color(self, risk_level: str) -> str:
        """
        获取风险等级对应的颜色
        
        Args:
            risk_level: 风险等级
            
        Returns:
            str: 颜色代码
        """
        color_map = {
            '高风险': '#dc3545',  # 红色
            '中等风险': '#ffc107',  # 黄色
            '低风险': '#28a745',  # 绿色
            '待评估': '#6c757d'  # 灰色
        }
        return color_map.get(risk_level, '#6c757d')


