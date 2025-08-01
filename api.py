from fastapi import FastAPI, HTTPException
import pandas as pd
import psycopg2
from http import HTTPStatus
from pydantic import BaseModel

app = FastAPI()

# connection = psycopg2.connect(database="postgres", user="postgres.jdghuqjbqcauhybwywzp", password="abclu3b3rr!3sz234", host="aws-0-eu-west-2.pooler.supabase.com", port=5432)

def fetch_query(sql: str, params: tuple = ()):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if cursor:
            cursor.close()

def execute_query(sql: str, params: tuple = ()):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            connection.commit()
            return {"status": "success"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if cursor:
            cursor.close()

def handle_get_macros():
    db_query = "SELECT * FROM macronutrient_tool"
    return fetch_query(db_query)

def handle_get_micros():
    db_query - "SELECT * FROM micronutrient_tool"
    return fetch_query(db_query)

@app.get("/")
async def root():
    return {"message": "Hello World"}

