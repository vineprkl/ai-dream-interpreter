from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
import os
import json
import requests
from datetime import datetime
from markupsafe import Markup
import uuid
import markdown2
import csv
from io import StringIO

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dreams.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REPORTS_FOLDER'] = 'reports'

# 确保报告目录存在
if not os.path.exists(app.config['REPORTS_FOLDER']):
    os.makedirs(app.config['REPORTS_FOLDER'])

# 添加markdown过滤器
@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ""
    return Markup(markdown2.markdown(text, extras=['fenced-code-blocks', 'tables', 'break-on-newline']))

# 添加nl2br过滤器
@app.template_filter('nl2br')
def nl2br_filter(text):
    if not text:
        return ""
    return Markup(text.replace('\n', '<br>'))

# 初始化数据库
db = SQLAlchemy(app)

# 定义数据模型
class AIConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_url = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIConfig {self.id}>'

class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    interpretation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Dream {self.id}>'

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Setting {self.key}>'

# 定义表单
class DreamForm(FlaskForm):
    dream_content = TextAreaField('描述你的梦境', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('解析梦境')

class AdminLoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class AIConfigForm(FlaskForm):
    api_url = StringField('API地址', validators=[DataRequired()])
    api_key = StringField('API密钥', validators=[DataRequired()])
    model_name = StringField('模型名称', validators=[DataRequired()])
    submit = SubmitField('保存')

# AI接口配置
DEFAULT_AI_CONFIG = {
    'api_url': "https://api.example.com/v1/chat/completions",
    'api_key': "your-api-key-here",
    'model_name': "gpt-3.5-turbo"
}

# 系统提示词（固定模板）
SYSTEM_PROMPT = """### GPT角色名称：梦境心理分析专家
**目标**：从专业心理学的角度帮助用户解读梦境中的象征和情绪，提供深度的自我反思建议和人际关系洞见。

---

#### 用户梦境内容输入
- **功能**：用户可以输入梦境的详细内容，包括情境、人物和主要情绪。此部分将作为梦境分析的基础数据。
- **输入提示**：请描述您的梦境，例如涉及的情境、人物和您的情绪感受。

---

#### 梦境解读结果输出模板

1. **概述**
   - **描述**：提供梦境的总体解读，从心理学角度揭示梦境可能传达的潜意识情绪和心理状态。
   - **示例**：
     > 每个梦都是潜意识的表达。您梦到的情境可能反映了您深层的情绪需求或心理矛盾。梦中的"替前同事结尾尴尬"可能揭示了您内心尚未处理的某些情绪或经历。

2. **主题概述**
   - **描述**：分析梦的主题，帮助用户理解梦中情境可能与现实生活中的情绪或行为模式的关联。
   - **示例**：
     > 在梦中，您替前同事处理某个事情的尴尬结尾，或许象征了您现实中某种责任感或对过去未完成事务的压力。

3. **关键符号**
   - **描述**：识别和解读梦中的关键符号，从心理学角度说明这些符号在潜意识中的象征意义。
   - **示例**：
     - **前同事**：可能代表了您过去的某种人际关系，或象征着您对特定关系的未了结情绪。
     - **尴尬结尾**：暗示未解决的内心冲突或对某个事件的不满，可能预示现实生活中有待改善的关系或事务。

4. **情感景观**
   - **描述**：分析梦中表现出的情绪氛围，例如焦虑、不安等，以帮助用户识别现实生活中的类似情绪反应。
   - **示例**：
     > 梦中的尴尬感可能揭示了您在某些现实情境下的焦虑感，尤其是在与同事或他人合作时的压力。

5. **潜在含义**
   - **描述**：总结梦境的可能深层含义，揭示梦境背后反映的心理动机或情绪需求。
   - **示例**：
     - **情感的未解之结**：暗示对过去关系的挂念或未完成的心理结，可能使您在内心持续感到不安。
     - **自我反省**：梦境促使您反思自己的沟通方式和职场互动模式，思考如何更好地应对类似情境。
     - **策略与规划**：提醒您在未来的职场或人际关系中，尝试更积极地建立沟通和理解。

6. **反思点**
   - **描述**：引导用户从梦境中得到启发，提出反思性问题以加深对自我的理解。
   - **示例**：
     > 在思考该梦时，请考虑以下问题：
       - 您是否仍对前同事或过去的工作环境有情感未解之结？
       - 当前的生活中，是否有类似的尴尬情境或不安的人际关系？
       - 您是否在需要主动改善某些关系，或者调整对他人的期望？

7. **总结**
   - **描述**：总结梦境解读的总体含义，并提醒用户从梦境得到的启示可能适用于改善其现实生活中的人际关系或心理状态。
   - **示例**：
     > 梦到替前同事结尾尴尬，提示您关注内心的未解情绪和人际关系的影响。适当处理这些情感，可能有助于您在未来的人际交往和自我成长上更加从容。

---

**技能模块总结**
- **用户梦境内容输入**：引导用户输入梦境情节。
- **梦境解读结果输出模板**：使用结构化模板分段呈现分析，帮助用户理解梦境的潜意识象征和情绪反映。
  
**语气**：温和、专业，带有心理学的探索性分析。

**适用场景**：适用于需要从专业心理学角度进行梦境解读的用户，以帮助其洞察潜意识的需求和情绪。"""

# 调用AI接口解析梦境
def interpret_dream(dream_content):
    # 获取最新的AI配置
    ai_config = AIConfig.query.order_by(AIConfig.created_at.desc()).first()
    
    if not ai_config:
        # 使用默认配置
        api_url = DEFAULT_AI_CONFIG['api_url']
        api_key = DEFAULT_AI_CONFIG['api_key']
        model_name = DEFAULT_AI_CONFIG['model_name']
    else:
        api_url = ai_config.api_url
        api_key = ai_config.api_key
        model_name = ai_config.model_name
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": dream_content}
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI API调用错误: {str(e)}")
        return "很抱歉，解梦服务暂时不可用，请稍后再试。"

def generate_report_html(dream_content, interpretation):
    report_id = str(uuid.uuid4())
    report_filename = f"dream_report_{report_id}.html"
    report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
    
    # 将解释结果转换为HTML
    interpretation_html = markdown2.markdown(interpretation, extras=['fenced-code-blocks', 'tables', 'break-on-newline'])
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>梦境心理分析报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            padding: 2rem 0;
        }}
        .report-container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,.1);
        }}
        .report-header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #007bff;
        }}
        .dream-content {{
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 2rem;
        }}
        .interpretation {{
            line-height: 1.8;
        }}
        .interpretation h1, .interpretation h2, .interpretation h3, 
        .interpretation h4, .interpretation h5, .interpretation h6 {{
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: #0d6efd;
        }}
        .interpretation ul, .interpretation ol {{
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }}
        .interpretation p {{
            margin-bottom: 1rem;
        }}
        .interpretation strong {{
            color: #0d6efd;
        }}
        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>梦境心理分析报告</h1>
            <p class="text-muted">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>梦境内容</h2>
        <div class="dream-content">
            {dream_content}
        </div>
        
        <h2>专业解析</h2>
        <div class="interpretation">
            {interpretation_html}
        </div>
        
        <div class="footer">
            <p>由AI解梦工具生成</p>
            <p>Copyright © 2025 dajiba工具合集</p>
        </div>
    </div>
</body>
</html>
    """
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_filename

@app.route('/reports/<filename>')
def download_report(filename):
    return send_from_directory(app.config['REPORTS_FOLDER'], filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = DreamForm()
    interpretation = None
    report_url = None
    
    if form.validate_on_submit():
        dream_content = form.dream_content.data
        interpretation = interpret_dream(dream_content)
        
        # 生成报告
        report_filename = generate_report_html(dream_content, interpretation)
        base_url = url_for('download_report', filename=report_filename, _external=True)
        
        # 获取网站域名设置
        site_domain = Settings.query.filter_by(key='site_domain').first()
        if site_domain and site_domain.value:
            # 如果设置了域名，替换链接中的域名部分
            report_url = base_url.replace(request.host_url.rstrip('/'), site_domain.value.rstrip('/'))
        else:
            report_url = base_url
        
        # 保存梦境和解析结果到数据库
        new_dream = Dream(content=dream_content, interpretation=interpretation)
        db.session.add(new_dream)
        db.session.commit()
        
    return render_template('index.html', form=form, interpretation=interpretation, report_url=report_url)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        # 简单的硬编码管理员验证，实际应用中应使用更安全的方式
        if form.username.data == 'admin' and form.password.data == 'admin123':
            session['admin_logged_in'] = True
            flash('登录成功！', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用户名或密码错误！', 'danger')
    
    return render_template('admin_login.html', form=form)

@app.route('/admin/dreams/<int:dream_id>', methods=['DELETE'])
def delete_dream(dream_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': '未授权的操作'}), 403
    
    try:
        dream = Dream.query.get_or_404(dream_id)
        db.session.delete(dream)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/dreams/clear', methods=['DELETE'])
def clear_dreams():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': '未授权的操作'}), 403
    
    try:
        Dream.query.delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/dreams/<int:dream_id>')
def get_dream(dream_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': '未授权的操作'}), 403
    
    try:
        dream = Dream.query.get_or_404(dream_id)
        return jsonify({
            'success': True,
            'dream': {
                'id': dream.id,
                'content': dream.content,
                'interpretation': dream.interpretation,
                'interpretation_html': markdown2.markdown(dream.interpretation),
                'created_at': dream.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/dreams/<int:dream_id>/export')
def export_single_dream(dream_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        dream = Dream.query.get_or_404(dream_id)
        si = StringIO()
        cw = csv.writer(si)
        
        # 写入表头
        cw.writerow(['时间', '梦境内容', '解析结果'])
        
        # 写入数据
        cw.writerow([
            dream.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            dream.content,
            dream.interpretation
        ])
        
        output = si.getvalue()
        si.close()
        
        return send_file(
            StringIO(output),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'dream_{dream_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        flash('导出失败：' + str(e), 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/dreams/export')
def export_dreams():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        si = StringIO()
        cw = csv.writer(si)
        
        # 写入表头
        cw.writerow(['时间', '梦境内容', '解析结果'])
        
        # 获取要导出的记录
        selected_ids = request.args.get('ids')
        if selected_ids:
            dream_ids = [int(id) for id in selected_ids.split(',')]
            dreams = Dream.query.filter(Dream.id.in_(dream_ids)).order_by(Dream.created_at.desc()).all()
        else:
            dreams = Dream.query.order_by(Dream.created_at.desc()).all()
        
        # 写入数据
        for dream in dreams:
            cw.writerow([
                dream.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                dream.content,
                dream.interpretation
            ])
        
        output = si.getvalue()
        si.close()
        
        filename = 'selected_dreams' if selected_ids else 'all_dreams'
        return send_file(
            StringIO(output),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        flash('导出失败：' + str(e), 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        site_domain = request.form.get('site_domain', '').strip()
        setting = Settings.query.filter_by(key='site_domain').first()
        
        if setting:
            setting.value = site_domain
        else:
            setting = Settings(key='site_domain', value=site_domain)
            db.session.add(setting)
        
        db.session.commit()
        flash('设置已更新', 'success')
    except Exception as e:
        flash('设置更新失败：' + str(e), 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    form = AIConfigForm()
    
    # 获取当前AI配置
    current_config = AIConfig.query.order_by(AIConfig.created_at.desc()).first()
    
    if current_config and not form.is_submitted():
        form.api_url.data = current_config.api_url
        form.api_key.data = current_config.api_key
        form.model_name.data = current_config.model_name
    
    if form.validate_on_submit():
        new_config = AIConfig(
            api_url=form.api_url.data,
            api_key=form.api_key.data,
            model_name=form.model_name.data
        )
        db.session.add(new_config)
        db.session.commit()
        flash('AI配置已更新！', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # 获取最近的梦境解析记录
    recent_dreams = Dream.query.order_by(Dream.created_at.desc()).all()
    
    # 获取网站设置
    site_domain = Settings.query.filter_by(key='site_domain').first()
    site_domain = site_domain.value if site_domain else ''
    
    return render_template('admin.html', 
                         form=form, 
                         recent_dreams=recent_dreams,
                         site_domain=site_domain)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('已退出登录！', 'info')
    return redirect(url_for('index'))

# 创建数据库表
with app.app_context():
    db.create_all()
    
    # 只在数据库完全为空时创建默认AI配置
    if AIConfig.query.count() == 0:
        default_config = AIConfig(
            api_url=DEFAULT_AI_CONFIG['api_url'],
            api_key=DEFAULT_AI_CONFIG['api_key'],
            model_name=DEFAULT_AI_CONFIG['model_name']
        )
        db.session.add(default_config)
        db.session.commit()

# 启动应用
if __name__ == '__main__':
    app.run(debug=True) 