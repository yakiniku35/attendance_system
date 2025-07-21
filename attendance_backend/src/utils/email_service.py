import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

class EmailService:
    def __init__(self):
        # 郵件服務配置（可以從環境變數讀取）
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', 'your-email@gmail.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', 'your-app-password')
        self.from_email = os.getenv('FROM_EMAIL', 'your-email@gmail.com')
        self.from_name = os.getenv('FROM_NAME', '出缺席管理系統')
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """發送郵件"""
        try:
            # 創建郵件對象
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加文本內容
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加HTML內容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 連接SMTP服務器並發送
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return True, "郵件發送成功"
        
        except Exception as e:
            print(f"郵件發送失敗: {str(e)}")
            return False, f"郵件發送失敗: {str(e)}"
    
    def send_registration_welcome(self, user_email, user_name, verification_token=None):
        """發送註冊歡迎郵件"""
        subject = "歡迎加入出缺席管理系統"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 歡迎加入出缺席管理系統</h1>
                </div>
                <div class="content">
                    <h2>親愛的 {user_name}，</h2>
                    <p>恭喜您成功註冊出缺席管理系統！我們很高興您加入我們的平台。</p>
                    
                    <h3>系統功能介紹：</h3>
                    <ul>
                        <li>📚 課程管理與加入</li>
                        <li>📝 出缺席表單填寫</li>
                        <li>📊 個人出席統計分析</li>
                        <li>🔔 即時通知提醒</li>
                    </ul>
                    
                    {f'''
                    <div style="background: #e8f4fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3>📧 郵件驗證</h3>
                        <p>為了確保您的帳號安全，請點擊下方按鈕驗證您的郵件地址：</p>
                        <a href="https://your-domain.com/verify-email?token={verification_token}" class="button">驗證郵件地址</a>
                        <p><small>此連結將在24小時後失效</small></p>
                    </div>
                    ''' if verification_token else ''}
                    
                    <p>如果您有任何問題，請隨時聯繫我們的客服團隊。</p>
                    
                    <p>祝您使用愉快！<br>
                    出缺席管理系統團隊</p>
                </div>
                <div class="footer">
                    <p>此郵件由系統自動發送，請勿直接回覆</p>
                    <p>發送時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        歡迎加入出缺席管理系統
        
        親愛的 {user_name}，
        
        恭喜您成功註冊出缺席管理系統！
        
        系統功能包括：
        - 課程管理與加入
        - 出缺席表單填寫
        - 個人出席統計分析
        - 即時通知提醒
        
        {f'請使用以下連結驗證您的郵件地址：https://your-domain.com/verify-email?token={verification_token}' if verification_token else ''}
        
        如有問題請聯繫客服團隊。
        
        出缺席管理系統團隊
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_password_reset(self, user_email, user_name, otp_code, reset_token):
        """發送密碼重置郵件"""
        subject = "密碼重置驗證碼"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .otp-code {{ background: #fff; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px; }}
                .otp-number {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; }}
                .warning {{ background: #fed7d7; border-left: 4px solid #f56565; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 密碼重置請求</h1>
                </div>
                <div class="content">
                    <h2>親愛的 {user_name}，</h2>
                    <p>我們收到了您的密碼重置請求。請使用以下驗證碼完成密碼重置：</p>
                    
                    <div class="otp-code">
                        <p>您的驗證碼是：</p>
                        <div class="otp-number">{otp_code}</div>
                        <p><small>此驗證碼將在15分鐘後失效</small></p>
                    </div>
                    
                    <div class="warning">
                        <h3>⚠️ 安全提醒</h3>
                        <ul>
                            <li>請勿將此驗證碼分享給任何人</li>
                            <li>如果您沒有請求密碼重置，請忽略此郵件</li>
                            <li>驗證碼僅能使用一次</li>
                        </ul>
                    </div>
                    
                    <p>如果您有任何疑問，請聯繫我們的客服團隊。</p>
                    
                    <p>出缺席管理系統團隊</p>
                </div>
                <div class="footer">
                    <p>此郵件由系統自動發送，請勿直接回覆</p>
                    <p>發送時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        密碼重置驗證碼
        
        親愛的 {user_name}，
        
        我們收到了您的密碼重置請求。
        
        您的驗證碼是：{otp_code}
        
        此驗證碼將在15分鐘後失效，請勿分享給任何人。
        
        如果您沒有請求密碼重置，請忽略此郵件。
        
        出缺席管理系統團隊
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_attendance_reminder(self, user_email, user_name, form_title, course_name, deadline):
        """發送出缺席提醒郵件"""
        subject = f"出缺席提醒 - {course_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .reminder-box {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #ed8936; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ 出缺席提醒</h1>
                </div>
                <div class="content">
                    <h2>親愛的 {user_name}，</h2>
                    <p>您有一個出缺席表單尚未填寫，請及時完成。</p>
                    
                    <div class="reminder-box">
                        <h3>📋 表單資訊</h3>
                        <p><strong>課程：</strong>{course_name}</p>
                        <p><strong>表單：</strong>{form_title}</p>
                        <p><strong>截止時間：</strong>{deadline}</p>
                    </div>
                    
                    <p>請盡快登入系統完成出缺席填寫。</p>
                    
                    <a href="https://your-domain.com/login" class="button">立即填寫</a>
                    
                    <p>出缺席管理系統團隊</p>
                </div>
                <div class="footer">
                    <p>此郵件由系統自動發送，請勿直接回覆</p>
                    <p>發送時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

# 創建全局郵件服務實例
email_service = EmailService()

