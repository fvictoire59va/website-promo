from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# Configuration de la connexion à la base erpbtp_clients
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "erpbtp_clients")
DB_USER = os.getenv("DB_USER", "erp_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "motdepasse")

class ClientRequest(BaseModel):
    nom: str

@app.post("/client-id/")
def get_client_id(data: ClientRequest):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SELECT id FROM clients WHERE nom = %s ORDER BY id DESC LIMIT 1", (data.nom,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {"id": row[0]}
        else:
            raise HTTPException(status_code=404, detail="Client non trouvé")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
