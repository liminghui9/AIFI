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
            
        # 现代化图表样式配置
        self.color_palette = [
            '#3b82f6',  # 蓝色
            '#8b5cf6',  # 紫色
            '#06b6d4',  # 青色
            '#10b981',  # 绿色
            '#f59e0b',  # 橙色
            '#ef4444',  # 红色
            '#6366f1',  # 靛蓝
            '#ec4899'   # 粉色
        ]
        
        self.risk_colors = {
            '低风险': '#10b981',    # 绿色
            '中等风险': '#f59e0b',  # 橙色  
            '高风险': '#ef4444'     # 红色
        }
        
        # 统一的图表布局配置
        self.layout_config = {
            'template': 'plotly_white',
            'font': {
                'family': 'Microsoft YaHei, SimHei, Arial',
                'size': 12,
                'color': '#1e293b'
            },
            'plot_bgcolor': '#ffffff',
            'paper_bgcolor': '#ffffff',
            'margin': {'l': 60, 'r': 40, 't': 80, 'b': 60},
            'hoverlabel': {
                'bgcolor': '#1e40af',
                'font': {'size': 13, 'color': 'white', 'family': 'Microsoft YaHei'},
                'bordercolor': '#1e40af'
            },
            'xaxis': {
                'showgrid': True,
                'gridcolor': '#f1f5f9',
                'gridwidth': 1,
                'showline': True,
                'linecolor': '#cbd5e1',
                'linewidth': 2,
                'tickfont': {'size': 11, 'color': '#64748b'}
            },
            'yaxis': {
                'showgrid': True,
                'gridcolor': '#f1f5f9',
                'gridwidth': 1,
                'showline': True,
                'linecolor': '#cbd5e1',
                'linewidth': 2,
                'tickfont': {'size': 11, 'color': '#64748b'}
            },
            'title': {
                'font': {'size': 16, 'color': '#1e3a8a', 'family': 'Microsoft YaHei'},
                'x': 0.5,
                'xanchor': 'center'
            }
        }
    
    def generate_all_charts(self, report_data: Dict) -> Dict[str, str]:
        """
        生成所有图表（HTML和PNG格式）
        
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
            html_path, png_path = self._generate_main_indicators_chart(years, indicators)
            charts['main_indicators'] = html_path
            charts['main_indicators_png'] = png_path
            
            # 2. 盈利能力趋势图
            html_path, png_path = self._generate_profitability_chart(years, indicators)
            charts['profitability'] = html_path
            charts['profitability_png'] = png_path
            
            # 3. 偿债能力分析图
            html_path, png_path = self._generate_solvency_chart(years, indicators)
            charts['solvency'] = html_path
            charts['solvency_png'] = png_path
            
            # 4. 运营能力分析图
            html_path, png_path = self._generate_operational_chart(years, indicators)
            charts['operational'] = html_path
            charts['operational_png'] = png_path
            
            # 5. 现金流分析图
            html_path, png_path = self._generate_cashflow_chart(years, indicators)
            charts['cashflow'] = html_path
            charts['cashflow_png'] = png_path
            
            # 6. 风险评估雷达图
            html_path, png_path = self._generate_risk_radar_chart(dimension_analyses)
            charts['risk_radar'] = html_path
            charts['risk_radar_png'] = png_path
            
            # 7. 综合财务健康度仪表盘
            html_path, png_path = self._generate_health_dashboard(indicators, dimension_analyses)
            charts['health_dashboard'] = html_path
            charts['health_dashboard_png'] = png_path
            
        except Exception as e:
            print(f"生成图表时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return charts
    
    def _save_chart_as_png(self, fig, base_filename: str) -> str:
        """
        将Plotly图表保存为PNG格式（使用matplotlib作为后备）
        
        Args:
            fig: Plotly图表对象
            base_filename: 基础文件名（不含扩展名）
            
        Returns:
            str: PNG文件的绝对路径
        """
        png_filename = f"{base_filename}.png"
        png_filepath = os.path.join(self.charts_folder, png_filename)
        
        try:
            # 根据图表类型动态设置尺寸
            if 'health_dashboard' in base_filename:
                width, height = 1200, 900  # 仪表盘使用更大尺寸
            elif 'risk_radar' in base_filename:
                width, height = 1100, 650  # 雷达图
            else:
                width, height = 1100, 600  # 其他图表（增加高度以容纳底部图例）
            
            # 使用kaleido导出（Plotly 6+默认使用kaleido）
            fig.write_image(
                png_filepath,
                width=width,
                height=height,
                scale=2  # 提高分辨率
            )
            print(f"✓ 使用kaleido生成PNG: {png_filename}")
            # 返回绝对路径，供PDF生成使用
            return os.path.abspath(png_filepath)
            
        except Exception as e1:
            print(f"⚠ PNG导出失败: {str(e1)}")
            
            # 使用matplotlib手动绘制简化版本
            try:
                print(f"→ 尝试使用matplotlib生成备用图表...")
                self._create_static_chart_fallback(fig, png_filepath)
                # 返回绝对路径
                return os.path.abspath(png_filepath)
            except Exception as e2:
                print(f"✗ 所有方法都失败: {str(e2)}")
                return None
    
    def _create_static_chart_fallback(self, plotly_fig, output_path: str):
        """使用matplotlib创建静态图表作为后备方案"""
        # 这是一个简化的后备方案，创建基本的图表
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, '图表生成中...\n请安装 kaleido 以显示完整图表\npip install kaleido', 
                ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"✓ 生成占位图表: {output_path}")
    
    def _generate_main_indicators_chart(self, years: List[int], indicators: Dict) -> Tuple[str, str]:
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
        
        # 移除layout_config中的title，避免冲突
        layout_config = self.layout_config.copy()
        layout_config.pop('title', None)
        
        fig.update_layout(
            **layout_config,
            title=dict(
                text="<b>主要财务指标分析</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#1e3a8a', family='Microsoft YaHei')
            ),
            height=700,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#e2e8f0',
                borderwidth=2,
                font=dict(size=11)
            ),
            hovermode='x unified'
        )
        
        # 设置Y轴自动调整边距
        fig.update_yaxes(automargin=True)
        fig.update_xaxes(automargin=True)
        
        # 保存图表
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"main_indicators_{timestamp}"
        
        # HTML版本
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        # PNG版本
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _generate_profitability_chart(self, years: List[int], indicators: Dict) -> Tuple[str, str]:
        """生成盈利能力趋势图"""
        fig = go.Figure()
        
        # 提取盈利能力指标（使用简短名称）
        metrics_mapping = {
            '净利润率': '净利润率',
            '毛利率': '毛利率',
            '净资产收益率': 'ROE'
        }
        colors = [self.color_palette[0], self.color_palette[1], self.color_palette[2]]
        
        for i, (full_name, short_name) in enumerate(metrics_mapping.items()):
            values = []
            for year in years:
                profitability_data = indicators.get(year, {}).get('盈利风险', {})
                values.append(profitability_data.get(full_name, 0))
            
            fig.add_trace(go.Scatter(
                x=years, y=values, 
                mode='lines+markers',
                name=short_name,
                line=dict(width=4, color=colors[i], shape='spline'),
                marker=dict(size=12, color=colors[i], line=dict(width=2, color='white')),
                hovertemplate=f'<b>{full_name}</b><br>年份: %{{x}}<br>比率: %{{y:.2f}}%<extra></extra>',
                fill='tonexty' if i > 0 else None,
                fillcolor=f'rgba{tuple(list(int(colors[i][j:j+2], 16) for j in (1, 3, 5)) + [0.1])}'.replace('[', '(').replace(']', ')')
            ))
        
        fig.update_layout(
            **self.layout_config,
            title=dict(
                text='<b>📈 盈利能力趋势分析</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#1e3a8a')
            ),
            xaxis_title='<b>年份</b>',
            yaxis_title='<b>比率 (%)</b>',
            height=600,  # 增加高度
            margin=dict(l=80, r=80, t=100, b=120),  # 增加底部边距
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.18,  # 调整图例位置
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.98)',
                bordercolor='#e2e8f0',
                borderwidth=2,
                font=dict(size=12)
            ),
            hovermode='x unified'
        )
        
        fig.update_yaxes(automargin=True)
        fig.update_xaxes(automargin=True)
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                      annotation_text="盈亏平衡线")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"profitability_{timestamp}"
        
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _generate_solvency_chart(self, years: List[int], indicators: Dict) -> Tuple[str, str]:
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
            **self.layout_config,
            title=dict(
                text="<b>💰 偿债能力分析</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#1e3a8a')
            ),
            height=600,  # 增加高度
            margin=dict(l=80, r=80, t=100, b=120),  # 增加底部边距
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.18,  # 调整图例位置
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.98)',
                bordercolor='#e2e8f0',
                borderwidth=2,
                font=dict(size=12)
            ),
            hovermode='x unified'
        )
        
        fig.update_yaxes(automargin=True)
        fig.update_xaxes(automargin=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"solvency_{timestamp}"
        
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _generate_operational_chart(self, years: List[int], indicators: Dict) -> Tuple[str, str]:
        """生成运营能力分析图"""
        fig = go.Figure()
        
        # 运营能力指标（缩短名称）
        metrics = {
            '应收账款周转率': '应收账款',
            '存货周转率': '存货', 
            '总资产周转率': '总资产'
        }
        
        colors = [self.color_palette[0], self.color_palette[1], self.color_palette[2]]
        
        for i, (metric, short_name) in enumerate(metrics.items()):
            values = []
            for year in years:
                operational_data = indicators.get(year, {}).get('运营风险', {})
                values.append(operational_data.get(metric, 0))
            
            fig.add_trace(go.Bar(
                name=short_name,
                x=years, y=values,
                text=[f"{v:.2f}" for v in values],
                textposition='auto',
                marker_color=colors[i],
                hovertemplate=f'<b>{metric}</b><br>年份: %{{x}}<br>周转率: %{{y:.2f}}次<extra></extra>'
            ))
        
        fig.update_layout(
            **self.layout_config,
            title=dict(
                text='<b>⚡ 运营能力分析</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#1e3a8a')
            ),
            xaxis_title='<b>年份</b>',
            yaxis_title='<b>周转率 (次)</b>',
            height=600,  # 增加高度为图例留空间
            barmode='group',
            margin=dict(l=80, r=80, t=100, b=120),  # 增加底部边距
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.18,  # 调整图例位置
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.98)',
                bordercolor='#e2e8f0',
                borderwidth=2,
                font=dict(size=12)
            ),
            hovermode='x unified'
        )
        
        fig.update_yaxes(automargin=True)
        fig.update_xaxes(automargin=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"operational_{timestamp}"
        
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _generate_cashflow_chart(self, years: List[int], indicators: Dict) -> Tuple[str, str]:
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
            go.Bar(name='经营现金流', x=years, y=operating_cashflow,
                   marker_color=self.color_palette[0],
                   text=[f'{v:,.0f}' for v in operating_cashflow],
                   textposition='outside',
                   hovertemplate='<b>经营性净现金流</b><br>年份: %{x}<br>金额: %{y:,.2f}万元<extra></extra>'),
            secondary_y=False,
        )
        
        # 现金利润比（线图）
        fig.add_trace(
            go.Scatter(name='利润比', x=years, y=cash_profit_ratio,
                      mode='lines+markers', 
                      line=dict(color=self.color_palette[1], width=3),
                      marker=dict(size=10),
                      hovertemplate='<b>现金利润比</b><br>年份: %{x}<br>比率: %{y:.2f}<extra></extra>'),
            secondary_y=True,
        )
        
        # 设置y轴标题和格式
        fig.update_yaxes(
            title_text="现金流(万元)", 
            secondary_y=False,
            automargin=True
        )
        fig.update_yaxes(
            title_text="现金利润比", 
            secondary_y=True,
            automargin=True
        )
        
        fig.update_layout(
            **self.layout_config,
            title=dict(
                text="<b>💵 现金流状况分析</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#1e3a8a')
            ),
            xaxis_title="<b>年份</b>",
            height=600,  # 增加高度
            margin=dict(l=80, r=80, t=100, b=120),  # 增加底部边距
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.18,  # 调整图例位置
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.98)',
                bordercolor='#e2e8f0',
                borderwidth=2,
                font=dict(size=12)
            ),
            hovermode='x unified'
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"cashflow_{timestamp}"
        
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _generate_risk_radar_chart(self, dimension_analyses: Dict) -> Tuple[str, str]:
        """生成风险评估雷达图"""
        # 风险维度和对应的分数
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        
        # 提取风险等级并转换为数值
        risk_scores = []
        risk_levels = []
        
        for dimension in dimensions:
            # dimension_analyses 的值是字符串（AI分析文字），需要从中提取风险等级
            analysis_text = dimension_analyses.get(dimension, '')
            
            # 从分析文字中提取风险等级
            risk_level = '中等风险'  # 默认值
            if '高风险' in analysis_text:
                risk_level = '高风险'
            elif '低风险' in analysis_text:
                risk_level = '低风险'
            elif '中等风险' in analysis_text:
                risk_level = '中等风险'
            
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
            line=dict(color='#3b82f6', width=3),
            fillcolor='rgba(59, 130, 246, 0.25)',
            marker=dict(size=10, color='#3b82f6', line=dict(width=2, color='white'))
        ))
        
        fig.update_layout(
            **self.layout_config,
            polar=dict(
                bgcolor='#fafbfc',
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[30, 60, 90],
                    ticktext=['<b>高风险</b>', '<b>中等风险</b>', '<b>低风险</b>'],
                    tickfont=dict(size=11, color='#64748b'),
                    gridcolor='#e2e8f0',
                    gridwidth=2
                ),
                angularaxis=dict(
                    gridcolor='#cbd5e1',
                    gridwidth=2,
                    tickfont=dict(size=13, color='#1e293b', family='Microsoft YaHei')
                )
            ),
            title=dict(
                text="<b>🎯 财务风险评估雷达图</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#1e3a8a')
            ),
            height=650,
            showlegend=False
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"risk_radar_{timestamp}"
        
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _generate_health_dashboard(self, indicators: Dict, dimension_analyses: Dict) -> Tuple[str, str]:
        """生成财务健康度仪表盘"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('', '', '', ''),  # 使用空标题，后面用annotations添加
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]],
            vertical_spacing=0.25,  # 增加垂直间距
            horizontal_spacing=0.15  # 增加水平间距
        )
        
        # 计算各维度健康度分数
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        dimension_names = ['盈利能力', '偿债能力', '运营能力', '现金流状况']
        positions = [(1,1), (1,2), (2,1), (2,2)]
        
        for i, dimension in enumerate(dimensions):
            analysis = dimension_analyses.get(dimension, {})
            
            # 方法1：从分析文本中提取风险等级
            if isinstance(analysis, str):
                risk_level = self._extract_risk_level_advanced(analysis)
                print(f"🎯 {dimension} 风险等级(文本提取): {risk_level}")
            elif isinstance(analysis, dict):
                risk_level = analysis.get('risk_level', '中等风险')
                print(f"🎯 {dimension} 风险等级(字典): {risk_level}")
            else:
                risk_level = '中等风险'
            
            # 方法2：基于实际指标数据计算分数（更准确）
            if indicators:
                # 获取最新年度的数据
                latest_year = max(indicators.keys())
                year_indicators = indicators[latest_year].get(dimension, {})
                
                # 基于指标计算健康度分数
                calculated_score = self._calculate_dimension_score(dimension, year_indicators)
                if calculated_score is not None:
                    score = calculated_score
                    print(f"✅ {dimension} 使用计算分数: {score}")
                else:
                    # 如果无法计算，使用文本提取的风险等级
                    score_map = {'低风险': 85, '中等风险': 65, '高风险': 35}
                    score = score_map.get(risk_level, 65)
                    print(f"📝 {dimension} 使用文本分数: {score}")
            else:
                # 没有指标数据，使用文本提取的风险等级
                score_map = {'低风险': 85, '中等风险': 65, '高风险': 35}
                score = score_map.get(risk_level, 65)
            
            # 确定颜色
            if score >= 80:
                color = "green"
            elif score >= 60:
                color = "yellow" 
            else:
                color = "red"
            
            # 现代化配色方案
            if score >= 80:
                bar_color = "#10b981"  # 绿色
                bg_colors = [
                    {'range': [0, 40], 'color': "#fee2e2"},    # 浅红
                    {'range': [40, 70], 'color': "#fef3c7"},   # 浅黄
                    {'range': [70, 100], 'color': "#d1fae5"}   # 浅绿
                ]
            elif score >= 60:
                bar_color = "#f59e0b"  # 橙色
                bg_colors = [
                    {'range': [0, 40], 'color': "#fee2e2"},
                    {'range': [40, 70], 'color': "#fef3c7"},
                    {'range': [70, 100], 'color': "#d1fae5"}
                ]
            else:
                bar_color = "#ef4444"  # 红色
                bg_colors = [
                    {'range': [0, 40], 'color': "#fee2e2"},
                    {'range': [40, 70], 'color': "#fef3c7"},
                    {'range': [70, 100], 'color': "#d1fae5"}
                ]
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = score,
                domain = {'x': [0.05, 0.95], 'y': [0.1, 0.9]},  # 调整domain防止裁剪
                number = {
                    'font': {'size': 42, 'color': '#1e293b', 'family': 'Microsoft YaHei'},
                    'suffix': "",
                    'valueformat': '.1f'
                },
                delta = {
                    'reference': 70, 
                    'increasing': {'color': "#10b981"}, 
                    'decreasing': {'color': "#ef4444"},
                    'font': {'size': 14}
                },
                gauge = {
                    'axis': {
                        'range': [None, 100],
                        'tickwidth': 2,
                        'tickcolor': "#cbd5e1",
                        'tickfont': {'size': 12, 'color': '#64748b'},
                        'tickmode': 'linear',
                        'tick0': 0,
                        'dtick': 20
                    },
                    'bar': {'color': bar_color, 'thickness': 0.7},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#e2e8f0",
                    'steps': bg_colors,
                    'threshold': {
                        'line': {'color': "#dc2626", 'width': 3},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ), row=positions[i][0], col=positions[i][1])
        
        fig.update_layout(
            **self.layout_config,
            title=dict(
                text="<b>💎 财务健康度仪表盘</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=20, color='#1e3a8a', family='Microsoft YaHei'),
                y=0.98,
                yanchor='top'
            ),
            height=900,  # 增加高度以完整显示所有仪表
            width=1200,  # 固定宽度
            showlegend=False,
            margin=dict(l=80, r=80, t=120, b=80),  # 调整边距
            annotations=[
                dict(
                    text=f"<b>{dimension_names[i]}</b>",
                    x=0.22 if i % 2 == 0 else 0.78,  # 调整标题位置
                    y=0.88 if i < 2 else 0.38,
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    font=dict(size=15, color='#1e3a8a', family='Microsoft YaHei'),
                    xanchor='center'
                ) for i in range(4)
            ]
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"health_dashboard_{timestamp}"
        
        html_filename = f"{base_name}.html"
        html_filepath = os.path.join(self.charts_folder, html_filename)
        fig.write_html(html_filepath)
        
        png_filepath = self._save_chart_as_png(fig, base_name)
        
        return f"/static/charts/{html_filename}", png_filepath
    
    def _extract_risk_level(self, analysis_text: str) -> str:
        """从分析文本中提取风险等级（简单版本）"""
        if '高风险' in analysis_text:
            return '高风险'
        elif '低风险' in analysis_text:
            return '低风险'
        elif '中等风险' in analysis_text:
            return '中等风险'
        else:
            return '中等风险'
    
    def _calculate_dimension_score(self, dimension: str, indicators: Dict[str, Optional[float]]) -> Optional[float]:
        """
        基于实际指标数据计算维度健康度分数
        
        Args:
            dimension: 维度名称
            indicators: 该维度的指标数据
            
        Returns:
            float: 健康度分数 (0-100)，None表示无法计算
        """
        if not indicators:
            return None
        
        scores = []
        
        if dimension == '盈利风险':
            # 盈利能力评分
            net_margin = indicators.get('净利润率')
            if net_margin is not None:
                if net_margin >= 15:
                    scores.append(95)
                elif net_margin >= 10:
                    scores.append(85)
                elif net_margin >= 5:
                    scores.append(70)
                elif net_margin >= 0:
                    scores.append(50)
                else:
                    scores.append(25)
            
            roe = indicators.get('净资产收益率')
            if roe is not None:
                if roe >= 15:
                    scores.append(95)
                elif roe >= 10:
                    scores.append(80)
                elif roe >= 5:
                    scores.append(60)
                else:
                    scores.append(35)
        
        elif dimension == '偿债风险':
            # 偿债能力评分（风险越低，分数越高）
            asset_liability = indicators.get('资产负债率')
            if asset_liability is not None:
                if asset_liability <= 40:
                    scores.append(95)
                elif asset_liability <= 60:
                    scores.append(80)
                elif asset_liability <= 70:
                    scores.append(60)
                elif asset_liability <= 80:
                    scores.append(40)
                else:
                    scores.append(20)
            
            current_ratio = indicators.get('流动比率')
            if current_ratio is not None:
                if current_ratio >= 2.0:
                    scores.append(95)
                elif current_ratio >= 1.5:
                    scores.append(85)
                elif current_ratio >= 1.0:
                    scores.append(65)
                else:
                    scores.append(35)
        
        elif dimension == '运营风险':
            # 运营能力评分
            total_turnover = indicators.get('总资产周转率')
            if total_turnover is not None:
                if total_turnover >= 1.5:
                    scores.append(95)
                elif total_turnover >= 1.0:
                    scores.append(85)
                elif total_turnover >= 0.6:
                    scores.append(70)
                else:
                    scores.append(50)
            
            receivable_turnover = indicators.get('应收账款周转率')
            if receivable_turnover is not None:
                if receivable_turnover >= 8:
                    scores.append(95)
                elif receivable_turnover >= 5:
                    scores.append(80)
                elif receivable_turnover >= 3:
                    scores.append(60)
                else:
                    scores.append(40)
        
        elif dimension == '现金流风险':
            # 现金流评分
            operating_cf = indicators.get('经营性净现金流')
            if operating_cf is not None:
                if operating_cf >= 100000:  # 10万以上
                    scores.append(95)
                elif operating_cf >= 50000:  # 5万以上
                    scores.append(85)
                elif operating_cf >= 0:     # 正现金流
                    scores.append(65)
                elif operating_cf >= -50000: # 轻微负
                    scores.append(40)
                else:
                    scores.append(20)
            
            cash_flow_ratio = indicators.get('现金流量比率')
            if cash_flow_ratio is not None:
                if cash_flow_ratio >= 1.5:
                    scores.append(95)
                elif cash_flow_ratio >= 1.0:
                    scores.append(85)
                elif cash_flow_ratio >= 0.5:
                    scores.append(65)
                else:
                    scores.append(40)
        
        # 计算平均分
        if scores:
            return sum(scores) / len(scores)
        else:
            return None
    
    def _extract_risk_level_advanced(self, analysis_text: str) -> str:
        """从分析文本中提取风险等级（增强版本）"""
        import re
        
        # 方法1：优先匹配标准格式 "风险等级：XXX"
        match = re.search(r'风险等级[：:]\s*(低风险|中等风险|高风险)', analysis_text)
        if match:
            return match.group(1)
        
        # 方法2：匹配最后出现的风险等级
        risk_patterns = [
            (r'(低风险)(?!.*风险)', '低风险'),
            (r'(高风险)(?!.*风险)', '高风险'),
            (r'(中等风险)(?!.*风险)', '中等风险'),
        ]
        
        for pattern, level in risk_patterns:
            if re.search(pattern, analysis_text):
                return level
        
        # 方法3：简单包含匹配（优先级：高 > 低 > 中等）
        if '高风险' in analysis_text:
            return '高风险'
        elif '低风险' in analysis_text:
            return '低风险'
        elif '中等风险' in analysis_text:
            return '中等风险'
        
        # 默认返回中等风险
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



