"""
AI分析模块
负责调用大语言模型进行风险分析和解读
"""

from openai import OpenAI
from typing import Dict, Optional, List
from config import Config

class AIAnalyzer:
    """AI风险分析器"""
    
    def __init__(self, model: str = None):
        """
        初始化AI分析器
        
        Args:
            model: 指定使用的AI模型，如果为None则使用配置文件中的默认模型
        """
        self.client = None
        if Config.OPENAI_API_KEY:
            self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_API_BASE
            )
        # 使用传入的模型或配置文件中的默认模型
        self.model = model if model else Config.OPENAI_MODEL
        print(f"✓ AI分析器初始化，使用模型: {self.model}")
    
    def _clean_markdown(self, text: str) -> str:
        """
        清理文本中的Markdown格式标记
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        import re
        
        # 移除加粗标记 **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        
        # 移除斜体标记 *text* 或 _text_
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 移除标题标记 # ## ###
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # 移除代码块标记 ```
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 移除链接 [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        return text.strip()
    
    def _format_analysis_text(self, text: str) -> str:
        """
        格式化AI分析文本，添加段落分隔和层次，并高亮重要数据
        
        Args:
            text: 原始分析文本
            
        Returns:
            str: 格式化后的文本（包含HTML标记）
        """
        import re
        
        # 先清理Markdown
        text = self._clean_markdown(text)
        
        # 1. 高亮百分比数据（加粗显红）
        # 匹配如：22.15%、-5.3%、10%等
        text = re.sub(
            r'([-+]?\d+\.?\d*%)',
            r'<span class="highlight-number">\1</span>',
            text
        )
        
        # 2. 高亮货币金额（加粗显红）
        # 匹配如：28000.00万元、1000万元、5000.5万元等
        text = re.sub(
            r'(\d+\.?\d*万元)',
            r'<span class="highlight-number">\1</span>',
            text
        )
        
        # 3. 高亮倍数/比率（加粗显红）
        # 匹配如：1.56倍、2.98倍、1.43倍等
        text = re.sub(
            r'(\d+\.?\d*倍)',
            r'<span class="highlight-number">\1</span>',
            text
        )
        
        # 4. 高亮年份数据对比
        # 匹配如：2023年、2022年
        text = re.sub(
            r'(20\d{2}年)',
            r'<strong>\1</strong>',
            text
        )
        
        # 5. 高亮风险等级关键词
        # 高风险 - 红色加粗
        text = re.sub(
            r'(高风险|严重|显著下降|大幅下降|明显恶化)',
            r'<span class="risk-high">\1</span>',
            text
        )
        
        # 中等风险 - 橙色加粗
        text = re.sub(
            r'(中等风险|需关注|有所下降|略有下降)',
            r'<span class="risk-medium">\1</span>',
            text
        )
        
        # 低风险/良好 - 绿色加粗
        text = re.sub(
            r'(低风险|良好|优秀|显著提升|大幅提升|明显改善|表现良好)',
            r'<span class="risk-low">\1</span>',
            text
        )
        
        # 6. 格式化段落和换行
        # 只在句号后换行，但要保留完整句子
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            # 在句号后添加换行，但保持在同一个段落内的紧凑性
            line = re.sub(r'([。])(?!\s*$)', r'\1<br>', line)
            if line.strip():
                formatted_lines.append(line.strip())
        
        text = '\n'.join(formatted_lines)
        
        # 7. 处理列表项前添加段落间隔
        text = re.sub(r'(?<=[。])\s*(?=[-–—])', '<br>', text)
        
        # 8. 移除多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 9. 移除开头和结尾的空白
        return text.strip()
    
    def _strip_html_tags(self, text: str) -> str:
        """
        移除文本中的HTML标签，用于PDF等纯文本输出
        
        Args:
            text: 包含HTML标签的文本
            
        Returns:
            str: 纯文本（移除所有HTML标签）
        """
        import re
        
        # 先将<br>转换为换行（在移除其他标签之前）
        text = re.sub(r'<br\s*/?>', '\n', text)
        
        # 移除所有HTML标签（包括span, strong等）
        text = re.sub(r'<[^>]+>', '', text)
        
        # 清理多余的空白和换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'  +', ' ', text)  # 多个空格替换为单个空格
        
        return text.strip()
    
    def format_for_pdf(self, text: str) -> str:
        """
        格式化文本用于PDF输出（纯文本，无HTML标签）
        
        Args:
            text: 原始或带HTML标签的文本
            
        Returns:
            str: 适合PDF显示的纯文本
        """
        # 如果文本中包含HTML标签，先移除
        if '<' in text and '>' in text:
            text = self._strip_html_tags(text)
        
        # 确保换行格式正确
        text = text.replace('<br>', '\n')
        
        return text
    
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
            # 格式化分析文本（包含清理Markdown）
            analysis = self._format_analysis_text(analysis)
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
请从以下角度进行分析，并在分析中引用具体的指标数值：

1. 当前{dimension_name}水平评价：
   - 必须引用上述具体指标值进行说明
   - 与{industry}行业标准对比（如：净利润率9.00%，略低于行业平均水平10%）

2. 指标变化趋势及其含义：
   - 引用具体数值变化（如：净利润率从8.57%上升至9.00%，上升0.43个百分点）
   - 说明变化的业务含义

3. 潜在风险点识别：
   - 用数据说明风险点（如：资产负债率达XX%，超出安全线XX%）
   - 量化风险程度

4. 简要建议：
   - 每条建议单独一行
   - 针对具体指标给出可操作建议
   - 格式：每条建议另起一行，用"；"或换行分隔

输出格式要求：
- 纯文本格式，不使用Markdown标记（不要用**、#、-、*等符号）
- 建议部分每条另起一行
- 必须引用具体数值，避免空泛描述
- 最后给出风险等级（低风险/中等风险/高风险）
- 控制在300字以内
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
                                        all_indicators: Dict[str, Dict],
                                        company_info: Dict[str, str]) -> str:
        """
        生成整体风险评估
        
        Args:
            dimension_analyses: 各维度风险分析
            all_indicators: 所有维度的指标数据
            company_info: 企业基本信息
            
        Returns:
            str: 整体风险评估文本
        """
        
        if not Config.OPENAI_API_KEY:
            return self._get_default_overall_assessment(dimension_analyses, all_indicators, company_info)
        
        try:
            # 提取关键财务指标数据
            key_indicators_text = self._format_key_indicators(all_indicators)
            
            # 构建综合评估提示词
            prompt = f"""基于以下财务数据和各维度分析，请给出企业整体财务健康状况的综合评估。

【企业基本信息】
企业名称：{company_info.get('企业名称', '该企业')}
行业类别：{company_info.get('行业类别', '相关行业')}
统一社会信用代码：{company_info.get('统一社会信用代码', '未提供')}

【关键财务指标】
{key_indicators_text}

【各维度风险分析】
"""
            for dimension, analysis in dimension_analyses.items():
                prompt += f"{dimension}：\n{analysis}\n\n"
            
            prompt += """
请结合以上具体数据，给出详细的综合评估：

1. 整体财务健康状况评级：良好/一般/较差
理由：必须引用3-5个关键指标的具体数值来支撑评级（如：净利润率9.00%，资产负债率XX%，流动比率XX等）

2. 主要风险点总结：
必须列举3-4个具体风险点，每个风险点要：
- 指出具体指标和数值
- 说明偏离标准的程度
- 每个风险点单独一行
示例格式：
盈利能力受行业竞争影响，净利润率9.00%低于行业平均10%，需关注利润率波动；
资产负债率XX%高于行业平均水平XX%，需加强长期偿债能力；
运营效率下降，应收账款周转率从XX降至XX，需优化库存管理。

3. 核心优势：
列举2-3个优势指标（如有），每个优势单独一行：
- 引用具体数值
- 与行业对比
示例：净资产收益率22.50%表现良好，高于行业平均15%；短期偿债能力较强，流动比率XX高于行业标准。

4. 整体建议：
给出3-5条可操作建议，每条建议必须：
- 单独一行
- 针对具体指标
- 可量化、可执行
示例格式：
关注行业竞争，优化成本控制，力争将净利润率提升至10%以上；
加强应收账款管理，将应收账款周转率从XX提升至行业平均XX；
优化负债结构，降低资产负债率至60%以下。

输出格式要求：
- 纯文本，不使用Markdown标记（不要用**、#、-、*等符号）
- 所有要点必须引用具体数值
- 风险点和建议各占一行，用"；"或换行分隔
- 控制在600字以内
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深的财务分析专家，擅长综合评估企业财务状况，并善于用具体数据支撑分析结论。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200  # 增加token限制以支持更详细的分析
            )
            
            assessment = response.choices[0].message.content.strip()
            # 格式化评估文本（包含清理Markdown）
            assessment = self._format_analysis_text(assessment)
            return assessment
            
        except Exception as e:
            print(f"整体评估生成失败: {str(e)}")
            return self._get_default_overall_assessment(dimension_analyses, all_indicators, company_info)
    
    def _format_key_indicators(self, all_indicators: Dict[str, Dict]) -> str:
        """格式化关键财务指标为文本"""
        if not all_indicators:
            return "暂无指标数据"
        
        # 获取最新年度
        latest_year = max(all_indicators.keys())
        indicators_by_dim = all_indicators[latest_year]
        
        text = f"【{latest_year}年度】\n\n"
        
        # 盈利能力
        if '盈利风险' in indicators_by_dim:
            text += "盈利能力：\n"
            for name, value in indicators_by_dim['盈利风险'].items():
                if value is not None:
                    if name in ['净利润率', '毛利率', '净资产收益率', '总资产报酬率']:
                        text += f"  • {name}: {value:.2f}%\n"
                    elif name in ['营业收入增长率', '净利润增长率']:
                        text += f"  • {name}: {value:+.2f}%\n"
                    else:
                        text += f"  • {name}: {value:.2f}\n"
            text += "\n"
        
        # 偿债能力
        if '偿债风险' in indicators_by_dim:
            text += "偿债能力：\n"
            for name, value in indicators_by_dim['偿债风险'].items():
                if value is not None:
                    if name == '资产负债率':
                        text += f"  • {name}: {value:.2f}%\n"
                    else:
                        text += f"  • {name}: {value:.2f}\n"
            text += "\n"
        
        # 运营能力
        if '运营风险' in indicators_by_dim:
            text += "运营能力：\n"
            for name, value in indicators_by_dim['运营风险'].items():
                if value is not None:
                    if name == '营业周期':
                        text += f"  • {name}: {value:.0f}天\n"
                    else:
                        text += f"  • {name}: {value:.2f}\n"
            text += "\n"
        
        # 现金流状况
        if '现金流风险' in indicators_by_dim:
            text += "现金流状况：\n"
            for name, value in indicators_by_dim['现金流风险'].items():
                if value is not None:
                    if name in ['经营性净现金流', '现金净增加额']:
                        text += f"  • {name}: {value:,.2f}万元\n"
                    else:
                        text += f"  • {name}: {value:.2f}\n"
        
        return text
    
    def _get_default_overall_assessment(self, dimension_analyses: Dict[str, str], 
                                       all_indicators: Dict[str, Dict] = None,
                                       company_info: Dict[str, str] = None) -> str:
        """生成默认的整体评估（结合具体数据）"""
        
        company_name = company_info.get('企业名称', '该企业') if company_info else '该企业'
        
        # 统计风险等级
        risk_counts = {'高风险': 0, '中等风险': 0, '低风险': 0}
        risk_details = {'高风险': [], '低风险': []}
        
        for dimension, analysis in dimension_analyses.items():
            if '高风险' in analysis:
                risk_counts['高风险'] += 1
                risk_details['高风险'].append(dimension)
            elif '低风险' in analysis:
                risk_counts['低风险'] += 1
                risk_details['低风险'].append(dimension)
            else:
                risk_counts['中等风险'] += 1
        
        # 判断整体风险水平
        if risk_counts['高风险'] >= 2:
            overall_level = "风险较高 ⚠️"
            conclusion = f"{company_name}存在{risk_counts['高风险']}个高风险维度，财务状况需要重点关注和改善。"
        elif risk_counts['低风险'] >= 3:
            overall_level = "良好 ✓"
            conclusion = f"{company_name}整体财务状况健康，{risk_counts['低风险']}个维度表现优异。"
        else:
            overall_level = "稳定 ○"
            conclusion = f"{company_name}财务状况整体稳定，但存在{risk_counts['中等风险']}个维度需要改善。"
        
        # 提取关键指标数据
        key_data = ""
        if all_indicators:
            latest_year = max(all_indicators.keys())
            indicators_by_dim = all_indicators[latest_year]
            
            # 提取最关键的几个指标
            if '盈利风险' in indicators_by_dim:
                net_margin = indicators_by_dim['盈利风险'].get('净利润率')
                if net_margin is not None:
                    key_data += f"\n• 净利润率：{net_margin:.2f}%"
            
            if '偿债风险' in indicators_by_dim:
                asset_liability = indicators_by_dim['偿债风险'].get('资产负债率')
                if asset_liability is not None:
                    key_data += f"\n• 资产负债率：{asset_liability:.2f}%"
            
            if '运营风险' in indicators_by_dim:
                total_turnover = indicators_by_dim['运营风险'].get('总资产周转率')
                if total_turnover is not None:
                    key_data += f"\n• 总资产周转率：{total_turnover:.2f}"
            
            if '现金流风险' in indicators_by_dim:
                operating_cf = indicators_by_dim['现金流风险'].get('经营性净现金流')
                if operating_cf is not None:
                    key_data += f"\n• 经营性净现金流：{operating_cf:,.2f}万元"
        
        assessment = f"""【整体财务健康状况评估】

📊 综合评级：{overall_level}

{conclusion}
{key_data}

🔍 主要风险点：
"""
        
        # 详细列出风险点
        if risk_details['高风险']:
            for dimension in risk_details['高风险']:
                assessment += f"• {dimension}：需要立即采取改善措施\n"
        else:
            assessment += "• 暂无重大风险点\n"
        
        assessment += "\n✨ 核心优势：\n"
        if risk_details['低风险']:
            for dimension in risk_details['低风险']:
                assessment += f"• {dimension}：表现优异，保持当前水平\n"
        else:
            assessment += "• 各维度处于稳定状态\n"
        
        assessment += """
💡 战略建议：
1. 定期监测财务指标变化趋势，建立预警机制
2. 针对高风险维度制定针对性改善计划
3. 优化资本结构，提升资金使用效率
4. 加强财务管理规范，保持稳健经营

（注：本评估基于简化模型，建议结合具体业务情况进行深入分析）
"""
        
        return assessment
    
    def answer_question(self,
                       question: str,
                       report_data: Dict,
                       company_info: Dict[str, any]) -> str:
        """
        回答用户关于财务报告的问题
        
        Args:
            question: 用户的问题
            report_data: 完整的报告数据
            company_info: 企业基本信息
            
        Returns:
            str: AI的回答
        """
        
        if not Config.OPENAI_API_KEY:
            return self._get_default_answer(question, report_data, company_info)
        
        try:
            # 构建上下文信息
            context = self._build_report_context(report_data, company_info)
            
            # 构建提示词
            prompt = f"""你是一位专业的财务分析师助手，现在需要回答用户关于以下财务报告的问题。

企业基本信息：
{context['basic_info']}

总体风险评估：
{context['overall_assessment']}

各维度风险分析：
{context['dimension_analyses']}

主要财务指标：
{context['key_indicators']}

用户问题：{question}

请基于报告数据给出专业、准确的回答。要求：
1. 回答要简洁明了，突出重点
2. 如果问题涉及具体数据，请引用报告中的实际数据
3. 保持专业的财务分析语气
4. 如果报告中没有相关信息，请说明无法从当前报告获取该信息
5. 控制在200字以内
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的财务分析师助手，擅长解读财务报告和回答财务相关问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            print(f"AI回答问题失败: {str(e)}")
            return self._get_default_answer(question, report_data, company_info)
    
    def _build_report_context(self, report_data: Dict, company_info: Dict[str, any]) -> Dict[str, str]:
        """构建报告上下文信息"""
        
        context = {}
        
        # 基本信息
        basic_info = []
        for key, value in company_info.items():
            basic_info.append(f"- {key}: {value}")
        context['basic_info'] = '\n'.join(basic_info)
        
        # 总体评估
        context['overall_assessment'] = report_data.get('overall_assessment', '暂无总体评估')
        
        # 各维度分析
        dimension_analyses = []
        for dimension, analysis in report_data.get('dimension_analyses', {}).items():
            dimension_analyses.append(f"【{dimension}】\n{analysis}")
        context['dimension_analyses'] = '\n\n'.join(dimension_analyses)
        
        # 主要指标
        indicators_info = []
        years = report_data.get('years', [])
        if years:
            current_year = years[0]
            all_indicators = report_data.get('indicators', {}).get(current_year, {})
            
            for dimension, indicators in all_indicators.items():
                indicators_info.append(f"\n{dimension}:")
                for indicator_name, value in indicators.items():
                    if value is not None:
                        unit = '%' if indicator_name in ['净利润率', '毛利率', '净资产收益率', '资产负债率'] else ''
                        if indicator_name in ['经营性净现金流', '现金净增加额']:
                            indicators_info.append(f"  - {indicator_name}: {value:,.2f} 万元")
                        else:
                            indicators_info.append(f"  - {indicator_name}: {value:.2f}{unit}")
                    else:
                        indicators_info.append(f"  - {indicator_name}: 数据缺失")
        
        context['key_indicators'] = '\n'.join(indicators_info) if indicators_info else '暂无指标数据'
        
        return context
    
    def _get_default_answer(self, question: str, report_data: Dict, company_info: Dict[str, any]) -> str:
        """生成默认答案（当API不可用时）"""
        
        question_lower = question.lower()
        
        # 根据关键词匹配回答
        if any(keyword in question_lower for keyword in ['风险', '问题', '隐患']):
            # 风险相关问题
            dimension_analyses = report_data.get('dimension_analyses', {})
            high_risk_areas = []
            for dimension, analysis in dimension_analyses.items():
                if '高风险' in analysis or '较差' in analysis:
                    high_risk_areas.append(dimension)
            
            if high_risk_areas:
                return f"根据报告分析，该企业的主要风险集中在：{' 、'.join(high_risk_areas)}。建议重点关注这些领域，采取针对性的改善措施。详细分析请查看报告中各维度的具体评估。"
            else:
                return "根据报告分析，该企业整体财务风险在可控范围内。建议继续保持良好的财务管理，定期监测各项指标变化。"
        
        elif any(keyword in question_lower for keyword in ['盈利', '利润', '赚钱']):
            # 盈利能力相关问题
            years = report_data.get('years', [])
            if years:
                current_year = years[0]
                indicators = report_data.get('indicators', {}).get(current_year, {}).get('盈利风险', {})
                net_margin = indicators.get('净利润率')
                
                if net_margin is not None:
                    if net_margin < 0:
                        return f"该企业{current_year}年净利润率为{net_margin:.2f}%，处于亏损状态。建议深入分析亏损原因，优化成本结构，提升盈利能力。"
                    elif net_margin < 5:
                        return f"该企业{current_year}年净利润率为{net_margin:.2f}%，盈利能力偏弱。建议关注成本控制和收入增长策略。"
                    else:
                        return f"该企业{current_year}年净利润率为{net_margin:.2f}%，盈利能力表现良好。建议继续保持优势，并寻找新的增长点。"
            
            return "盈利能力相关的详细分析请查看报告中的盈利风险维度部分。"
        
        elif any(keyword in question_lower for keyword in ['现金流', '资金', '流动性']):
            # 现金流相关问题
            years = report_data.get('years', [])
            if years:
                current_year = years[0]
                indicators = report_data.get('indicators', {}).get(current_year, {}).get('现金流风险', {})
                operating_cf = indicators.get('经营性净现金流')
                
                if operating_cf is not None:
                    if operating_cf < 0:
                        return f"该企业{current_year}年经营性净现金流为{operating_cf:,.2f}万元，为负值，存在资金压力。建议优化应收账款管理，加快资金回笼。"
                    else:
                        return f"该企业{current_year}年经营性净现金流为{operating_cf:,.2f}万元，现金流状况整体稳健。建议继续保持良好的资金管理。"
            
            return "现金流相关的详细分析请查看报告中的现金流风险维度部分。"
        
        elif any(keyword in question_lower for keyword in ['偿债', '负债', '还款']):
            # 偿债能力相关问题
            years = report_data.get('years', [])
            if years:
                current_year = years[0]
                indicators = report_data.get('indicators', {}).get(current_year, {}).get('偿债风险', {})
                asset_liability = indicators.get('资产负债率')
                
                if asset_liability is not None:
                    if asset_liability > 70:
                        return f"该企业{current_year}年资产负债率为{asset_liability:.2f}%，负债水平较高，偿债压力较大。建议优化资本结构，控制负债规模。"
                    elif asset_liability > 50:
                        return f"该企业{current_year}年资产负债率为{asset_liability:.2f}%，负债水平适中。建议持续关注偿债能力指标。"
                    else:
                        return f"该企业{current_year}年资产负债率为{asset_liability:.2f}%，负债水平健康，偿债能力较强。"
            
            return "偿债能力相关的详细分析请查看报告中的偿债风险维度部分。"
        
        elif any(keyword in question_lower for keyword in ['建议', '改善', '优化', '提升']):
            # 改善建议相关问题
            overall = report_data.get('overall_assessment', '')
            if '建议' in overall:
                # 提取建议部分
                suggestions_start = overall.find('建议')
                if suggestions_start != -1:
                    suggestions = overall[suggestions_start:]
                    return f"根据报告分析，给出以下建议：\n{suggestions[:200]}"
            
            return "改善建议请参考报告中的总体风险评估和各维度分析部分。主要包括：定期监测财务指标、针对高风险领域制定改善措施、保持良好的财务管理规范等。"
        
        else:
            # 通用回答
            company_name = company_info.get('企业名称', '该企业')
            return f"关于{company_name}的这个问题，建议您查看报告中的相关章节。报告包含了企业基本信息、总体风险评估、分维度风险分析（盈利、偿债、运营、现金流）以及详细的财务数据。如有具体问题，可以询问特定维度的情况。"


