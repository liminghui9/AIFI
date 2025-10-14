# AIFI 系统 - AI 接入完整指南

## 📋 目录
1. [快速接入（3步）](#快速接入)
2. [详细配置说明](#详细配置)
3. [支持的AI服务](#支持的ai服务)
4. [测试验证](#测试验证)
5. [常见问题](#常见问题)

---

## 🚀 快速接入（3步）

### 步骤1：获取 OpenAI API 密钥

#### 方法A：使用 OpenAI 官方（推荐）
1. 访问：https://platform.openai.com/
2. 注册/登录账号
3. 进入 API Keys 页面：https://platform.openai.com/api-keys
4. 点击 "Create new secret key"
5. 复制生成的密钥（格式：`sk-...`）

**注意**：
- 需要国际信用卡
- 需要科学上网
- 有免费额度，超出后按使用量付费

#### 方法B：使用国内API服务（替代方案）
如果无法访问OpenAI，可以使用国内兼容服务：
- **智谱AI**（ChatGLM）：https://open.bigmodel.cn/
- **通义千问**：https://dashscope.aliyun.com/
- **百度文心**：https://cloud.baidu.com/
- **讯飞星火**：https://xinghuo.xfyun.cn/

### 步骤2：创建配置文件

在项目根目录创建 `.env` 文件：

```bash
# 方法1：复制模板文件（推荐）
# （注：.env.example文件已被删除，请手动创建）

# 方法2：手动创建
# 创建新文件：.env
```

**`.env` 文件内容：**

```env
# OpenAI API 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# Flask 配置
SECRET_KEY=your-random-secret-key-here
```

**重要**：
- ✅ 替换 `sk-your-api-key-here` 为您的真实API密钥
- ✅ 不要上传 `.env` 到Git（已在.gitignore中）
- ✅ SECRET_KEY 可以是任意随机字符串

### 步骤3：重启系统

```bash
# 停止当前运行的系统（Ctrl+C）
# 重新启动
python app.py
```

启动时会显示AI状态：
```
==================================================
AIFI 智能财报系统启动中...
==================================================
访问地址: http://localhost:5000
AI功能状态: 已启用  ← 看到这个就成功了！
==================================================
```

---

## 📝 详细配置说明

### 配置选项详解

#### 1. OPENAI_API_KEY（必需）
```env
OPENAI_API_KEY=sk-proj-xxx...
```
- **说明**：OpenAI API密钥
- **获取**：https://platform.openai.com/api-keys
- **格式**：以 `sk-` 开头
- **作用**：调用GPT模型进行智能分析

#### 2. OPENAI_API_BASE（可选）
```env
OPENAI_API_BASE=https://api.openai.com/v1
```
- **说明**：API接口地址
- **默认值**：https://api.openai.com/v1
- **用途**：
  - 使用代理服务时修改此地址
  - 使用国内兼容服务时修改

**示例（使用代理）**：
```env
OPENAI_API_BASE=https://your-proxy.com/v1
```

#### 3. 修改AI模型（高级）

编辑 `config.py` 文件：

```python
class Config:
    # 修改这一行
    OPENAI_MODEL = 'gpt-3.5-turbo'  # 或 'gpt-4'
```

**模型对比**：

| 模型 | 速度 | 质量 | 成本 | 推荐场景 |
|------|------|------|------|----------|
| gpt-3.5-turbo | ⚡⚡⚡ | ⭐⭐⭐ | 💰 | 日常使用 |
| gpt-4 | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | 专业分析 |
| gpt-4-turbo | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰 | 推荐 |

---

## 🌐 支持的AI服务

### 1. OpenAI 官方（推荐）

**配置**：
```env
OPENAI_API_KEY=sk-your-key
OPENAI_API_BASE=https://api.openai.com/v1
```

**优点**：
- ✅ 模型最强大
- ✅ 稳定性最好
- ✅ 文档完善

**缺点**：
- ❌ 需要科学上网
- ❌ 需要国际信用卡

---

### 2. 智谱AI（国内推荐）

**配置**：
```env
OPENAI_API_KEY=your-zhipu-api-key
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4
```

**获取密钥**：
1. 访问：https://open.bigmodel.cn/
2. 注册并登录
3. 创建API密钥

**修改代码**（`modules/ai_analyzer.py`）：
```python
# 第48行附近，修改模型调用
response = openai.ChatCompletion.create(
    model='glm-4',  # 使用智谱模型
    messages=[...],
    temperature=0.7,
    max_tokens=500
)
```

---

### 3. 阿里云通义千问

**配置**：
```env
OPENAI_API_KEY=your-dashscope-key
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**获取密钥**：
1. 访问：https://dashscope.aliyun.com/
2. 开通服务并获取API-KEY

---

### 4. 百度文心一言

**配置**：
```env
OPENAI_API_KEY=your-baidu-key
OPENAI_API_BASE=https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop
```

**注意**：需要修改 `ai_analyzer.py` 适配百度API格式

---

## ✅ 测试验证

### 方法1：查看启动信息

启动系统时查看控制台输出：

```bash
python app.py
```

**成功示例**：
```
AI功能状态: 已启用  ← 配置成功
```

**失败示例**：
```
AI功能状态: 未配置（将使用默认分析）  ← 未配置或配置错误
```

---

### 方法2：生成报告测试

1. 登录系统
2. 上传财务数据
3. 查看生成的报告
4. 检查AI分析内容

**AI分析特征**：
- 文字更自然流畅
- 分析更深入细致
- 有具体的数字引用
- 提供专业建议

**默认分析特征**：
- 文字较简单
- 基于规则判断
- 结论较笼统

---

### 方法3：创建测试脚本

创建文件 `test_ai.py`：

```python
"""测试AI连接"""
import openai
from config import Config

openai.api_key = Config.OPENAI_API_KEY
openai.api_base = Config.OPENAI_API_BASE

try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=10
    )
    print("✅ AI连接成功！")
    print(f"回复：{response.choices[0].message.content}")
except Exception as e:
    print(f"❌ AI连接失败：{str(e)}")
```

运行测试：
```bash
python test_ai.py
```

---

## ❓ 常见问题

### Q1: 提示"API密钥无效"？

**原因**：
- API密钥错误或过期
- API密钥没有额度

**解决**：
1. 检查 `.env` 中的密钥是否正确
2. 登录OpenAI查看余额：https://platform.openai.com/usage
3. 确认密钥未被撤销

---

### Q2: 提示"连接超时"？

**原因**：
- 网络无法访问OpenAI
- API地址配置错误

**解决**：
1. 确认网络可以访问国外网站
2. 使用代理或VPN
3. 改用国内AI服务

---

### Q3: AI分析质量不好？

**优化方法**：

**1. 升级模型**（`config.py`）：
```python
OPENAI_MODEL = 'gpt-4'  # 或 'gpt-4-turbo'
```

**2. 调整温度参数**（`ai_analyzer.py` 第50行）：
```python
temperature=0.7,  # 降低到0.5更保守，提高到0.9更创新
```

**3. 增加提示词上下文**（`ai_analyzer.py` 第61-90行）：
- 添加更多行业信息
- 提供更详细的指标说明

---

### Q4: 成本控制？

**查看用量**：
- OpenAI Dashboard：https://platform.openai.com/usage

**降低成本**：

**方法1：设置月度限额**
- OpenAI后台设置月度预算

**方法2：使用更便宜的模型**
```python
OPENAI_MODEL = 'gpt-3.5-turbo'  # 而不是 gpt-4
```

**方法3：缩短回复长度**（`ai_analyzer.py`）：
```python
max_tokens=300,  # 从500降低到300
```

**参考价格**（2024年）：
- GPT-3.5-turbo: $0.0005 / 1K tokens
- GPT-4: $0.03 / 1K tokens
- GPT-4-turbo: $0.01 / 1K tokens

---

### Q5: 不想使用AI可以吗？

**可以！** 系统有内置的默认分析逻辑。

不配置 `.env` 或留空 `OPENAI_API_KEY`，系统会：
- ✅ 正常生成报告
- ✅ 使用规则引擎分析
- ✅ 提供基础风险判断
- ⚠️ 分析较简单

---

## 🔧 高级配置

### 自定义提示词

编辑 `modules/ai_analyzer.py`，找到 `_build_risk_analysis_prompt` 方法：

```python
def _build_risk_analysis_prompt(self, ...):
    prompt = f"""请分析{company_name}的{dimension_name}状况。

【在这里添加您的自定义指令】
例如：
- 请使用专业金融术语
- 重点关注行业对比
- 提供具体改进建议

企业基本信息：
...
```

---

### 使用本地AI模型

如果您有本地部署的大模型（如Llama、ChatGLM）：

1. 确保模型提供OpenAI兼容接口
2. 修改配置：

```env
OPENAI_API_KEY=dummy-key  # 本地模型可能不需要
OPENAI_API_BASE=http://localhost:8000/v1  # 本地服务地址
```

3. 修改 `config.py`：
```python
OPENAI_MODEL = 'your-local-model-name'
```

---

## 📊 效果对比

### 使用AI前（默认分析）
```
【盈利风险分析】企业处于盈利状态，盈利能力表现良好。
建议持续关注相关指标变化趋势。风险等级：低风险。
```

### 使用AI后（GPT-4分析）
```
【盈利风险分析】该企业2023年净利润率为9.00%，较2022年的
8.57%提升0.43个百分点，显示盈利能力持续改善。毛利率达到
40.00%，高于行业平均水平37.14%，表明产品具有较强的市场
竞争力和定价能力。净资产收益率22.50%处于健康区间，资本
运作效率良好。

潜在风险：虽然整体盈利能力强劲，但需关注营业成本占比的
变化趋势，建议优化成本结构以保持竞争优势。

风险等级：低风险
```

---

## 🎯 推荐配置

### 方案A：个人学习/演示
```env
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
# 使用 gpt-3.5-turbo（默认）
```
**成本**：约 $0.01 / 次报告

---

### 方案B：专业使用
```env
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
```

修改 `config.py`：
```python
OPENAI_MODEL = 'gpt-4-turbo'
```
**成本**：约 $0.05 / 次报告

---

### 方案C：国内用户
```env
# 使用智谱AI
OPENAI_API_KEY=your-zhipu-key
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4
```

修改 `config.py`：
```python
OPENAI_MODEL = 'glm-4'
```

---

## 📞 获取帮助

如遇问题：
1. 查看控制台错误信息
2. 检查 `.env` 配置是否正确
3. 运行 `test_ai.py` 测试连接
4. 查看OpenAI官方文档：https://platform.openai.com/docs

---

**祝您使用愉快！AI加持让财报分析更智能！🚀**

---

*最后更新：2024年*  
*AIFI 智能财报系统 v1.1*

