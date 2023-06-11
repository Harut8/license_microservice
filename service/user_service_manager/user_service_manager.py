from auth.auth import decode_token
from uuid import UUID
from repository.user_db_manager.user_db_manager import UserDbManager
from models.user_model.user_model import UserInfo, AccountRegModel
from typing import Union
from service.user_service_manager.user_service_interface import UserServiceInterface
from service.url_token_generators.token_creator import create_token_for_email_verify, generate_url_for_email_verify
from mailing.verify_mailing.send_account_verify_link import send_email_verify_link
from asyncpg import Record


class UserServiceManager(UserServiceInterface):

    @staticmethod
    async def get_user_from_db(*, username) -> Union[UserInfo, None]:
        try:
            user_info = await UserDbManager.get_user_from_db(username=username)
            if user_info:
                return UserInfo(**user_info)
            return
        except Exception as e:
            raise e

    @staticmethod
    async def post_acc_into_temp_db(add_user_data: AccountRegModel) -> Union[bool, None]:
        try:
            _user_add_state = await UserDbManager.post_acc_into_temp_db(item=add_user_data)
            if _user_add_state:
                id_for_link: Union[str, UUID, Record] = _user_add_state["temp_id"]
                id_for_link = str(id_for_link["t_id"])
                id_for_link_generated_JWTEncoded = create_token_for_email_verify(id_for_link)
                generated_link = generate_url_for_email_verify(id_=id_for_link_generated_JWTEncoded)
                send_email_verify_link.delay(_user_add_state["temp_email"], generated_link)
                return True
            return
        except Exception as e:
            raise e

    @staticmethod
    async def verify_registration_with_email(token_verify):
        """
        -1 EMPTY USER ID
        -2 WRONG VERIFY ID
        :param token_verify:
        :return:
        """
        try:
            temp_payload = await decode_token(token_verify)
            temp_id = temp_payload['sub']
            if not temp_id:
                return -1
            _verify_state = await UserDbManager.verify_registration_with_email(temp_id=temp_id)
            if not _verify_state:
                return -2
            _info = _verify_state["del_tmp_add_company"]
            _unique_id = _info["c_unique_id"]
            _c_email = _info["c_email"]
            return True
        except Exception as e:
            print(e)
            return
