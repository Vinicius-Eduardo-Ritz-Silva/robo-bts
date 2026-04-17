import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import requests

# ==========================================
# CONFIGURAÇÕES DE SENHAS SEGURAS (GITHUB SECRETS)
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ==========================================
# SITES A SEREM MONITORADOS E REGRAS
# ==========================================
SITES = [
    {
        "url": "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10",
        "termo": "ESGOTADO",
        "qtd_esperada": 1  # Ticketmaster costuma ter 1 banner de Esgotado geral
    },
    {
        "url": "https://bts.buyticketbrasil.com/ingressos?data=31-10-2026",
        "termo": "ESGOTADO",
        "qtd_esperada": 8  # BuyTicket listando 4 setores esgotados
    }
]

def send_email(url):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚨 Preparando envio de e-mail alertando sobre a URL: {url}")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = "🚨 ALERTA: INGRESSO BTS DISPONÍVEL! 🚨"

    body = f"""
Um ingresso para o show do BTS pode estar disponível! 💜

A tag 'Esgotado' não foi encontrada na página.

Corra para o site agora mesmo: 
{url}

Boa sorte!
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ E-mail de alerta enviado com sucesso para {EMAIL_RECEIVER}!")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ Erro ao enviar e-mail: {e}")

def send_telegram(url):
    if not TELEGRAM_CHAT_ID:
        return
        
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Disparando notificação no Telegram!")
    mensagem = f"🚨 *INGRESSO DO BTS DISPONÍVEL!* 💜\n\nCorra para o site: {url}"
    
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ Notificação do Telegram enviada no seu celular!")
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Erro no Telegram: {response.text}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ Falha ao tentar conectar na API do Telegram: {e}")

def check_tickets():
    print(f"\n--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando nova verificação de ingressos ---")
    
    # Configurações do Chrome (Headless: Roda em modo invisível, sem abrir a janela no seu rosto)
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Roda o navegador oculto, comente essa linha se quiser ver ele abrindo visualmente
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3") # Menos poluição visual no terminal
    
    # O webdriver do Selenium > 4.6 já baixa o ChromeDriver correto sozinho!
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
         print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ Erro ao iniciar o Google Chrome. Ele está instalado? Erro: {e}")
         return
    
    for site in SITES:
        url = site["url"]
        termo = site["termo"]
        qtd_esperada = site["qtd_esperada"]
        
        try:
            print(f"Acessando: {url}")
            driver.get(url)
            
            # Aguarda a página carregar o 'body'
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Dá mais 3 segundos de garantia para aplicações como React carregarem tudo (caso da BuyTicketBrasil)
            time.sleep(3)  
            
            # Pega todo o texto visível na página e converte para maiúsculo para facilitar a busca
            page_text = driver.execute_script("return document.body.innerText;").upper()
            
            # Conta quantas vezes a palavra aparece
            ocorrencias = page_text.count(termo)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📊 Verificando '{termo}': Encontrado {ocorrencias} vezes no texto.")
            
            if ocorrencias < qtd_esperada:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚀 POSSÍVEL DISPONIBILIDADE NA URL (qtd caiu para {ocorrencias}): {url}")
                send_email(url)
                send_telegram(url)
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔒 Continua esgotado em: {url}")
                
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Erro ao tentar verificar a URL {url}: {e}")
            
    driver.quit()
    print(f"--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] Verificação finalizada. Aguardando próximo ciclo. ---")

if __name__ == "__main__":
    print("=========================================================")
    print("💜 ROBÔ MONITOR DE INGRESSOS DO BTS - GITHUB ACTIONS 💜")
    print("=========================================================")
    
    # No GitHub Actions nós rodamos tudo solto, pois a infraestrutura do GitHub Action 
    # é quem assume o papel do Agendador! A máquina abre, roda isso, e se destrói.
    if TELEGRAM_TOKEN and not TELEGRAM_CHAT_ID:
        print("⚠️ VOCÊ PRECISA DEFINIR TANTOS OS TOKENS QUANTO O CHAT_ID NO SEGREDO DO GITHUB!")
        
    check_tickets()
