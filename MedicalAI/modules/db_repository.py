from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

@st.cache_resource
def init_connection_pool():
    pool = ConnectionPool(conninfo=os.getenv("CONNECTION_STRING"), min_size=2, max_size=10, open=True)
    return pool

def execute_select_query(query: str, params: tuple = None):
    pool = init_connection_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)

            return cur.fetchall()