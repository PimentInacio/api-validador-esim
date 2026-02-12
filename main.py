from fastapi import FastAPI
from duckduckgo_search import DDGS
import logging

app = FastAPI()

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValidadorESIM")

# LISTA VIP: Sites que confiamos 100%
TRUSTED_DOMAINS = [
    "gsmarena.com", 
    "airalo.com", 
    "holafly.com", 
    "apple.com", 
    "samsung.com", 
    "motorola.com", 
    "mi.com", 
    "devicespecifications.com",
    "tudocelular.com", 
    "tecmundo.com.br", 
    "kimovil.com"
]

def search_esim_capability(model_name: str):
    logger.info(f"Validando: {model_name}")
    
    # Busca técnica aberta
    query = f"{model_name} technical specifications esim support"
    
    try:
        # Busca até 10 resultados
        results = DDGS().text(keywords=query, max_results=10, backend="html")
    except Exception as e:
        logger.error(f"Erro DuckDuckGo: {e}")
        return {"compatible": 0, "error": str(e)}

    if not results:
        return {"compatible": 0, "reason": "Sem resultados"}

    esim_confirmed = False
    trusted_source_found = False
    evidence_text = ""
    source_url = ""

    for result in results:
        body = result.get('body', '').lower()
        url = result.get('href', '').lower()

        # 1. É site VIP?
        is_vip = any(domain in url for domain in TRUSTED_DOMAINS)

        # 2. Tem termos positivos?
        has_positive = 'esim' in body or 'embedded sim' in body or 'e-sim' in body

        # 3. Tem termos negativos (pra evitar falso positivo)?
        has_negative = ('no esim' in body or 'not support esim' in body or 'nano-sim only' in body)

        if has_positive and not has_negative:
            esim_confirmed = True
            evidence_text = body
            source_url = url
            if is_vip:
                trusted_source_found = True
                break # Achou no VIP, encerra e confirma.

    if esim_confirmed:
        return {
            "compatible": 1,
            "model": model_name,
            "confidence": "high" if trusted_source_found else "medium",
            "source": source_url,
            "evidence": evidence_text
        }
    else:
        return {
            "compatible": 0,
            "model": model_name,
            "reason": "Nenhuma menção explícita encontrada"
        }

@app.get("/")
def home():
    return {"status": "Online", "service": "Validador eSIM V2"}

@app.get("/check")
def check(model: str):
    return search_esim_capability(model)