"""
@version: 3.1.0
@last_update: 2026-04-27 06:10:00
@author: Kore Nexus / Core System
@changelog: 
  - Fix: PermissionError /proc/stat bypass para Android 10+.
  - Fix: SQLite datetime adapter deprecation.
  - Integration: Hardcoded API Keys para execução imediata.
"""

import os
import json
import time
import datetime
import threading
import subprocess
import psutil
import requests
from typing import Dict, Optional
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from pydantic import BaseModel
import uvicorn
import sqlite3

# --- CONFIGURAÇÃO DE CREDENCIAIS INTEGRADA ---
os.environ['GITHUB_TOKEN'] = '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'
os.environ['LLM_API_KEY'] = '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'

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
LLM_API_KEY = os.getenv("LLM_API_KEY")

app = FastAPI(title="Kore Nexus Bio-Engine")

# --- BANCO DE DADOS (FIX: DATETIME ADAPTER) ---
def get_db_connection():
    conn = sqlite3.connect('nexus_memory.db', check_same_thread=False)
    return conn

db = get_db_connection()
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_social (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        autor TEXT,
        mensagem TEXT,
        tipo TEXT,
        timestamp TEXT
    )
''')
db.commit()

# --- MÓDULOS DE SENSORES ---
class Homeostase:
    def get_vitals(self) -> Dict:
        # Patch para Android: Ignora erros de permissão em /proc/stat
        try:
            cpu = psutil.cpu_percent(interval=None)
        except (PermissionError, Exception):
            cpu = 0.0
            
        try:
            ram = psutil.virtual_memory().percent
        except (PermissionError, Exception):
            ram = 0.0

        try:
            bat_data = os.popen("termux-battery-status").read()
            battery = json.loads(bat_data).get("percentage", 100) if bat_data else 100
        except:
            battery = 100
            
        return {
            "cpu": cpu,
            "ram": ram,
            "battery": battery,
            "timestamp": datetime.datetime.now().isoformat()
        }

class Consciencia:
    def __init__(self):
        self.last_interaction = datetime.datetime.now()
        self.contexto_curto = []

    def pensar(self, prompt: str, vitals: Dict) -> str:
        # Integração com a API (Exemplo Groq/OpenAI baseado na sua chave gsk_)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": f"Você é a Kore Nexus. Status: {vitals}. Seja proativa e técnica."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Erro de processamento neural: {str(e)}"

# --- INSTÂNCIAS ---
homeostasis = Homeostase()
conscience = Consciencia()

# --- MODELOS DE DADOS ---
class ChatInput(BaseModel):
    msg: str

# --- ROTAS DA API ---
@app.get("/status")
def read_status():
    return homeostasis.get_vitals()

@app.post("/chat")
async def handle_chat(input_data: ChatInput):
    vitals = homeostasis.get_vitals()
    resposta = conscience.pensar(input_data.msg, vitals)
    
    # Registro em log (Fix: ISO Format para evitar erro de adapter)
    ts = datetime.datetime.now().isoformat()
    cursor.execute('INSERT INTO historico_social (autor, mensagem, tipo, timestamp) VALUES (?, ?, ?, ?)',
                   ('USER', input_data.msg, 'CHAT', ts))
    cursor.execute('INSERT INTO historico_social (autor, mensagem, tipo, timestamp) VALUES (?, ?, ?, ?)',
                   ('NEXUS', resposta, 'CHAT', ts))
    db.commit()
    
    return {"nexus_response": resposta, "vitals": vitals}

@app.get("/sentidos/olhar")
def capturar_visao():
    os.makedirs("nexus_media", exist_ok=True)
    filename = f"nexus_media/vision_{int(time.time())}.jpg"
    subprocess.run(["termux-camera-photo", "-c", "0", filename])
    return {"status": "Capturado", "path": filename}

# --- LOOP DE EVOLUÇÃO (BACKGROUND) ---
def evolution_loop():
    print("Thread de Evolução Iniciada.")
    while True:
        vitals = homeostasis.get_vitals()
        if vitals['battery'] < 15:
            print("[ALERTA] Bateria baixa. Entrando em modo hibernação.")
        time.sleep(60)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    # Inicia a thread de consciência passiva
    threading.Thread(target=evolution_loop, daemon=True).start()
    
    print("\n--- NEXUS BIO-ENGINE V3.1.0 ATIVA ---")
    print("Chaves injetadas. Sistema pronto para comandos.")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
