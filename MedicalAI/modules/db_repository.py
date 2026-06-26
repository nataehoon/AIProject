from config import CONNECTION_STRING
from psycopg_pool import ConnectionPool
import streamlit as st

@st.cache_resource
def init_connection_pool():
    pool = ConnectionPool(conninfo=CONNECTION_STRING, min_size=2, max_size=10, open=True)
    return pool

def execute_select_query(query: str, params: tuple = None):
    pool = init_connection_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)

            return cur.fetchall()