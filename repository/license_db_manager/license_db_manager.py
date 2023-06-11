import uuid
from secrets import token_hex
from typing import Union
from repository.core.core import DbConnection, fetch_row_transaction, insert_row_transaction, execute_delete_query
from dataclasses import dataclass
from repository.license_db_manager.license_db_interface import LicenseDbInterface
from asyncpg import Record

product_id_table = {
    1: 'cass_stantion_count',
    2: 'mobile_cass_count',
    3: 'web_manager_count',
    4: 'mobile_manager_count'
}


@dataclass
class LicenseDbManager(LicenseDbInterface):

    @staticmethod
    async def check_license_state(
            unique_code,
            product_id):
        """DIVIDE TO CHECK_LICENSE_STATE, WEB_LICENSE AND OTHER"""
        _is_license_expire = await fetch_row_transaction(
            f"""select
        case
        when(
              sum({product_id_table[product_id]}) -
             (select count(product_id_fk) from licenses l where product_id_fk = $2 and unique_id_cp = $1 )) > 0
        then
        true
        else false
        end
        as state_of_license
        from
        saved_order_and_tarif soat
        where
        company_id = (select c_id from company c where c_unique_id = $1) and order_state = true;""",
            unique_code,
            product_id
        )
        return _is_license_expire

    @staticmethod
    async def add_new_license(device_code, product_id, license_key, unique_code):
        async with DbConnection() as connection:
            async with connection.acquire() as db:
                async with db.transaction():
                    await db.execute(
                        """
                        insert into uniqunes_product(device_code, product_id, u_license_key)
                        VALUES($1, $2, $3);
                        """,
                        device_code,
                        product_id,
                        license_key
                    )

                    await db.execute(
                        """
                        insert into licenses(license_key, product_id_fk, unique_id_cp)
                        VALUES($1, $2, $3);""",
                        license_key,
                        product_id,
                        unique_code
                    )
                    await db.execute(
                        """
                        INSERT INTO device_info(device_code, device_license_key)
                        VALUES($1, $2);
                        """,
                        device_code,
                        license_key
                    )
                    res = await db.fetchrow("""
                    INSERT INTO device_port(port,unique_id_cp,ip_of_client )
                    VALUES(( select coalesce( max(port)+1,4000) from device_port), $1,
                    (select ip_of_client from client_ip where
                    ip_id = (select max(ip_id) from client_ip)))
                    on conflict(unique_id_cp) do
                    UPDATE SET unique_id_cp = excluded.unique_id_cp where
                    device_port.unique_id_cp = $1
                    returning port, ip_of_client;
                    """, unique_code)

                    _port = res["port"]
                    _ip = res["ip_of_client"][product_id-1]
                    if _port and _ip:
                        await db.execute(
                            """
                            UPDATE licenses SET own_ip = $1, own_port = $2 where license_key = $3;
                            """,
                            _ip,
                            _port,
                            license_key)
                    else:
                        return {'port': int(_port),
                                'ip': _ip,
                                'license_key': license_key}

    @staticmethod
    async def web_manager_license(_is_license_expire, unique_code, device_code):
        if not _is_license_expire:
            #  check are there any license for web
            _web_random_license_key = await fetch_row_transaction(
                """
                SELECT license_key AS device_license_key 
                FROM licenses 
                WHERE unique_id_cp = $1 
                AND product_id_fk = 3 
                ORDER BY RANDOM() 
                LIMIT 1;""",
                unique_code
            )
            if not _web_random_license_key:
                _license_key = token_hex(32)
                #  add license
                ...
            else:
                # update existing license code for web
                _license_key = _web_random_license_key["license_key"]
                async with DbConnection() as connection:
                    async with connection.acquire() as db:
                        async with db.transaction():
                            await db.execute(
                                """
                                update device_info
                                set device_code=%(device_code)s where
                                device_license_key = $1;""",
                                _license_key
                            )
                            await db.execute(
                                """
                                update uniqunes_product set device_code = $1
                                where u_license_key = $2;
                                """,
                                device_code,
                                _license_key
                            )
                            _port_ip_key = await db.fetchrow(
                                """
                                select own_port::int as port, own_ip from device_port dp,licenses
                                where license_key = $1 and dp.unique_id_cp = $2
                                """,
                                _license_key,
                                unique_code
                            )
                            return {
                                "port": _port_ip_key["port"],
                                "ip": _port_ip_key["own_ip"],
                                "license_key": _license_key}

        else:
            return

    @staticmethod
    async def check_license(license_key,
                            device_code,
                            product_id):
        ...
