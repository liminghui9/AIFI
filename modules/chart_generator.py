"""
财务图表生成模块
负责生成各种财务分析图表
"""

import os
import matplotlib.pyplot as plt
import matplotlib
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Tuple, Optional
import base64
import io
from datetime import datetime

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False

class ChartGenerator:
    """财务图表生成器"""
    
    def __init__(self, static_folder: str = "static"):
        """
        初始化图表生成器
        
        Args:
            static_folder: 静态文件存储目录
        """
        self.static_folder = static_folder
        self.charts_folder = os.path.join(static_folder, 'charts')
        
        # 确保图表目录存在
        if not os.path.exists(self.charts_folder):
            os.makedirs(self.charts_folder, exist_ok=True)
            
        # 图表样式配置
        self.color_palette = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
            '#9b59b6', '#1abc9c', '#34495e', '#95a5a6'
        ]
        
        self.risk_colors = {
            '低风险': '#2ecc71',    # 绿色
            '中等风险': '#f39c12',  # 橙色  
            '高风险': '#e74c3c'     # 红色
        }
    
    def generate_all_charts(self, report_data: Dict) -> Dict[str, str]:
        """
        生成所有图表
        
        Args:
            report_data: 报告数据
            
        Returns:
            Dict[str, str]: 图表名称到文件路径的映射
        """
        charts = {}
        
        # 获取基础数据
        years = report_data.get('years', [])
        indicators = report_data.get('indicators', {})
        dimension_analyses = report_data.get('dimension_analyses', {})
        
        if not years or not indicators:
            return charts
        
        try:
            # 1. 主要财务指标对比图
            charts['main_indicators'] = self._generate_main_indicators_chart(years, indicators)
            
            # 2. 盈利能力趋势图
            charts['profitability'] = self._generate_profitability_chart(years, indicators)
            
            # 3. 偿债能力分析图
            charts['solvency'] = self._generate_solvency_chart(years, indicators)
            
            # 4. 运营能力分析图
            charts['operational'] = self._generate_operational_chart(years, indicators)
            
            # 5. 现金流分析图
            charts['cashflow'] = self._generate_cashflow_chart(years, indicators)
            
            # 6. 风险评估雷达图
            charts['risk_radar'] = self._generate_risk_radar_chart(dimension_analyses)
            
            # 7. 综合财务健康度仪表盘
            charts['health_dashboard'] = self._generate_health_dashboard(indicators, dimension_analyses)
            
        except Exception as e:
            print(f"生成图表时出错: {str(e)}")
        
        return charts
    
    def _generate_main_indicators_chart(self, years: List[int], indicators: Dict) -> str:
        """生成主要财务指标对比图"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('收入与利润', '资产负债率', '净资产收益率', '流动比率'),
            specs=[[{"secondary_y": True}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 数据准备
        revenue_data = []
        profit_data = []
        asset_liability_ratio = []
        roe_data = []
        current_ratio = []
        
        for year in years:
            year_indicators = indicators.get(year, {})
            # 假设我们能从基础财务数据中获取这些信息
            revenue_data.append(year_indicators.get('营业收入', 0))
            profit_data.append(year_indicators.get('净利润', 0))
            
            # 从各维度指标中提取
            profitability = year_indicators.get('盈利风险', {})
            solvency = year_indicators.get('偿债风险', {})
            
            asset_liability_ratio.append(solvency.get('资产负债率', 0))
            roe_data.append(profitability.get('净资产收益率', 0))
            current_ratio.append(solvency.get('流动比率', 0))
        
        # 添加图表
        # 收入与利润 (双轴)
        fig.add_trace(go.Bar(name='营业收入', x=years, y=revenue_data, 
                            marker_color=self.color_palette[0]), 
                      row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(name='净利润', x=years, y=profit_data, 
                                mode='lines+markers', line=dict(color=self.color_palette[1])), 
                      row=1, col=1, secondary_y=True)
        
        # 资产负债率
        fig.add_trace(go.Bar(name='资产负债率(%)', x=years, y=asset_liability_ratio, 
                            marker_color=self.color_palette[2]), row=1, col=2)
        
        # 净资产收益率
        fig.add_trace(go.Scatter(name='净资产收益率(%)', x=years, y=roe_data, 
                                mode='lines+markers', marker_size=10, 
                                line=dict(color=self.color_palette[3])), row=2, col=1)
        
        # 流动比率
        fig.add_trace(go.Bar(name='流动比率', x=years, y=current_ratio, 
                            marker_color=self.color_palette[4]), row=2, col=2)
        
        fig.update_layout(
            title_text="主要财务指标分析",
            height=600,
            showlegend=False,
            font=dict(family="Microsoft YaHei, Arial", size=12)
        )
        
        # 保存图表
        filename = f"main_indicators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _generate_profitability_chart(self, years: List[int], indicators: Dict) -> str:
        """生成盈利能力趋势图"""
        fig = go.Figure()
        
        # 提取盈利能力指标
        metrics = ['净利润率', '毛利率', '净资产收益率']
        
        for metric in metrics:
            values = []
            for year in years:
                profitability_data = indicators.get(year, {}).get('盈利风险', {})
                values.append(profitability_data.get(metric, 0))
            
            fig.add_trace(go.Scatter(
                x=years, y=values, 
                mode='lines+markers',
                name=metric,
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title='盈利能力趋势分析',
            xaxis_title='年份',
            yaxis_title='比率 (%)',
            height=400,
            template='plotly_white',
            font=dict(family="Microsoft YaHei, Arial", size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                      annotation_text="盈亏平衡线")
        
        filename = f"profitability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _generate_solvency_chart(self, years: List[int], indicators: Dict) -> str:
        """生成偿债能力分析图"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('短期偿债能力', '长期偿债能力'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # 短期偿债能力指标
        current_ratios = []
        quick_ratios = []
        
        # 长期偿债能力指标  
        asset_liability_ratios = []
        
        for year in years:
            solvency_data = indicators.get(year, {}).get('偿债风险', {})
            current_ratios.append(solvency_data.get('流动比率', 0))
            quick_ratios.append(solvency_data.get('速动比率', 0))
            asset_liability_ratios.append(solvency_data.get('资产负债率', 0))
        
        # 添加短期偿债能力图表
        fig.add_trace(go.Bar(name='流动比率', x=years, y=current_ratios, 
                            marker_color=self.color_palette[0]), row=1, col=1)
        fig.add_trace(go.Bar(name='速动比率', x=years, y=quick_ratios, 
                            marker_color=self.color_palette[1]), row=1, col=1)
        
        # 添加长期偿债能力图表
        fig.add_trace(go.Bar(name='资产负债率(%)', x=years, y=asset_liability_ratios, 
                            marker_color=self.color_palette[2]), row=1, col=2)
        
        # 添加安全线参考
        fig.add_hline(y=2.0, line_dash="dash", line_color="green", 
                      annotation_text="流动比率安全线(2.0)", row=1, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", 
                      annotation_text="资产负债率警戒线(70%)", row=1, col=2)
        
        fig.update_layout(
            title_text="偿债能力分析",
            height=400,
            font=dict(family="Microsoft YaHei, Arial", size=12)
        )
        
        filename = f"solvency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _generate_operational_chart(self, years: List[int], indicators: Dict) -> str:
        """生成运营能力分析图"""
        fig = go.Figure()
        
        # 运营能力指标
        metrics = {
            '应收账款周转率': '次',
            '存货周转率': '次', 
            '总资产周转率': '次'
        }
        
        for metric, unit in metrics.items():
            values = []
            for year in years:
                operational_data = indicators.get(year, {}).get('运营风险', {})
                values.append(operational_data.get(metric, 0))
            
            fig.add_trace(go.Bar(
                name=f"{metric}({unit})",
                x=years, y=values,
                text=[f"{v:.2f}" for v in values],
                textposition='auto'
            ))
        
        fig.update_layout(
            title='运营能力分析',
            xaxis_title='年份',
            yaxis_title='周转率 (次)',
            height=400,
            template='plotly_white',
            font=dict(family="Microsoft YaHei, Arial", size=12),
            barmode='group'
        )
        
        filename = f"operational_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _generate_cashflow_chart(self, years: List[int], indicators: Dict) -> str:
        """生成现金流分析图"""
        fig = go.Figure()
        
        # 现金流指标
        operating_cashflow = []
        cash_profit_ratio = []
        
        for year in years:
            cashflow_data = indicators.get(year, {}).get('现金流风险', {})
            operating_cashflow.append(cashflow_data.get('经营性净现金流', 0))
            cash_profit_ratio.append(cashflow_data.get('现金利润比', 0))
        
        # 双轴图表
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 经营性净现金流（柱状图）
        fig.add_trace(
            go.Bar(name='经营性净现金流(万元)', x=years, y=operating_cashflow,
                   marker_color=self.color_palette[0]),
            secondary_y=False,
        )
        
        # 现金利润比（线图）
        fig.add_trace(
            go.Scatter(name='现金利润比', x=years, y=cash_profit_ratio,
                      mode='lines+markers', line=dict(color=self.color_palette[1], width=3)),
            secondary_y=True,
        )
        
        # 设置y轴标题
        fig.update_yaxes(title_text="现金流(万元)", secondary_y=False)
        fig.update_yaxes(title_text="现金利润比", secondary_y=True)
        
        fig.update_layout(
            title_text="现金流状况分析",
            xaxis_title="年份",
            height=400,
            font=dict(family="Microsoft YaHei, Arial", size=12)
        )
        
        filename = f"cashflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _generate_risk_radar_chart(self, dimension_analyses: Dict) -> str:
        """生成风险评估雷达图"""
        # 风险维度和对应的分数
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        
        # 提取风险等级并转换为数值
        risk_scores = []
        risk_levels = []
        
        for dimension in dimensions:
            analysis = dimension_analyses.get(dimension, {})
            risk_level = analysis.get('risk_level', '中等风险')
            risk_levels.append(risk_level)
            
            # 风险等级转分数 (分数越高风险越低)
            score_map = {'低风险': 90, '中等风险': 60, '高风险': 30}
            risk_scores.append(score_map.get(risk_level, 60))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=risk_scores,
            theta=dimensions,
            fill='toself',
            name='风险评估',
            line_color='rgb(46, 204, 113)',
            fillcolor='rgba(46, 204, 113, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[30, 60, 90],
                    ticktext=['高风险', '中等风险', '低风险']
                )),
            title="财务风险评估雷达图",
            height=500,
            font=dict(family="Microsoft YaHei, Arial", size=12)
        )
        
        filename = f"risk_radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _generate_health_dashboard(self, indicators: Dict, dimension_analyses: Dict) -> str:
        """生成财务健康度仪表盘"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('盈利能力', '偿债能力', '运营能力', '现金流状况'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # 计算各维度健康度分数
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        positions = [(1,1), (1,2), (2,1), (2,2)]
        
        for i, dimension in enumerate(dimensions):
            analysis = dimension_analyses.get(dimension, {})
            risk_level = analysis.get('risk_level', '中等风险')
            
            # 转换为健康度分数
            score_map = {'低风险': 85, '中等风险': 65, '高风险': 35}
            score = score_map.get(risk_level, 65)
            
            # 确定颜色
            if score >= 80:
                color = "green"
            elif score >= 60:
                color = "yellow" 
            else:
                color = "red"
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': dimension.replace('风险', '能力')},
                gauge = {'axis': {'range': [None, 100]},
                        'bar': {'color': color},
                        'steps' : [
                            {'range': [0, 40], 'color': "lightgray"},
                            {'range': [40, 70], 'color': "gray"},
                            {'range': [70, 100], 'color': "lightgreen"}],
                        'threshold' : {'line': {'color': "red", 'width': 4},
                                      'thickness': 0.75, 'value': 90}}),
                row=positions[i][0], col=positions[i][1])
        
        fig.update_layout(
            title_text="财务健康度仪表盘",
            height=600,
            font=dict(family="Microsoft YaHei, Arial", size=10)
        )
        
        filename = f"health_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.charts_folder, filename)
        fig.write_html(filepath)
        
        return f"/static/charts/{filename}"
    
    def _extract_risk_level(self, analysis_text: str) -> str:
        """从分析文本中提取风险等级"""
        if '高风险' in analysis_text:
            return '高风险'
        elif '低风险' in analysis_text:
            return '低风险'
        elif '中等风险' in analysis_text:
            return '中等风险'
        else:
            return '中等风险'
    
    def cleanup_old_charts(self, keep_recent: int = 10):
        """清理旧的图表文件"""
        try:
            if not os.path.exists(self.charts_folder):
                return
            
            # 获取所有图表文件
            chart_files = []
            for filename in os.listdir(self.charts_folder):
                if filename.endswith('.html'):
                    filepath = os.path.join(self.charts_folder, filename)
                    mtime = os.path.getmtime(filepath)
                    chart_files.append((filepath, mtime))
            
            # 按修改时间排序
            chart_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出保留数量的文件
            for filepath, _ in chart_files[keep_recent:]:
                try:
                    os.remove(filepath)
                except:
                    pass
                    
        except Exception as e:
            print(f"清理图表文件时出错: {str(e)}")



