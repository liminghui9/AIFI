# 财务分析报告系统

企业财务数据分析与报告生成系统，支持Excel数据导入、智能分析、图表生成和报告导出。

## 功能特性

- 📊 财务数据导入与处理
- 📈 多维度财务指标分析
- 📉 可视化图表生成
- 📄 PDF/Word报告导出
- 🤖 AI智能分析（可选）

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML/CSS/JavaScript
- **数据处理**: pandas, openpyxl
- **图表**: pyecharts
- **文档生成**: python-docx, reportlab

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行应用
```bash
python app.py
```

3. 访问系统
打开浏览器访问: http://localhost:5000

## 项目结构

```
├── app.py                 # 主应用入口
├── config.py             # 配置文件
├── modules/              # 核心模块
│   ├── data_processor.py       # 数据处理
│   ├── indicator_calculator.py # 指标计算
│   ├── chart_generator.py      # 图表生成
│   ├── report_generator.py     # 报告生成
│   ├── export_generator.py     # 导出功能
│   └── ai_analyzer.py          # AI分析
├── templates/            # HTML模板
├── static/              # 静态资源
├── sample_data/         # 示例数据
└── uploads/             # 上传文件目录
```

## 使用说明

详见 `快速开始.txt` 和 `AI接入指南.md`

## 许可证

此项目仅供学习和研究使用

