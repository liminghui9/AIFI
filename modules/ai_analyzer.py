"""
AI分析模块
负责调用大语言模型进行风险分析和解读
"""

from openai import OpenAI
from typing import Dict, Optional, List
from config import Config

class AIAnalyzer:
    """AI风险分析器"""
    
    def __init__(self):
        """初始化AI分析器"""
        self.client = None
        if Config.OPENAI_API_KEY:
            self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_API_BASE
            )
        self.model = Config.OPENAI_MODEL
    
    def analyze_dimension_risk(self, 
                               dimension_name: str,
                               indicators: Dict[str, Optional[float]],
                               year_data: Dict[int, Dict[str, Optional[float]]],
                               company_info: Dict[str, any]) -> str:
        """
        分析特定维度的风险
        
        Args:
            dimension_name: 维度名称（盈利风险/偿债风险/运营风险/现金流风险）
            indicators: 当前年度指标数据
            year_data: 两年的指标数据（用于趋势分析）
            company_info: 企业基本信息
            
        Returns:
            str: 风险分析文本
        """
        # 如果API密钥未配置，返回默认分析
        if not Config.OPENAI_API_KEY:
            return self._get_default_analysis(dimension_name, indicators, year_data)
        
        try:
            # 构建提示词
            prompt = self._build_risk_analysis_prompt(
                dimension_name, indicators, year_data, company_info
            )
            
            # 调用OpenAI API（新版）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的财务分析师，擅长企业财务风险分析。请基于提供的财务数据，给出专业、客观的风险分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content.strip()
            return analysis
            
        except Exception as e:
            print(f"AI分析失败: {str(e)}")
            return self._get_default_analysis(dimension_name, indicators, year_data)
    
    def _build_risk_analysis_prompt(self,
                                    dimension_name: str,
                                    indicators: Dict[str, Optional[float]],
                                    year_data: Dict[int, Dict[str, Optional[float]]],
                                    company_info: Dict[str, any]) -> str:
        """构建风险分析提示词"""
        
        company_name = company_info.get('企业名称', '该企业')
        industry = company_info.get('行业类别', '相关行业')
        
        years = sorted(list(year_data.keys()), reverse=True)
        
        prompt = f"""请分析{company_name}的{dimension_name}状况。

企业基本信息：
- 企业名称：{company_name}
- 行业类别：{industry}

{dimension_name}核心指标：
"""
        
        # 添加指标数据
        for indicator_name, value in indicators.items():
            if value is not None:
                unit = '%' if indicator_name in ['净利润率', '毛利率', '净资产收益率', '资产负债率'] else ''
                prompt += f"- {indicator_name}：{value}{unit}\n"
            else:
                prompt += f"- {indicator_name}：数据缺失\n"
        
        # 添加趋势信息（如果有两年数据）
        if len(years) >= 2:
            prompt += f"\n年度对比（{years[0]} vs {years[1]}）：\n"
            for indicator_name in indicators.keys():
                val_new = year_data[years[0]].get(indicator_name)
                val_old = year_data[years[1]].get(indicator_name)
                if val_new is not None and val_old is not None:
                    change = val_new - val_old
                    trend = "上升" if change > 0 else "下降" if change < 0 else "持平"
                    prompt += f"- {indicator_name}：{trend}（{change:+.2f}）\n"
        
        prompt += f"""
请从以下角度进行分析：
1. 当前{dimension_name}水平评价（与行业标准对比）
2. 指标变化趋势及其含义
3. 潜在风险点识别
4. 简要建议

要求：
- 分析应专业、客观，控制在200字以内
- 如遇数据缺失，说明其影响
- 给出明确的风险等级判断（低风险/中等风险/高风险）
"""
        
        return prompt
    
    def _get_default_analysis(self,
                              dimension_name: str,
                              indicators: Dict[str, Optional[float]],
                              year_data: Dict[int, Dict[str, Optional[float]]]) -> str:
        """
        获取默认分析（当API不可用时）
        
        Args:
            dimension_name: 维度名称
            indicators: 指标数据
            year_data: 年度数据
            
        Returns:
            str: 默认分析文本
        """
        
        # 统计有效指标数量
        valid_count = sum(1 for v in indicators.values() if v is not None)
        total_count = len(indicators)
        
        if valid_count == 0:
            return f"【{dimension_name}分析】由于关键财务数据缺失，无法进行完整的{dimension_name}评估。建议补充相关财务数据后重新分析。风险等级：无法判断"
        
        # 基于指标值进行简单判断
        risk_level = "中等风险"
        analysis_points = []
        
        if dimension_name == "盈利风险":
            net_margin = indicators.get('净利润率')
            if net_margin is not None:
                if net_margin < 0:
                    risk_level = "高风险"
                    analysis_points.append("企业处于亏损状态")
                elif net_margin < 5:
                    risk_level = "中等风险"
                    analysis_points.append("净利润率较低，盈利能力有待提升")
                else:
                    risk_level = "低风险"
                    analysis_points.append("盈利能力表现良好")
        
        elif dimension_name == "偿债风险":
            asset_liability = indicators.get('资产负债率')
            if asset_liability is not None:
                if asset_liability > 70:
                    risk_level = "高风险"
                    analysis_points.append("资产负债率偏高，偿债压力较大")
                elif asset_liability > 50:
                    risk_level = "中等风险"
                    analysis_points.append("负债水平适中，需关注偿债能力")
                else:
                    risk_level = "低风险"
                    analysis_points.append("负债水平健康，偿债能力较强")
        
        elif dimension_name == "运营风险":
            total_turnover = indicators.get('总资产周转率')
            if total_turnover is not None:
                if total_turnover < 0.5:
                    risk_level = "中等风险"
                    analysis_points.append("资产周转效率有待提高")
                else:
                    risk_level = "低风险"
                    analysis_points.append("资产运营效率良好")
        
        elif dimension_name == "现金流风险":
            cash_profit = indicators.get('现金利润比')
            operating_cf = indicators.get('经营性净现金流')
            if operating_cf is not None and operating_cf < 0:
                risk_level = "高风险"
                analysis_points.append("经营活动现金流为负，资金压力较大")
            elif cash_profit is not None and cash_profit < 0.8:
                risk_level = "中等风险"
                analysis_points.append("现金回收能力需要改善")
            else:
                risk_level = "低风险"
                analysis_points.append("现金流状况稳健")
        
        # 构建分析文本
        analysis = f"【{dimension_name}分析】"
        if analysis_points:
            analysis += "，".join(analysis_points) + "。"
        else:
            analysis += f"基于现有数据，企业{dimension_name}水平处于行业中等水平。"
        
        analysis += f"建议持续关注相关指标变化趋势。风险等级：{risk_level}。"
        
        # 添加数据缺失提示
        if valid_count < total_count:
            analysis += f"（注：部分指标数据缺失，可能影响分析准确性）"
        
        return analysis
    
    def generate_overall_risk_assessment(self,
                                        dimension_analyses: Dict[str, str],
                                        all_indicators: Dict[str, Dict[str, Optional[float]]],
                                        company_info: Dict[str, any]) -> str:
        """
        生成整体风险评估
        
        Args:
            dimension_analyses: 各维度分析结果
            all_indicators: 所有维度的指标数据
            company_info: 企业基本信息
            
        Returns:
            str: 整体风险评估文本
        """
        
        if not Config.OPENAI_API_KEY:
            return self._get_default_overall_assessment(dimension_analyses)
        
        try:
            # 构建综合评估提示词
            prompt = f"""基于以下各维度的财务风险分析，请给出企业整体财务健康状况的综合评估。

企业名称：{company_info.get('企业名称', '该企业')}
行业类别：{company_info.get('行业类别', '相关行业')}

各维度分析结果：

"""
            for dimension, analysis in dimension_analyses.items():
                prompt += f"【{dimension}】\n{analysis}\n\n"
            
            prompt += """
请给出：
1. 整体财务健康状况评级（优秀/良好/一般/较差/风险较高）
2. 主要风险点总结（2-3点）
3. 核心优势（如有）
4. 整体建议

要求：分析应简洁明了，控制在300字以内。
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深的财务分析专家，擅长综合评估企业财务状况。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            assessment = response.choices[0].message.content.strip()
            return assessment
            
        except Exception as e:
            print(f"整体评估生成失败: {str(e)}")
            return self._get_default_overall_assessment(dimension_analyses)
    
    def _get_default_overall_assessment(self, dimension_analyses: Dict[str, str]) -> str:
        """生成默认的整体评估"""
        
        # 统计风险等级
        risk_counts = {'高风险': 0, '中等风险': 0, '低风险': 0}
        for analysis in dimension_analyses.values():
            if '高风险' in analysis:
                risk_counts['高风险'] += 1
            elif '低风险' in analysis:
                risk_counts['低风险'] += 1
            else:
                risk_counts['中等风险'] += 1
        
        # 判断整体风险水平
        if risk_counts['高风险'] >= 2:
            overall_level = "风险较高"
            conclusion = "企业存在多个高风险维度，需要重点关注和改善。"
        elif risk_counts['低风险'] >= 3:
            overall_level = "良好"
            conclusion = "企业整体财务状况健康，各项指标表现较好。"
        else:
            overall_level = "稳定"
            conclusion = "企业财务状况整体稳定，但仍有改善空间。"
        
        assessment = f"""【整体财务健康状况评估】

综合评级：{overall_level}

{conclusion}

主要发现：
"""
        
        # 提取各维度关键信息
        for dimension, analysis in dimension_analyses.items():
            if '高风险' in analysis:
                assessment += f"- {dimension}需要重点关注\n"
            elif '低风险' in analysis:
                assessment += f"- {dimension}表现良好\n"
        
        assessment += """
建议：
1. 定期监测财务指标变化趋势
2. 针对风险较高的维度制定改善措施
3. 保持良好的财务管理规范

（注：本评估基于简化模型，建议结合具体业务情况进行深入分析）
"""
        
        return assessment


