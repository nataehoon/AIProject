from modules.db_repository import execute_select_query
from models.member import Member, MemberProfile, UserSessionDTO
from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

class MemberService:

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"

    @staticmethod
    def login_process(user_id: str, user_pw: str) -> str | None:
        query = "SELECT * FROM member WHERE user_id = %s"
        params = (user_id,)

        raw_rows = execute_select_query(query, params)

        if not raw_rows:
            return None

        member_info = Member(**raw_rows[0])

        if user_pw == member_info.password:
            query = "SELECT * FROM member_profile WHERE id = %s"
            params = (member_info.id,)

            raw_rows = execute_select_query(query, params)

            if not raw_rows:
                return None

            member_profile = MemberProfile(**raw_rows[0])

            payload = {"id": member_profile.id, "user_id": user_id, "name": member_profile.name, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}

            token = jwt.encode(payload, MemberService.SECRET_KEY, algorithm=MemberService.ALGORITHM)

            return token
        else:
            return False
        
    @staticmethod
    def login_by_token(token: str) -> UserSessionDTO | None:
        try:
            payload = jwt.decode(token, MemberService.SECRET_KEY, algorithms=[MemberService.ALGORITHM])

            return UserSessionDTO(
                id=payload["id"],
                user_id=payload["user_id"],
                name=payload["name"]
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None