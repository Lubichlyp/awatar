from fastapi import FastAPI, HTTPException
import generowanie

app = FastAPI(title="Generator wideo")

@app.get("/")
def root():
    return {"info": "API generatora wideo"}

@app.get("/generuj/{news_id}")
def generuj(news_id: int):
    try:
        wynik = generowanie.run(news_id)
        return {"status": "ok", "wynik": wynik}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))