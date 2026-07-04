from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
import streamlit as st
from dotenv import load_dotenv
import os
from typing import List, Tuple

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

def execute_non_query(query: str, params: tuple = None) -> int:
    pool = init_connection_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)

                conn.commit()

                return cur.rowcount
            except Exception as e:
                print(f"[non_query 실패]: {e}")
                return cur.rowcount

def execute_transaction_query(queries_params: List[Tuple[str, tuple]]) -> bool:
    pool = init_connection_pool()
    with pool.connection() as conn:
        try:
            with conn.cursor() as cur:
                for query, params in queries_params:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)

            conn.commit()
            return True
        except Exception as e:
            print(f"[실패]: {e}")
            conn.rollback()
            return False