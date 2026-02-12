from fastapi import FastAPI
from duckduckgo_search import DDGS
import logging

app = FastAPI()

# Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValidadorESIM")

def search_esim_capability(model_name: str):
    logger.info(f"Validando: {model_name}")
    
    # === MUDANÇA PRINCIPAL AQUI ===
    # Em vez de buscar na internet toda, vamos direto na fonte técnica.
    # Adicionamos 'gsmarena' para pegar o snippet técnico que sempre diz "Nano-SIM and eSIM"
    query = f"{model_name} gsmarena specs esim"
    
    try:
        # Puxamos 5 resultados. O backend 'api' costuma trazer snippets melhores.
        results = DDGS().text(keywords=query, max_results=5, backend="api")
    except Exception as e:
        return {"compatible": 0, "error": str(e)}

    if not results:
        return {"compatible": 0, "reason": "Sem resultados"}

    # Debug: Vamos guardar o que ele achou pra você ver se der erro
    found_snippets = []

    for result in results:
        body = result.get('body', '').lower()
        title = result.get('title', '').lower()
        url = result.get('href', '').lower()
        
        found_snippets.append(body[:100]) # Guarda o começo do texto pra debug

        # Palavras-chave de sucesso
        has_esim = 'esim' in body or 'embedded sim' in body
        
        # Palavras-chave de fracasso (apenas se for explícito que NÃO tem)
        # Removemos 'nano-sim' da negativa porque celulares modernos têm OS DOIS.
        has_negative = 'no esim' in body

        if has_esim and not has_negative:
            # BINGO!
            return {
                "compatible": 1,
                "model": model_name,
                "source": url,
                "evidence": body
            }

    # Se chegou aqui, não achou. Vamos retornar o que ele leu pra gente entender o erro.
    return {
        "compatible": 0,
        "model": model_name,
        "reason": "Não encontrei a palavra eSIM nos resultados.",
        "debug_snippets": found_snippets
    }

@app.get("/")
def home():
    return {"status": "Online", "version": "V3 - GSMArena Focus"}

@app.get("/check")
def check(model: str):
    return search_esim_capability(model)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)