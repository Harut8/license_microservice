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
        _is_not_license_expire = await fetch_row_transaction(
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
        return _is_not_license_expire

    @staticmethod
    async def _add_new_license(device_code, product_id, license_key, unique_code):
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
                    _ip = res["ip_of_client"][product_id - 1]
                    if not _port and not _ip:
                        return
                    await db.execute(
                        """
                        UPDATE licenses SET own_ip = $1, own_port = $2 where license_key = $3;
                        """,
                        _ip,
                        _port,
                        license_key)
                    return {'port': int(_port),
                            'ip': _ip,
                            'license_key': license_key}

    @staticmethod
    async def _check_exists_device_license(
            unique_code,
            device_code,
            product_id
    ):
        return await fetch_row_transaction(
            """
            SELECT license_key AS device_license_key 
            FROM licenses l
            JOIN device_info di on l.license_key = di.device_license_key 
            WHERE unique_id_cp = $1 
            AND product_id_fk = $3
            AND device_code = $2 ;""",
            unique_code,
            device_code,
            product_id
        )

    @staticmethod
    async def _get_port_ip(
            _license_key,
            unique_code
    ):
        _port_ip_key = await fetch_row_transaction(
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

    @staticmethod
    async def web_manager_license(
            _is_not_license_expire,
            unique_code,
            device_code,
            product_id
    ):
        #  can add license
        #  cant add license
        _web_license_key = await LicenseDbManager._check_exists_device_license(unique_code, device_code, product_id)

        if _web_license_key:
            #  return existing license if use same device
            _license_key = _web_license_key["device_license_key"]
            _port_ip_key = await fetch_row_transaction(
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

        if _is_not_license_expire:
            #  add license if new device
            _license_key = token_hex(32)
            _web_license = await LicenseDbManager._add_new_license(
                device_code,
                product_id,
                _license_key,
                unique_code
            )
            return _web_license

        elif not _is_not_license_expire:
            #  get random license from existing licenses
            _web_random_license_key = await fetch_row_transaction(
                """
                SELECT license_key AS device_license_key 
                FROM licenses l
                WHERE unique_id_cp = $1 
                AND product_id_fk = 3
                ORDER BY RANDOM()
                LIMIT 1;""",
                unique_code
            )
            _license_key = _web_random_license_key["device_license_key"]
            async with DbConnection() as connection:
                async with connection.acquire() as db:
                    async with db.transaction():
                        await db.execute(
                            """
                            update device_info
                            set device_code=$2 where
                            device_license_key = $1;""",
                            _license_key,
                            device_code
                        )
                        await db.execute(
                            """
                            update uniqunes_product set device_code = $1
                            where u_license_key = $2;
                            """,
                            device_code,
                            _license_key
                        )
                        _port_ip = await LicenseDbManager._get_port_ip(_license_key, unique_code)
                        return _port_ip

        else:
            return

    @staticmethod
    async def other_platform_license(
            _is_not_license_expire,
            unique_code,
            device_code,
            product_id
    ):
        _other_license_key = await LicenseDbManager._check_exists_device_license(
            unique_code,
            device_code,
            product_id
        )
        if _other_license_key:
            #  device exists
            _license_key = _other_license_key["device_license_key"]
            _port_ip = LicenseDbManager._get_port_ip(_license_key,unique_code)
            _other_license = await LicenseDbManager._add_new_license(
                device_code,
                product_id,
                _license_key,
                unique_code
            )
            return _other_license
        else:
            return

    @staticmethod
    async def _check_license_date(
            license_key,
            device_code,
            product_id
    ):
        async with DbConnection() as connection:
            async with connection.acquire() as db:
                async with db.transaction():
                    _license_date_is_ok = await db.fetchrow(
                        """
                        with cte as (
                        SELECT ct.end_license::date > current_date as date_state 
                        FROM client_tarif ct 
                        JOIN company c ON ct.c_t_id = c.c_id 
                        JOIN licenses l ON c.c_unique_id  = l.unique_id_cp 
                        JOIN device_info di ON l.license_key = di.device_license_key 
                        WHERE l.license_key = $1
                        AND di.device_code = $2 and product_id_fk = $3)
                        select * from cte where exists (select * from cte) limit 1;
                        """,
                        license_key,
                        device_code,
                        product_id)
                    if _license_date_is_ok:
                        return _license_date_is_ok["date_state"]
                    return

    @staticmethod
    async def check_license(license_key,
                            device_code,
                            product_id):
        """
        :param license_key:
        :param device_code:
        :param product_id:
        :return:
        """
        _license_date = await LicenseDbManager._check_license_date(license_key,device_code,product_id)
        print(_license_date)
        if _license_date:
            _unique_code = await fetch_row_transaction(
                """select unique_id_cp from licenses where license_key = $1""",
                license_key)
            _unique_code = _unique_code["unique_id_cp"]
            _port_ip = await LicenseDbManager._get_port_ip(license_key, _unique_code)
            return {'state': True, 'ip': _port_ip['ip'], 'port': _port_ip['port']}
        elif _license_date is False:
            # need to renewal
            return {'state': False}
        else:
            # need to buy
            return {'state': 0}

