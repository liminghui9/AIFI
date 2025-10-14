"""
报告导出模块
支持导出为Word和PDF格式
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from typing import Dict, Optional
from datetime import datetime

class ExportGenerator:
    """报告导出生成器"""
    
    def __init__(self):
        """初始化导出生成器"""
        pass
    
    def export_to_word(self, report_data: Dict, output_path: str) -> bool:
        """
        导出为Word格式
        
        Args:
            report_data: 报告数据
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            doc = Document()
            
            # 设置页面
            sections = doc.sections
            for section in sections:
                section.page_height = Inches(11.69)  # A4高度
                section.page_width = Inches(8.27)    # A4宽度
            
            # 1. 添加标题
            title = doc.add_heading('企业财务分析报告', 0)
            title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # 2. 添加生成信息
            info_para = doc.add_paragraph(f"生成时间：{report_data['generated_at']}")
            info_para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
            
            doc.add_paragraph()  # 空行
            
            # 3. 企业基本信息
            doc.add_heading('一、企业基本信息', 1)
            basic_info = report_data['basic_info']
            
            # 创建基本信息表格
            info_table = doc.add_table(rows=len(basic_info), cols=2)
            info_table.style = 'Light Grid Accent 1'
            
            for idx, (key, value) in enumerate(basic_info.items()):
                row_cells = info_table.rows[idx].cells
                row_cells[0].text = key
                row_cells[1].text = str(value)
            
            doc.add_paragraph()
            
            # 4. 总体风险评估
            doc.add_heading('二、总体风险评估', 1)
            doc.add_paragraph(report_data['overall_assessment'])
            
            doc.add_paragraph()
            
            # 4.1 数据可视化分析说明
            if report_data.get('charts'):
                doc.add_heading('三、数据可视化分析', 1)
                chart_info = doc.add_paragraph()
                chart_run = chart_info.add_run('本报告包含以下数据可视化图表：')
                chart_run.bold = True
                
                chart_descriptions = {
                    'health_dashboard': '• 财务健康度仪表盘：全面展示企业各维度财务健康状况',
                    'main_indicators': '• 主要财务指标对比图：展示核心财务指标的年度对比',
                    'profitability': '• 盈利能力趋势图：分析企业盈利能力的发展趋势',
                    'solvency': '• 偿债能力分析图：评估企业短期和长期偿债能力',
                    'operational': '• 运营能力分析图：衡量企业资产运营效率',
                    'cashflow': '• 现金流分析图：分析企业现金流状况',
                    'risk_radar': '• 风险评估雷达图：直观展示各维度风险等级'
                }
                
                for chart_key, description in chart_descriptions.items():
                    if report_data['charts'].get(chart_key):
                        doc.add_paragraph(description)
                
                note_para = doc.add_paragraph('注意：详细的交互式图表请查看在线报告页面进行分析。')
                note_run = note_para.runs[0]
                note_run.italic = True
                note_run.font.size = Pt(10)
                
                doc.add_paragraph()
            
            # 5. 分维度风险分析
            doc.add_heading('四、分维度风险分析', 1)
            
            dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
            years = report_data['years']
            
            for dimension in dimensions:
                doc.add_heading(f'（{dimensions.index(dimension) + 1}）{dimension}', 2)
                
                # 添加指标数据
                if years and dimension in report_data['indicators'].get(years[0], {}):
                    indicators = report_data['indicators'][years[0]][dimension]
                    
                    # 创建指标表格
                    indicator_table = doc.add_table(rows=len(indicators) + 1, cols=3 if len(years) >= 2 else 2)
                    indicator_table.style = 'Light List Accent 1'
                    
                    # 表头
                    hdr_cells = indicator_table.rows[0].cells
                    hdr_cells[0].text = '指标名称'
                    hdr_cells[1].text = f'{years[0]}年' if years else '当前年度'
                    if len(years) >= 2:
                        hdr_cells[2].text = f'{years[1]}年'
                    
                    # 填充数据
                    for idx, (indicator_name, value) in enumerate(indicators.items()):
                        row_cells = indicator_table.rows[idx + 1].cells
                        row_cells[0].text = indicator_name
                        
                        # 获取单位
                        unit = self._get_indicator_unit(indicator_name)
                        
                        # 当前年度值
                        if value is not None:
                            row_cells[1].text = f"{value:.2f}{unit}"
                        else:
                            row_cells[1].text = "数据缺失"
                        
                        # 上一年度值
                        if len(years) >= 2:
                            prev_value = report_data['indicators'].get(years[1], {}).get(dimension, {}).get(indicator_name)
                            if prev_value is not None:
                                row_cells[2].text = f"{prev_value:.2f}{unit}"
                            else:
                                row_cells[2].text = "数据缺失"
                
                # 添加AI分析
                doc.add_paragraph()
                analysis_para = doc.add_paragraph(f"分析：{report_data['dimension_analyses'].get(dimension, '暂无分析')}")
                
                doc.add_paragraph()
            
            # 6. 财务报表数据
            doc.add_heading('四、财务报表数据（精简版）', 1)
            
            financial_data = report_data['financial_data']
            tables_to_show = ['资产负债表', '利润表', '现金流量表']
            
            for table_name in tables_to_show:
                doc.add_heading(f'（{tables_to_show.index(table_name) + 1}）{table_name}', 2)
                
                if years:
                    year1_data = financial_data.get(years[0], {}).get(table_name, {})
                    
                    if year1_data:
                        # 创建财务表格
                        fin_table = doc.add_table(rows=len(year1_data) + 1, cols=3 if len(years) >= 2 else 2)
                        fin_table.style = 'Light Grid'
                        
                        # 表头
                        hdr_cells = fin_table.rows[0].cells
                        hdr_cells[0].text = '项目'
                        hdr_cells[1].text = f'{years[0]}年（万元）'
                        if len(years) >= 2:
                            hdr_cells[2].text = f'{years[1]}年（万元）'
                        
                        # 填充数据
                        for idx, (item_name, value) in enumerate(year1_data.items()):
                            row_cells = fin_table.rows[idx + 1].cells
                            row_cells[0].text = item_name
                            
                            if value is not None:
                                row_cells[1].text = f"{value:,.2f}"
                            else:
                                row_cells[1].text = "数据缺失"
                            
                            if len(years) >= 2:
                                year2_value = financial_data.get(years[1], {}).get(table_name, {}).get(item_name)
                                if year2_value is not None:
                                    row_cells[2].text = f"{year2_value:,.2f}"
                                else:
                                    row_cells[2].text = "数据缺失"
                
                doc.add_paragraph()
            
            # 7. 添加免责声明
            doc.add_page_break()
            doc.add_heading('免责声明', 1)
            disclaimer = """
本报告由AIFI智能财报系统自动生成，分析结果基于大语言模型和财务数据计算得出。
报告内容仅供参考，不构成审计、投资、法律或信用评级结论。
使用者应结合实际业务情况，谨慎判断和使用本报告信息。
系统不对分析结果的准确性、完整性或稳定性作出保证。
            """
            doc.add_paragraph(disclaimer.strip())
            
            # 保存文档
            doc.save(output_path)
            return True
            
        except Exception as e:
            print(f"导出Word失败: {str(e)}")
            return False
    
    def export_to_pdf(self, report_data: Dict, output_path: str) -> bool:
        """
        导出为PDF格式
        
        Args:
            report_data: 报告数据
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 注册中文字体
            chinese_font = self._register_chinese_fonts()
            
            # 创建PDF文档
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # 自定义样式（使用中文字体）
            if chinese_font:
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Title'],
                    fontName=chinese_font,
                    fontSize=20,
                    alignment=1,  # 居中
                    spaceAfter=12
                )
                
                heading1_style = ParagraphStyle(
                    'CustomHeading1',
                    parent=styles['Heading1'],
                    fontName=chinese_font,
                    fontSize=14,
                    spaceAfter=10
                )
                
                heading2_style = ParagraphStyle(
                    'CustomHeading2',
                    parent=styles['Heading2'],
                    fontName=chinese_font,
                    fontSize=12,
                    spaceAfter=8
                )
                
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontName=chinese_font,
                    fontSize=10,
                    leading=14
                )
            else:
                # 如果没有中文字体，使用默认样式
                title_style = styles['Title']
                heading1_style = styles['Heading1']
                heading2_style = styles['Heading2']
                normal_style = styles['Normal']
            
            # 1. 标题
            story.append(Paragraph('企业财务分析报告', title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # 2. 生成信息
            story.append(Paragraph(f"生成时间：{report_data['generated_at']}", normal_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 3. 企业基本信息
            story.append(Paragraph('一、企业基本信息', heading1_style))
            
            basic_info = report_data['basic_info']
            basic_data = [[k, str(v)] for k, v in basic_info.items()]
            basic_table = Table(basic_data, colWidths=[2*inch, 4*inch])
            
            # 表格样式（使用中文字体）
            table_font = chinese_font if chinese_font else 'Helvetica'
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), table_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(basic_table)
            story.append(Spacer(1, 0.3*inch))
            
            # 4. 总体风险评估
            story.append(Paragraph('二、总体风险评估', heading1_style))
            story.append(Paragraph(report_data['overall_assessment'], normal_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 4.1 数据可视化分析说明
            if report_data.get('charts'):
                story.append(Paragraph('三、数据可视化分析', heading1_style))
                story.append(Paragraph('<b>本报告包含以下数据可视化图表：</b>', normal_style))
                
                chart_descriptions = {
                    'health_dashboard': '• 财务健康度仪表盘：全面展示企业各维度财务健康状况',
                    'main_indicators': '• 主要财务指标对比图：展示核心财务指标的年度对比',
                    'profitability': '• 盈利能力趋势图：分析企业盈利能力的发展趋势',
                    'solvency': '• 偿债能力分析图：评估企业短期和长期偿债能力',
                    'operational': '• 运营能力分析图：衡量企业资产运营效率',
                    'cashflow': '• 现金流分析图：分析企业现金流状况',
                    'risk_radar': '• 风险评估雷达图：直观展示各维度风险等级'
                }
                
                for chart_key, description in chart_descriptions.items():
                    if report_data['charts'].get(chart_key):
                        story.append(Paragraph(description, normal_style))
                
                story.append(Paragraph('<i>注意：详细的交互式图表请查看在线报告页面进行分析。</i>', normal_style))
                story.append(Spacer(1, 0.3*inch))
            
            # 5. 分维度风险分析
            story.append(Paragraph('四、分维度风险分析', heading1_style))
            
            dimensions = ['盈利风险', '偿债风险', '运营风险', '现金流风险']
            years = report_data['years']
            
            for dimension in dimensions:
                story.append(Paragraph(f'（{dimensions.index(dimension) + 1}）{dimension}', heading2_style))
                
                # 添加指标表格
                if years and dimension in report_data['indicators'].get(years[0], {}):
                    indicators = report_data['indicators'][years[0]][dimension]
                    
                    # 准备表格数据
                    table_data = [['指标名称', f'{years[0]}年']]
                    if len(years) >= 2:
                        table_data[0].append(f'{years[1]}年')
                    
                    for indicator_name, value in indicators.items():
                        unit = self._get_indicator_unit(indicator_name)
                        row = [indicator_name]
                        
                        if value is not None:
                            row.append(f"{value:.2f}{unit}")
                        else:
                            row.append("数据缺失")
                        
                        if len(years) >= 2:
                            prev_value = report_data['indicators'].get(years[1], {}).get(dimension, {}).get(indicator_name)
                            if prev_value is not None:
                                row.append(f"{prev_value:.2f}{unit}")
                            else:
                                row.append("数据缺失")
                        
                        table_data.append(row)
                    
                    # 创建表格
                    col_widths = [2.5*inch, 1.5*inch]
                    if len(years) >= 2:
                        col_widths.append(1.5*inch)
                    
                    indicator_table = Table(table_data, colWidths=col_widths)
                    
                    # 表格样式（使用中文字体）
                    indicator_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), table_font),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (1, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    story.append(indicator_table)
                
                # 添加分析
                story.append(Spacer(1, 0.1*inch))
                analysis_text = f"分析：{report_data['dimension_analyses'].get(dimension, '暂无分析')}"
                story.append(Paragraph(analysis_text, normal_style))
                story.append(Spacer(1, 0.2*inch))
            
            # 添加分页
            story.append(PageBreak())
            
            # 6. 免责声明
            story.append(Paragraph('免责声明', heading1_style))
            disclaimer = """
本报告由AIFI智能财报系统自动生成，分析结果基于大语言模型和财务数据计算得出。
报告内容仅供参考，不构成审计、投资、法律或信用评级结论。
使用者应结合实际业务情况，谨慎判断和使用本报告信息。
系统不对分析结果的准确性、完整性或稳定性作出保证。
            """
            story.append(Paragraph(disclaimer.strip(), normal_style))
            
            # 生成PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"导出PDF失败: {str(e)}")
            return False
    
    def _register_chinese_fonts(self):
        """注册中文字体（如果可用）"""
        try:
            # 尝试注册常见的中文字体 - Windows
            font_paths = [
                ('SimSun', 'C:/Windows/Fonts/simsun.ttc'),      # 宋体
                ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),      # 黑体
                ('Microsoft', 'C:/Windows/Fonts/msyh.ttc'),     # 微软雅黑
                ('SimSun', 'C:/Windows/Fonts/simsun.ttf'),      # 宋体备用
            ]
            
            for font_name, font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        # 成功注册就返回字体名
                        return font_name
                    except:
                        continue
            
            # 如果都失败，返回None
            return None
        except:
            return None
    
    def _get_indicator_unit(self, indicator_name: str) -> str:
        """获取指标单位"""
        percentage_indicators = [
            '净利润率', '毛利率', '净资产收益率', '资产负债率'
        ]
        
        amount_indicators = [
            '经营性净现金流', '现金净增加额'
        ]
        
        if indicator_name in percentage_indicators:
            return '%'
        elif indicator_name in amount_indicators:
            return '万元'
        else:
            return ''

