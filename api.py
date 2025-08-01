from fastapi import FastAPI, HTTPException
import pandas as pd
import psycopg2
from http import HTTPStatus
from pydantic import BaseModel

class CustomerCreate(BaseModel):
    customer_name: str
    email: str
    phone_number: str
    address_line_1: str
    city: str

app = FastAPI()

connection = psycopg2.connect(database="postgres", user="postgres.jdghuqjbqcauhybwywzp", password="abclu3b3rr!3sz234", host="aws-0-eu-west-2.pooler.supabase.com", port=5432)

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

# def execute_query(sql: str):
#     try:
#         cursor = connection.cursor()
#         print(sql)
#         cursor.execute(sql)
#         # Fetch all rows from database
#         record = cursor.fetchall()
#         if len(record) == 0:
#             raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
#         return record
#     #except Exception as e:
#      #   raise HTTPStatus.NOT_FOUND
#     finally:
#         if cursor:
#             cursor.close()

def handle_create_customer(customer: CustomerCreate):
    db_query = """INSERT INTO toni_schema.customer
    (customer_name, email, phone_number, address_line_1, city)
    VALUES (%s, %s, %s, %s, %s)"""
    params = (
        customer.customer_name,
        customer.email,
        customer.phone_number,
        customer.address_line_1,
        customer.city
    )
    return execute_query(db_query, params)

def handle_update_customer(customer_id: int, customer: CustomerCreate):
    db_query = """UPDATE toni_schema.customer
    SET customer_name = %s,
        email = %s,
        phone_number = %s,
        address_line_1 = %s,
        city = %s
    WHERE customer_id = %s"""
    params = (
        customer.customer_name,
        customer.email,
        customer.phone_number,
        customer.address_line_1,
        customer.city,
        customer_id
    )
    return execute_query(db_query, params)

def handle_update_order_status(order_id: int, new_status_id: int):
    db_query = """UPDATE toni_schema.orders
    SET order_status_id = %s
    WHERE order_id = %s"""
    return execute_query(db_query, (new_status_id, order_id))

def handle_delete_order(order_id: int):
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM toni_schema.order_line WHERE order_id = %s", (order_id,))
            cursor.execute("DELETE FROM toni_schema.orders WHERE order_id = %s", (order_id,))
        connection.commit()
        return {"status": "success"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

def handle_get_customers():
    db_query = "SELECT customer_id, customer_name, email, city FROM toni_schema.customer"
    return fetch_query(db_query)

def handle_get_customer_name(name: str):
    db_query = "SELECT * FROM toni_schema.customer WHERE customer_name ILIKE %s"
    params = (f"{name}%",)
    return fetch_query(db_query, params)

def handle_get_customer_id(customer_id: int):
    db_query = "SELECT * FROM toni_schema.customer WHERE customer_id = %s"
    return fetch_query(db_query, (customer_id,))

def handle_get_all_products():
    db_query = "SELECT product_id, product_name, selling_price FROM toni_schema.product"
    return fetch_query(db_query)

def handle_get_product(product_id: int):
    db_query = "SELECT * FROM toni_schema.product WHERE product_id = %s"
    return fetch_query(db_query, (product_id,))

def handle_get_order_details(order_id: int):
    db_query = """SELECT o.order_id, o.order_date, o.total_amount, c.customer_name, c.email, s.status_name
    FROM toni_schema.orders o
    JOIN toni_schema.customer c ON o.customer_id = c.customer_id
    JOIN toni_schema.order_status s ON o.order_status_id = s.order_status_id
    WHERE o.order_id = %s"""
    return fetch_query(db_query, (order_id,))

def handle_get_order_items(order_id: int):
    db_query = """SELECT ol.quantity, p.product_name, p.selling_price, (ol.quantity * p.selling_price) AS line_total
    FROM toni_schema.order_line ol
    JOIN toni_schema.product p ON ol.product_id = p.product_id
    WHERE ol.order_id = %s"""
    return fetch_query(db_query, (order_id,))

def handle_get_customer_orders(customer_id: int):
    db_query = """SELECT o.order_id, o.order_date, o.total_amount, s.status_name
    FROM toni_schema.orders o
    JOIN toni_schema.order_status s ON o.order_status_id = s.order_status_id
    WHERE o.customer_id = %s
    ORDER BY o.order_date DESC"""
    return fetch_query(db_query, (customer_id,))

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/customers')
def create_customer(customer: CustomerCreate):
    return handle_create_customer(customer)

@app.get('/customers')
async def get_customers():
    return handle_get_customers()

@app.get('/customers/by-name/{name}')
async def get_customer_name(name: str):
    return handle_get_customer_name(name)

@app.get('/customers/by-id/{customer_id}')
async def get_customer_id(customer_id: int):
    return handle_get_customer_id(customer_id)

@app.get('/products')
async def get_all_products():
    return handle_get_all_products()

@app.get('/products/{product_id}')
async def get_product(product_id: int):
    return handle_get_product(product_id)

@app.get('/orders/{order_id}')
async def get_order_details(order_id: int):
    return handle_get_order_details(order_id)

@app.get('/orders/{order_id}/items')
async def get_order_items(order_id: int):
    return handle_get_order_items(order_id)

@app.get('/customers/{customer_id}/orders')
async def get_customer_orders(customer_id: int):
    return handle_get_customer_orders(customer_id)

@app.put('/customers/{customer_id}')
async def update_customer(customer_id: int, customer: CustomerCreate):
    return handle_update_customer(customer_id, customer)

@app.put('/orders/{order_id}/status')
async def update_order_status(order_id: int, new_status_id: int):
    return handle_update_order_status(order_id, new_status_id)

@app.delete('/orders/{order_id}')
async def delete_order(order_id: int):
    return handle_delete_order(order_id)
