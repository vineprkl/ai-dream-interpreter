# AI解梦工具

这是一个基于人工智能的解梦工具，可以帮助用户解析梦境的含义，提供专业的心理分析和建议。

## 功能特点

- 🌙 直观的梦境输入界面
- 🤖 基于AI的专业梦境解析
- 📊 详细的分析报告生成
- 🔗 支持报告在线分享
- 🎨 美观的深色主题界面
- 📱 完全响应式设计
- 👨‍💼 管理员控制面板
  - AI接口配置管理
  - 历史记录查看与导出
  - 网站设置管理

## 技术栈

- 后端：Flask (Python)
- 前端：HTML5/CSS3/JavaScript
- UI框架：Bootstrap 5
- 数据库：SQLite
- AI接口：支持自定义AI服务端点

## 快速开始

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/ai-dream-interpreter.git
   cd ai-dream-interpreter
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置AI接口：
   - 访问管理面板 `/admin`（默认用户名：admin，密码：admin123）
   - 在管理面板中配置AI接口参数

4. 启动应用：
   ```bash
   python app.py
   ```

5. 访问网站：
   - 打开浏览器访问 `http://localhost:5000`
   - 管理面板地址 `http://localhost:5000/admin`

## 环境要求

- Python 3.8+
- 详细依赖见 `requirements.txt`

## 使用说明

1. 在首页输入梦境内容
2. 系统会自动进行AI解析
3. 生成详细的解析报告
4. 可以在线查看或分享报告链接

## 自定义配置

- AI接口参数配置
- 网站域名设置
- 系统提示词模板

## 注意事项

- 请妥善保管管理员密码
- 定期备份数据库文件
- 谨慎使用数据清除功能

## 许可证

MIT License 