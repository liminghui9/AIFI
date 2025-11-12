"""
ECharts图表生成器
使用ECharts替代Plotly，解决图例显示和布局问题
"""
import json
from typing import Dict, List, Tuple
from datetime import datetime
import os


class EChartsGenerator:
    """使用ECharts生成财务分析图表"""
    
    def __init__(self, charts_folder: str = 'static/charts'):
        """
        初始化ECharts生成器
        
        Args:
            charts_folder: 图表文件保存目录
        """
        self.charts_folder = charts_folder
        os.makedirs(charts_folder, exist_ok=True)
        
        # 统一的颜色方案
        self.color_palette = [
            '#3b82f6',  # 蓝色
            '#ef4444',  # 红色
            '#10b981',  # 绿色
            '#f59e0b',  # 橙色
            '#8b5cf6',  # 紫色
            '#ec4899',  # 粉色
            '#14b8a6',  # 青色
        ]
    
    def generate_all_charts(self, years: List[int], indicators: Dict, 
                          dimension_analyses: Dict) -> Dict[str, str]:
        """
        生成所有图表
        
        Args:
            years: 年份列表
            indicators: 财务指标数据
            dimension_analyses: 维度分析数据
            
        Returns:
            Dict[str, str]: 图表ID到配置的映射
        """
        charts = {}
        
        try:
            # 1. 主要财务指标
            charts['main_indicators'] = self._generate_main_indicators_chart(years, indicators)
            
            # 2. 盈利能力
            charts['profitability'] = self._generate_profitability_chart(years, indicators)
            
            # 3. 偿债能力
            charts['solvency'] = self._generate_solvency_chart(years, indicators)
            
            # 4. 运营能力
            charts['operational'] = self._generate_operational_chart(years, indicators)
            
            # 5. 现金流
            charts['cashflow'] = self._generate_cashflow_chart(years, indicators)
            
            # 6. 风险雷达图
            charts['risk_radar'] = self._generate_risk_radar_chart(dimension_analyses)
            
            # 7. 健康度仪表盘
            charts['health_dashboard'] = self._generate_health_dashboard(indicators, dimension_analyses)
            
        except Exception as e:
            print(f"生成图表时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return charts
    
    def _generate_profitability_chart(self, years: List[int], indicators: Dict) -> str:
        """生成盈利能力趋势图"""
        # 准备数据
        metrics = {
            '销售净利率': [],
            '毛利率': [],
            '净资产收益率': []
        }
        
        for year in years:
            # 尝试整数和字符串两种键
            profitability_data = indicators.get(year, indicators.get(str(year), {})).get('盈利风险', {})
            for metric in metrics.keys():
                metrics[metric].append(profitability_data.get(metric, 0))
        
        # ECharts配置
        option = {
            'title': {
                'text': '盈利能力趋势分析',
                'left': 'center',
                'textStyle': {
                    'fontSize': 18,
                    'fontWeight': 'bold',
                    'color': '#1e3a8a'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross'
                }
            },
            'legend': {
                'data': list(metrics.keys()),
                'bottom': 10,
                'left': 'center',
                'textStyle': {
                    'fontSize': 12
                }
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '15%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': [str(y) + '年' for y in years],
                'name': '年份',
                'nameTextStyle': {
                    'fontWeight': 'bold'
                }
            },
            'yAxis': {
                'type': 'value',
                'name': '比率 (%)',
                'nameTextStyle': {
                    'fontWeight': 'bold'
                }
            },
            'series': [
                {
                    'name': metric,
                    'type': 'line',
                    'smooth': True,
                    'data': values,
                    'lineStyle': {
                        'width': 3
                    },
                    'itemStyle': {
                        'color': self.color_palette[i]
                    },
                    'areaStyle': {
                        'opacity': 0.1
                    },
                    'emphasis': {
                        'focus': 'series'
                    }
                }
                for i, (metric, values) in enumerate(metrics.items())
            ],
            'color': self.color_palette
        }
        
        return json.dumps(option, ensure_ascii=False)
    
    def _generate_solvency_chart(self, years: List[int], indicators: Dict) -> str:
        """生成偿债能力分析图"""
        # 准备数据
        current_ratios = []
        quick_ratios = []
        asset_liability_ratios = []
        
        for year in years:
            solvency_data = indicators.get(year, indicators.get(str(year), {})).get('偿债风险', {})
            current_ratios.append(solvency_data.get('流动比率', 0))
            quick_ratios.append(solvency_data.get('速动比率', 0))
            asset_liability_ratios.append(solvency_data.get('资产负债率', 0))
        
        option = {
            'title': {
                'text': '偿债能力分析',
                'left': 'center',
                'textStyle': {
                    'fontSize': 18,
                    'fontWeight': 'bold',
                    'color': '#1e3a8a'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'shadow'
                }
            },
            'legend': {
                'data': ['流动比率', '速动比率', '资产负债率(%)'],
                'bottom': 10,
                'left': 'center'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '15%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': [str(y) + '年' for y in years],
                'name': '年份'
            },
            'yAxis': {
                'type': 'value',
                'name': '比率'
            },
            'series': [
                {
                    'name': '流动比率',
                    'type': 'bar',
                    'data': current_ratios,
                    'itemStyle': {'color': self.color_palette[0]},
                    'markLine': {
                        'data': [
                            {
                                'yAxis': 2.0,
                                'name': '安全线',
                                'lineStyle': {'color': '#10b981', 'type': 'dashed'},
                                'label': {'formatter': '安全线(2.0)'}
                            }
                        ]
                    }
                },
                {
                    'name': '速动比率',
                    'type': 'bar',
                    'data': quick_ratios,
                    'itemStyle': {'color': self.color_palette[1]}
                },
                {
                    'name': '资产负债率(%)',
                    'type': 'bar',
                    'data': asset_liability_ratios,
                    'itemStyle': {'color': self.color_palette[2]},
                    'markLine': {
                        'data': [
                            {
                                'yAxis': 70,
                                'name': '警戒线',
                                'lineStyle': {'color': '#ef4444', 'type': 'dashed'},
                                'label': {'formatter': '警戒线(70%)'}
                            }
                        ]
                    }
                }
            ],
            'color': self.color_palette
        }
        
        return json.dumps(option, ensure_ascii=False)
    
    def _generate_operational_chart(self, years: List[int], indicators: Dict) -> str:
        """生成运营能力分析图"""
        metrics = {
            '应收账款周转率': [],
            '存货周转率': [],
            '总资产周转率': []
        }
        
        for year in years:
            operational_data = indicators.get(year, indicators.get(str(year), {})).get('运营风险', {})
            for metric in metrics.keys():
                metrics[metric].append(operational_data.get(metric, 0))
        
        option = {
            'title': {
                'text': '运营能力分析',
                'left': 'center',
                'textStyle': {
                    'fontSize': 18,
                    'fontWeight': 'bold',
                    'color': '#1e3a8a'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'shadow'
                }
            },
            'legend': {
                'data': list(metrics.keys()),
                'bottom': 10,
                'left': 'center'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '15%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': [str(y) + '年' for y in years],
                'name': '年份'
            },
            'yAxis': {
                'type': 'value',
                'name': '周转率 (次)'
            },
            'series': [
                {
                    'name': metric,
                    'type': 'bar',
                    'data': values,
                    'itemStyle': {'color': self.color_palette[i]},
                    'label': {
                        'show': True,
                        'position': 'top',
                        'formatter': '{c}'
                    }
                }
                for i, (metric, values) in enumerate(metrics.items())
            ],
            'color': self.color_palette
        }
        
        return json.dumps(option, ensure_ascii=False)
    
    def _generate_cashflow_chart(self, years: List[int], indicators: Dict) -> str:
        """生成现金流状况分析图"""
        operating_cashflow = []
        cash_profit_ratio = []
        
        for year in years:
            cashflow_data = indicators.get(year, indicators.get(str(year), {})).get('现金流风险', {})
            operating_cashflow.append(cashflow_data.get('经营性净现金流', 0))
            cash_profit_ratio.append(cashflow_data.get('现金利润比', 0))
        
        option = {
            'title': {
                'text': '现金流状况分析',
                'left': 'center',
                'textStyle': {
                    'fontSize': 18,
                    'fontWeight': 'bold',
                    'color': '#1e3a8a'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross'
                }
            },
            'legend': {
                'data': ['经营性净现金流', '现金利润比'],
                'bottom': 10,
                'left': 'center'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '15%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': [str(y) + '年' for y in years],
                'name': '年份'
            },
            'yAxis': [
                {
                    'type': 'value',
                    'name': '现金流(万元)',
                    'position': 'left'
                },
                {
                    'type': 'value',
                    'name': '现金利润比',
                    'position': 'right'
                }
            ],
            'series': [
                {
                    'name': '经营性净现金流',
                    'type': 'bar',
                    'data': operating_cashflow,
                    'itemStyle': {'color': self.color_palette[0]},
                    'yAxisIndex': 0
                },
                {
                    'name': '现金利润比',
                    'type': 'line',
                    'data': cash_profit_ratio,
                    'itemStyle': {'color': self.color_palette[1]},
                    'yAxisIndex': 1,
                    'smooth': True,
                    'lineStyle': {
                        'width': 3
                    }
                }
            ],
            'color': self.color_palette
        }
        
        return json.dumps(option, ensure_ascii=False)
    
    def _generate_risk_radar_chart(self, dimension_analyses: Dict) -> str:
        """生成风险评估雷达图"""
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        risk_scores = []
        
        for dimension in dimensions:
            analysis_text = dimension_analyses.get(dimension, '')
            
            # 从分析文字中提取风险等级
            risk_level = '中等风险'
            if '高风险' in analysis_text:
                risk_level = '高风险'
            elif '低风险' in analysis_text:
                risk_level = '低风险'
            elif '中等风险' in analysis_text:
                risk_level = '中等风险'
            
            # 风险等级转分数 (分数越高风险越低)
            score_map = {'低风险': 90, '中等风险': 60, '高风险': 30}
            risk_scores.append(score_map.get(risk_level, 60))
        
        option = {
            'title': {
                'text': '财务风险评估雷达图',
                'left': 'center',
                'textStyle': {
                    'fontSize': 18,
                    'fontWeight': 'bold',
                    'color': '#1e3a8a'
                }
            },
            'tooltip': {
                'trigger': 'item'
            },
            'radar': {
                'indicator': [
                    {'name': dim, 'max': 100} for dim in dimensions
                ],
                'shape': 'polygon',
                'splitNumber': 3,
                'name': {
                    'textStyle': {
                        'color': '#1e293b',
                        'fontSize': 13,
                        'fontWeight': 'bold'
                    }
                },
                'splitLine': {
                    'lineStyle': {
                        'color': '#e2e8f0'
                    }
                },
                'splitArea': {
                    'areaStyle': {
                        'color': ['#fafbfc', '#f1f5f9']
                    }
                },
                'axisLine': {
                    'lineStyle': {
                        'color': '#cbd5e1'
                    }
                }
            },
            'series': [
                {
                    'name': '风险评估',
                    'type': 'radar',
                    'data': [
                        {
                            'value': risk_scores,
                            'name': '风险评估',
                            'areaStyle': {
                                'opacity': 0.25,
                                'color': '#3b82f6'
                            },
                            'lineStyle': {
                                'color': '#3b82f6',
                                'width': 3
                            },
                            'itemStyle': {
                                'color': '#3b82f6'
                            }
                        }
                    ]
                }
            ]
        }
        
        return json.dumps(option, ensure_ascii=False)
    
    def _generate_health_dashboard(self, indicators: Dict, dimension_analyses: Dict) -> str:
        """生成财务健康度仪表盘"""
        dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
        dimension_names = ['盈利能力', '偿债能力', '运营能力', '现金流状况']
        
        # 计算各维度健康度分数
        scores = []
        for dimension in dimensions:
            analysis_text = dimension_analyses.get(dimension, '')
            
            risk_level = '中等风险'
            if '高风险' in analysis_text:
                risk_level = '高风险'
            elif '低风险' in analysis_text:
                risk_level = '低风险'
            
            score_map = {'低风险': 85, '中等风险': 60, '高风险': 35}
            scores.append(score_map.get(risk_level, 60))
        
        # 创建4个仪表盘
        series = []
        for i, (name, score) in enumerate(zip(dimension_names, scores)):
            # 确定颜色
            if score >= 70:
                color = [[1, '#10b981']]  # 绿色
            elif score >= 40:
                color = [[1, '#f59e0b']]  # 橙色
            else:
                color = [[1, '#ef4444']]  # 红色
            
            # 计算位置（2x2网格）
            row = i // 2
            col = i % 2
            center_x = f'{25 + col * 50}%'
            center_y = f'{30 + row * 40}%'
            
            series.append({
                'name': name,
                'type': 'gauge',
                'center': [center_x, center_y],
                'radius': '35%',
                'startAngle': 200,
                'endAngle': -20,
                'min': 0,
                'max': 100,
                'splitNumber': 5,
                'itemStyle': {
                    'color': color[0][1]
                },
                'progress': {
                    'show': True,
                    'width': 15
                },
                'pointer': {
                    'show': False
                },
                'axisLine': {
                    'lineStyle': {
                        'width': 15,
                        'color': [[1, '#e2e8f0']]
                    }
                },
                'axisTick': {
                    'show': False
                },
                'splitLine': {
                    'show': False
                },
                'axisLabel': {
                    'show': False
                },
                'detail': {
                    'valueAnimation': True,
                    'formatter': '{value}',
                    'color': '#1e293b',
                    'fontSize': 32,
                    'fontWeight': 'bold',
                    'offsetCenter': [0, '-10%']
                },
                'title': {
                    'show': True,
                    'offsetCenter': [0, '75%'],
                    'fontSize': 16,
                    'color': '#1e3a8a',
                    'fontWeight': 'bold'
                },
                'data': [{'value': score, 'name': name}]
            })
        
        option = {
            'series': series
        }
        
        return json.dumps(option, ensure_ascii=False)
    
    def _generate_main_indicators_chart(self, years: List[int], indicators: Dict) -> str:
        """生成主要财务指标对比图"""
        # 数据准备
        revenue_data = []
        profit_data = []
        asset_liability_ratio = []
        roe_data = []
        current_ratio = []
        
        for year in years:
            year_indicators = indicators.get(year, indicators.get(str(year), {}))
            revenue_data.append(year_indicators.get('营业收入', 0))
            profit_data.append(year_indicators.get('净利润', 0))
            
            profitability = year_indicators.get('盈利风险', {})
            solvency = year_indicators.get('偿债风险', {})
            
            asset_liability_ratio.append(solvency.get('资产负债率', 0))
            roe_data.append(profitability.get('净资产收益率', 0))
            current_ratio.append(solvency.get('流动比率', 0))
        
        option = {
            'title': {
                'text': '主要财务指标分析',
                'left': 'center',
                'textStyle': {
                    'fontSize': 18,
                    'fontWeight': 'bold',
                    'color': '#1e3a8a'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross'
                }
            },
            'legend': {
                'data': ['营业收入', '净利润', '资产负债率(%)', '净资产收益率(%)', '流动比率'],
                'bottom': 10,
                'left': 'center'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '15%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': [str(y) + '年' for y in years],
                'name': '年份'
            },
            'yAxis': {
                'type': 'value',
                'name': '数值'
            },
            'series': [
                {
                    'name': '营业收入',
                    'type': 'bar',
                    'data': revenue_data,
                    'itemStyle': {'color': self.color_palette[0]}
                },
                {
                    'name': '净利润',
                    'type': 'line',
                    'data': profit_data,
                    'itemStyle': {'color': self.color_palette[1]},
                    'smooth': True
                },
                {
                    'name': '资产负债率(%)',
                    'type': 'bar',
                    'data': asset_liability_ratio,
                    'itemStyle': {'color': self.color_palette[2]}
                },
                {
                    'name': '净资产收益率(%)',
                    'type': 'line',
                    'data': roe_data,
                    'itemStyle': {'color': self.color_palette[3]},
                    'smooth': True
                },
                {
                    'name': '流动比率',
                    'type': 'bar',
                    'data': current_ratio,
                    'itemStyle': {'color': self.color_palette[4]}
                }
            ],
            'color': self.color_palette
        }
        
        return json.dumps(option, ensure_ascii=False)

