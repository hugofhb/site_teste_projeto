import os
import io

from flask import Flask, request ,render_template
from tchan import ChannelScraper
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import date, timedelta
import telegram 
import pandas as pd
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from wordcloud import WordCloud, STOPWORDS
import base64
from PIL import Image





TELEGRAM_API_KEY = os.environ["TELEGRAM_API_KEY"]
bot = telegram.Bot(token=os.environ["TELEGRAM_API_KEY"])
TELEGRAM_ADMIN_ID = os.environ["TELEGRAM_ADMIN_ID"]
GOOGLE_SHEETS_CREDENTIALS = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
with open("credenciais.json", mode="w") as arquivo:
  arquivo.write(GOOGLE_SHEETS_CREDENTIALS)
conta = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json")
api = gspread.authorize(conta)
planilha = api.open_by_key("1YorOvbJkLGBQLn1T1y_Re0eAm58HOIsl5qIoJxiCbcY")
sheet = planilha.worksheet("Página1")

app = Flask(__name__)

menu = """ 
<a href="/">Página inicial</a> | <a href="/sobre">Sobre</a> | <a href="/contato">Contato</a> | <a href="/promocoes">PROMOÇÕES</a>  
<br>
"""

@app.route("/")
def index():
    menu = """<a href="/">Página inicial</a> | <a href="/sobre">Sobre</a> | <a href="/contato">Contato</a> | <a href="/promocoes">PROMOÇÕES</a><br>"""

    # Carrega os dados dos projetos de lei aprovados usando o pandas
    projetos_df = pd.DataFrame(projetos_aprovados(), columns=['projeto'])

    # Cria um gráfico de barras a partir dos dados
    fig = Figure()
    ax = fig.add_subplot(111)
    projetos_df.plot(kind='bar', ax=ax)

    # Cria a nuvem de palavras
    text = " ".join(projetos_df['projeto'].tolist())
    stopwords = set(STOPWORDS)
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)

    # Converte o gráfico de barras e a nuvem de palavras em objetos de imagem para serem exibidos na página
    output1 = BytesIO()
    FigureCanvas(fig).print_png(output1)
    output2 = BytesIO()
    wordcloud.to_image().save(output2, 'PNG')

    # Concatena as imagens em uma única imagem
    output = BytesIO()
    img1 = Image.open(output1)
    img2 = Image.open(output2)
    widths, heights = zip(*(i.size for i in [img1, img2]))
    total_width = sum(widths)
    max_height = max(heights)
    new_im = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for im in [img1, img2]:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]
    new_im.save(output, format='PNG')

    # Codifica a imagem em base64 para ser exibida na página
    encoded_image = base64.b64encode(output.getvalue()).decode()

    return menu + "<h1>Gráfico dos projetos de lei aprovados:</h1><br><img src='data:image/png;base64,{}'/>".format(encoded_image)

@app.route("/sobre")
def sobre():
    return menu + "Aqui vai o conteúdo da página Sobre"
  
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

        # Autenticação com as credenciais do Google Sheets
        GOOGLE_SHEETS_CREDENTIALS = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
        with open("credenciais.json", mode="w") as arquivo:
            arquivo.write(GOOGLE_SHEETS_CREDENTIALS)
        conta = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json")
        api = gspread.authorize(conta)
        planilha = api.open_by_key("1YorOvbJkLGBQLn1T1y_Re0eAm58HOIsl5qIoJxiCbcY") # Substitua pelo ID da sua planilha
        sheet = planilha.worksheet("Página1") # Substitua pelo nome da planilha ou da página que deseja acessar

        # Escrever os dados na planilha
        for projeto in projetos_aprovados:
            sheet.append_row([projeto])

        return projetos_aprovados
    else:
        return f"Erro: {response.status_code}"
      
@app.route("/telegram-bot", methods=["POST"])
def telegram_bot():
    update = request.json
    chat_id = update["message"]["chat"]["id"]
    message = update["message"]["text"]

    if message.lower() == '1':
        projetos = projetos_aprovados()
        if projetos:
            mensagem = "*Projetos de Lei aprovados na Câmara dos Deputados:* \n\n"
            for projeto in projetos:
                mensagem += f"• {projeto}\n"
        else:
            mensagem = "Nenhum projeto de lei foi aprovado recentemente."
    elif message.lower() == '2':
        mensagem = "🔗 *Acesse o site do nosso bot e veja as Pls aprovadas no dia de hoje:* 🔗\n https://site-teste-hugoh.onrender.com"
    elif message.lower() == '3':
        mensagem = "*Olá! Em que posso ajudar?* 😊"
    elif message.lower() == '4':
        mensagem = "*Obrigado por usar nosso bot! Até a próxima!* 👋"
    else:
        mensagem = "*Escolha uma das opções abaixo:* \n\n1. Ver projetos de lei aprovados\n2. Acessar o site do nosso robô\n3. Saudação\n4. Despedida"

    partes = []
    while mensagem:
        partes.append(mensagem[:4096])
        mensagem = mensagem[4096:]

    for parte in partes:
        nova_mensagem = {
            "chat_id": chat_id,
            "text": parte,
            "parse_mode": "HTML",
        }
        resposta = requests.post(f"https://api.telegram.org./bot{TELEGRAM_API_KEY}/sendMessage", data=nova_mensagem)
        print(resposta.text)

    return "ok"
      
