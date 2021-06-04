# @Time : 2021/5/31 17:59 
# @Author : miaokela
# @File : sql.py 
# @Description: sql


COMPANY_NAMES = """SELECT company_name FROM {db_name}.{table_name}"""
COMPANY_INFO_INSERT = """
                      INSERT INTO {db_name}.{table_name}
                      (company_name,location,legal_representative,date_of_establishment,operating_status,registered_capital,paid_in_capital,
                      unified_social_credit_code,business_registration_number,organization_code,taxpayer_identification_number,taxpayer_qualification,
                      type_of_enterprise,industry,operating_period_std,operating_period_edt,staff_size,number_of_participants,english_name,
                      former_name,registration_authority,approved_date,registered_address,business_scope,import_and_export_enterprise_code,
                      category,industry_category,credit_code,address,phone_number,bank,bank_account,origin,create_time,update_time)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      """

COMPANY_INFO_UPDATE = """
                      UPDATE {db_name}.{table_name} SET
                      company_name=%s,location=%s,legal_representative=%s,date_of_establishment=%s,operating_status=%s,registered_capital=%s,paid_in_capital=%s,
                      unified_social_credit_code=%s,business_registration_number=%s,organization_code=%s,taxpayer_identification_number=%s,taxpayer_qualification=%s,
                      type_of_enterprise=%s,industry=%s,operating_period_std=%s,operating_period_edt=%s,staff_size=%s,number_of_participants=%s,english_name=%s,
                      former_name=%s,registration_authority=%s,approved_date=%s,registered_address=%s,business_scope=%s,import_and_export_enterprise_code=%s,
                      category=%s,industry_category=%s,credit_code=%s,address=%s,phone_number=%s,bank=%s,bank_account=%s,origin=%s,update_time=%s
                      WHERE company_name=
                      """

COMPANY_FETCH_BY_NAME = """SELECT COUNT(QYMC) c FROM {db_name}.{table_name} WHERE QYMC='%s'"""

# 新增发票信息
ADD_INVOICES = """
               ALTER TABLE `test2_data_collection`.`QCC_qcc_crawler`
               ADD COLUMN `credit_code` VARCHAR(512) NULL DEFAULT NULL COMMENT '企业税号' AFTER `HYDL`,
               ADD COLUMN `address` VARCHAR(512) NULL DEFAULT NULL COMMENT '企业地址' AFTER `QYSH`,
               ADD COLUMN `phone_number` VARCHAR(512) NULL DEFAULT NULL COMMENT '电话号码' AFTER `QYDZ`,
               ADD COLUMN `bank` VARCHAR(512) NULL DEFAULT NULL COMMENT '开户银行' AFTER `DHHM`,
               ADD COLUMN `bank_account` VARCHAR(45) NULL DEFAULT NULL COMMENT '银行账户' AFTER `KHYH`;
               ADD COLUMN `origin` VARCHAR(45) NULL DEFAULT NULL COMMENT '网站地址' AFTER `origin`;
               """
