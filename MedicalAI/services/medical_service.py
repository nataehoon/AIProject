from modules.db_repository import execute_select_query, execute_non_query
from models.mediinfo import Mediinfo
import os
from dotenv import load_dotenv

load_dotenv()

class MedicalService:
    @staticmethod
    def get_my_mediinfo(id: int) -> Mediinfo | None:
        qeury = "SELECT * FROM mediinfo WHERE id=%s"
        params = (id,)

        raw_rows = execute_select_query(query=qeury, params=params)

        if not raw_rows:
            return None

        return Mediinfo(**raw_rows[0])

    @staticmethod
    def save_my_mediinfo(my_medi: Mediinfo) -> bool | None:
        query = "INSERT INTO mediinfo(member_id, modality, file_name, analyzed_text) VALUES(%s, %s, %s, %s)"
        params = (my_medi.member_id, my_medi.modality, my_medi.file_name, my_medi.analyzed_text)

        return execute_non_query(query, params)

        



