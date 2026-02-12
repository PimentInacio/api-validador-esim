from fastapi import FastAPI
from duckduckgo_search import DDGS
import logging
import time

app = FastAPI()

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValidadorESIM")

def search_esim_capability(model_name: str):
    logger.info(f"Validando: {model_name}")
    
    # Query focada: Tenta forçar o aparecimento da palavra eSIM junto com o site GSMArena
    query = f"{model_name} gsmarena specs esim"
    
    results = []
    backend_used = "none"

    # TENTATIVA 1: Backend HTML (Mais robusto)
    try:
        logger.info("Tentando backend HTML...")
        # O backend html simula um navegador real
        results = list(DDGS().text(keywords=query, max_results=5, backend="html"))
        backend_used = "html"
    except Exception as e:
        logger.error(f"Erro HTML: {e}")

    # TENTATIVA 2: Backend Lite (Se o HTML falhar ou vier vazio)
    if not results:
        try:
            logger.info("Tentando backend Lite (Fallback)...")
            time.sleep(1) # Respira 1 segundo pra não parecer spam
            results = list(DDGS().text(keywords=query, max_results=5, backend="lite"))
            backend_used = "lite"
        except Exception as e:
            logger.error(f"Erro Lite: {e}")

    # Se depois das duas tentativas ainda estiver vazio
    if not results:
        return {
            "compatible": 0, 
            "reason": "Bloqueio de IP ou sem resultados nos dois modos.",
            "backend_attempted": backend_used
        }

    # ANÁLISE DOS RESULTADOS
    found_snippets = []

    for result in results:
        body = result.get('body', '').lower()
        title = result.get('title', '').lower()
        url = result.get('href', '').lower()
        
        # Guarda um pedacinho pra gente ver o que ele leu (Debug)
        found_snippets.append(body[:150])

        # Verificações
        has_esim = 'esim' in body or 'embedded sim' in body
        
        # Só nega se disser explicitamente "NO eSIM"
        has_negative = 'no esim' in body

        if has_esim and not has_negative:
            # SUCESSO!
            return {
                "compatible": 1,
                "model": model_name,
                "confidence": "high",
                "source": url,
                "evidence": body,
                "backend": backend_used
            }

    # Se leu os textos e não achou a palavra eSIM
    return {
        "compatible": 0,
        "model": model_name,
        "reason": "Resultados encontrados, mas a palavra eSIM não estava neles.",
        "backend": backend_used,
        "debug_snippets": found_snippets
    }

@app.get("/")
def home():
    return {"status": "Online", "version": "V4 - Dual Backend"}

@app.get("/check")
def check(model: str):
    return search_esim_capability(model)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)