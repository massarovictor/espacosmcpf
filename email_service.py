# email_service.py
import os
import smtplib
import logging
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Carrega as variáveis definidas no arquivo .env
load_dotenv()

def send_email(subject: str, body: str, to_email: str) -> None:
    """
    Envia um e-mail com o assunto e corpo especificados para o destinatário informado.

    Parâmetros:
    subject (str): O assunto do e-mail.
    body (str): O corpo do e-mail.
    to_email (str): O endereço de e-mail do destinatário.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL")
    
    # Cria o objeto de mensagem de e-mail
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        # Conectar ao servidor SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Segurança
            server.login(smtp_username, smtp_password)  # Autenticação
            server.sendmail(from_email, [to_email], msg.as_string())  # Envio do e-mail
            
            # Registra sucesso no log
            logging.info(f"E-mail enviado com sucesso para {to_email} | Assunto: {subject}")
    
    except Exception as e:
        # Registra erro no log
        logging.error(f"Erro ao enviar e-mail para {to_email}: {e}")
