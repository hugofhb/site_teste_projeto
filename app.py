import os

from flask import Flask, request ,render_template
from tchan import ChannelScraper
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import date, timedelta
import telegram
import pandas as pd


TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
bot = telegram.Bot(token=os.environ["TELEGRAM_API_KEY"])
TELEGRAM_ADMIN_ID = os.environ["TELEGRAM_ADMIN_ID"]
GOOGLE_SHEETS_CREDENTIALS = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
with open("credenciais.json", mode="w") as arquivo:
  arquivo.write(GOOGLE_SHEETS_CREDENTIALS)
conta = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json")
api = gspread.authorize(conta)
planilha = api.open_by_key("1srTpWeSZKLAxMcw_OqhKmzEJxwDPjP7jhvvNGudtx-E")
sheet = planilha.worksheet("Página1")

app = Flask(__name__)

menu = """ 
<a href="/">Página inicial</a> | <a href="/sobre">Sobre</a> | <a href="/contato">Contato</a> | <a href="/promocoes">PROMOÇÕES</a>  
<br>
"""

@app.route("/")
def index():
  return menu + "Olá, este é o site do robô sobre PLs aprovadas."

@app.route("/sobre")
def sobre():
  return menu + "Aqui vai o conteúdo da página Sobre"

@app.route("/contato")
def contato():
  return menu + "Aqui vai o conteúdo da página Contato"

@app.route("/promocoes2")
def promocoes2():
  conteudo = menu + """
  Encontrei as seguintes promoções no <a href="https://t.me/promocoeseachadinhos">@promocoeseachadinhos</a>:
  <br>
  <ul>
  """
  scraper = ChannelScraper()
  contador = 0
  for message in scraper.messages("promocoeseachadinhos"):
    contador += 1
    texto = message.text.strip().splitlines()[0]
    conteudo += f"<li>{message.created_at} {texto}</li>"
    if contador == 10:
      break
  return conteudo + "</ul>"

@app.route("/dedoduro")
def dedoduro():
  mensagem = {"chat_id": TELEGRAM_ADMIN_ID, "text": "Alguém acessou a página dedo duro!"}
  resposta = requests.post(f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage", data=mensagem)
  return f"Mensagem enviada. Resposta ({resposta.status_code}): {resposta.text}"

@app.route("/dedoduro2")
def dedoduro2():
  sheet.append_row(["HUGO", "H", "a partir do Flask"])
  return "Planilha escrita!"

      

def projetos_aprovados():
    hoje = date.today().strftime('%Y-%m-%d')
    ontem = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?dataInicio={ontem}&dataFim={hoje}&siglaTipo=PL&ordenarPor=ano"
    response = requests.get(url)
    
    if response.status_code == 200:
        dados = response.json()['dados']
        projetos_aprovados = []
        
        for projeto in dados:
            tipo = projeto['siglaTipo']
            numero = projeto['numero']
            ementa = projeto['ementa']
            projetos_aprovados.append(f"{tipo} {numero} - {ementa}")
            
        return projetos_aprovados
    else:
        return f"Erro: {response.status_code}"
      
@app.route("/telegram-bot", methods=["POST"])
def telegram_bot():
    update = request.json
    chat_id = update["message"]["chat"]["id"]
    message = update["message"]["text"]

    if message.lower() == '1':
        # code to display a list of projects approved in the last day
        projetos = projetos_aprovados()
        nova_mensagem = {
            "chat_id": chat_id,
            "text": "Projetos de Lei aprovados na Câmara dos Deputados:\n" + "\n".join(projetos),
        }
    elif message.lower() == '2':
        # code to display a link to the Chamber of Deputies website
        nova_mensagem = {
            "chat_id": chat_id,
            "text": "Acesse o site da Câmara dos Deputados para mais detalhes: https://www.camara.leg.br/busca-portal/projetoslegislativos/",
        }
    elif message.lower() == '3':
        # code to display a greeting message
        nova_mensagem = {
            "chat_id": chat_id,
            "text": "Olá! Em que posso ajudar?",
        }
    elif message.lower() == '4':
        # code to display a farewell message
        nova_mensagem = {
            "chat_id": chat_id,
            "text": "Obrigado por usar nosso bot! Até a próxima!",
        }
    else:
        # default message if no valid option is chosen
        nova_mensagem = {
            "chat_id": chat_id,
            "text": "Escolha uma das opções abaixo:\n1. Ver projetos de lei aprovados\n2. Acessar o site da Câmara dos Deputados\n3. Saudação\n4. Despedida",
        }

    resposta = requests.post(f"https://api.telegram.org./bot{TELEGRAM_API_KEY}/sendMessage", data=nova_mensagem)
    print(resposta.text)
    return "ok"      
      
      
      
