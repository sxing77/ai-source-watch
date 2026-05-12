#!/usr/bin/env python3
"""
发送监控报告邮件
使用 QQ 邮箱 SMTP
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SMTP_USER = "2294128005@qq.com"
# 注意：这里需要 QQ 邮箱的授权码，不是登录密码
# 获取方式：QQ邮箱设置 -> 账户 -> 开启SMTP服务 -> 获取授权码
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

TO_EMAIL = "2294128005@qq.com"


def send_report(report_path: str = "reports/latest.md"):
    """读取报告并发送邮件"""
    
    if not os.path.exists(report_path):
        print(f"报告文件不存在: {report_path}")
        return False
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # 解析报告内容
    lines = report_content.split('\n')
    new_count = 0
    for line in lines:
        if '新增数量：' in line:
            try:
                new_count = int(line.split('：')[1].strip())
            except:
                pass
            break
    
    # 邮件主题
    if new_count > 0:
        subject = f"🤖 AI新品监控 - 发现 {new_count} 个新项目"
    else:
        subject = "🤖 AI新品监控 - 今日无新增"
    
    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"AI监控 <{SMTP_USER}>"
    msg['To'] = TO_EMAIL
    
    # 纯文本版本
    text_part = MIMEText(report_content, 'plain', 'utf-8')
    msg.attach(text_part)
    
    # HTML 版本（简单转换）
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2563eb; }}
            h2 {{ color: #4b5563; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.5rem; }}
            ul {{ padding-left: 1.5rem; }}
            li {{ margin-bottom: 0.5rem; }}
            a {{ color: #2563eb; text-decoration: none; }}
            .meta {{ color: #6b7280; font-size: 0.875rem; }}
            .warning {{ background: #fef3c7; padding: 0.75rem; border-radius: 0.375rem; color: #92400e; }}
        </style>
    </head>
    <body>
        <pre style="white-space: pre-wrap; font-family: inherit;">{report_content}</pre>
        <hr>
        <p style="color: #6b7280; font-size: 0.875rem;">
            发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            查看面板：<a href="http://107.161.89.207:8081/ai-watch/">http://107.161.89.207:8081/ai-watch/</a>
        </p>
    </body>
    </html>
    """
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    # 发送邮件
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ 邮件已发送: {subject}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        send_report(sys.argv[1])
    else:
        send_report()
