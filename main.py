from fastapi import FastAPI
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import logging
import re

app = FastAPI()

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ColetorSpecs")

# Headers para fingir que somos um navegador (evita bloqueio 403 do GSMArena)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_page_content(url):
    try:
        # Timeout curto (3s) para não travar sua automação
        response = requests.get(url, headers=HEADERS, timeout=3)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts e estilos para limpar o texto
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Pega o texto e limpa espaços extras
            text = soup.get_text(separator=' ')
            clean_text = re.sub(r'\s+', ' ', text).strip()
            
            # Corta em 3500 caracteres (suficiente para a IA e economiza tokens)
            return clean_text[:3500]
    except Exception as e:
        logger.error(f"Erro ao ler site {url}: {e}")
    return None

def search_specs(model_name: str):
    logger.info(f"Buscando specs para: {model_name}")
    
    # Busca focada em ficha técnica
    query = f"{model_name} specs gsmarena phonearena devicespecifications"
    
    results = []
    try:
        # Tenta modo HTML (mais robusto)
        results = list(DDGS().text(keywords=query, max_results=5, backend="html"))
    except:
        try:
            # Fallback para Lite
            results = list(DDGS().text(keywords=query, max_results=5, backend="lite"))
        except Exception as e:
            return {"error": str(e), "content": ""}

    if not results:
        return {"content": "Nenhum resultado de busca encontrado."}

    # Estratégia: Tentar ler o conteúdo do 1º site técnico que encontrar
    full_content = ""
    source_url = ""

    for result in results:
        url = result.get('href', '')
        
        # Tenta entrar no site e pegar o texto real
        page_text = get_page_content(url)
        
        if page_text and len(page_text) > 500:
            full_content = page_text
            source_url = url
            break # Achou um bom texto? Para e retorna ele.
    
    # Se não conseguiu entrar em nenhum site (bloqueio), junta os resumos (snippets)
    if not full_content:
        logger.warning("Falha ao ler sites. Usando snippets.")
        snippets = [r.get('body', '') for r in results]
        full_content = " | ".join(snippets)
        source_url = "DuckDuckGo Snippets (Leitura falhou)"

    return {
        "model": model_name,
        "source": source_url,
        "content_length": len(full_content),
        "raw_text": full_content
    }

@app.get("/check")
def check(model: str):
    return search_specs(model)