"""
PDF导出模块 - 基于HTML模板
使用 WeasyPrint 将HTML渲染为PDF，优化输出质量
"""

from weasyprint import HTML, CSS
from flask import render_template
import os
from typing import Dict
import tempfile

class PDFExporter:
    """PDF导出器 - 基于HTML模板，优化PDF输出质量"""
    
    def __init__(self):
        """初始化PDF导出器"""
        pass
    
    def export_to_pdf(self, report_data: Dict, output_path: str) -> bool:
        """
        将报告导出为PDF
        
        Args:
            report_data: 报告数据字典
            output_path: 输出PDF文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取项目根目录的绝对路径
            import os
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cover_image_path = os.path.join(current_dir, 'static', 'image', 'tupian.png')
            
            # 将封面图片路径添加到报告数据中
            report_data['cover_image_path'] = cover_image_path
            
            # 渲染HTML模板
            html_content = render_template('report_pdf.html', report=report_data)
            
            # 自定义CSS（用于PDF打印优化）
            pdf_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2.2cm 1.8cm;
                }
                
                @page :first {
                    margin: 0;
                }
                
                body {
                    font-size: 10.5pt;
                    font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
                }
                
                /* 表格优化 - 避免跨页断开 */
                table {
                    page-break-inside: avoid;
                }
                
                thead {
                    display: table-header-group;
                }
                
                tr {
                    page-break-inside: avoid;
                    page-break-after: auto;
                }
                
                /* 标题避免孤立 */
                h1, h2, h3, h4, h5 {
                    page-break-after: avoid;
                    page-break-inside: avoid;
                }
                
                /* 图表容器不跨页 */
                .chart-container {
                    page-break-inside: avoid;
                    page-break-before: auto;
                }
                
                /* 模块分页控制 - 每个模块新起一页 */
                .report-card {
                    page-break-before: always;
                    page-break-inside: avoid;
                }
                
                .overall-assessment {
                    page-break-before: always;
                    page-break-inside: avoid;
                }
                
                /* 维度卡片分页控制 - 每个维度新起一页 */
                .dimension-card {
                    page-break-before: always;
                    page-break-inside: avoid;
                }
                
                /* 分析文本优化 */
                .analysis-text {
                    page-break-inside: avoid;
                    orphans: 3;
                    widows: 3;
                }
            ''')
            
            # 生成PDF - 优化渲染参数
            HTML(string=html_content).write_pdf(
                output_path,
                stylesheets=[pdf_css],
                presentational_hints=True,
                optimize_images=True
            )
            
            return True
            
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_to_pdf_alt(self, report_data: Dict, output_path: str) -> bool:
        """
        备用方案：使用 pdfkit（需要安装 wkhtmltopdf）
        
        Args:
            report_data: 报告数据字典
            output_path: 输出PDF文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            import pdfkit
            
            # 渲染HTML模板
            html_content = render_template('report_pdf.html', report=report_data)
            
            # PDF选项
            options = {
                'page-size': 'A4',
                'margin-top': '2cm',
                'margin-right': '1.5cm',
                'margin-bottom': '2cm',
                'margin-left': '1.5cm',
                'encoding': 'UTF-8',
                'enable-local-file-access': None,
                'no-outline': None,
                'print-media-type': None,
                'dpi': 300,
                'image-quality': 100,
            }
            
            # 生成PDF
            pdfkit.from_string(html_content, output_path, options=options)
            
            return True
            
        except ImportError:
            print("pdfkit 未安装，使用 WeasyPrint")
            return self.export_to_pdf(report_data, output_path)
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def get_pdf_filename(report_data: Dict, report_id: str) -> str:
        """
        生成PDF文件名
        
        Args:
            report_data: 报告数据
            report_id: 报告ID
            
        Returns:
            str: 文件名
        """
        company_name = report_data.get('basic_info', {}).get('企业名称', '企业')
        # 清理文件名中的非法字符
        safe_name = company_name.replace('/', '_').replace('\\', '_')
        return f"{safe_name}_财务分析报告_{report_id}.pdf"

