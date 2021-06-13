# @Time : 2021/5/31 17:59 
# @Author : miaokela
# @File : sql.py 
# @Description: sql


COMPANY_NAMES = """SELECT company_name FROM {db_name}.{table_name}"""
COMPANY_INFO_INSERT = """INSERT INTO {db_name}.{table_name}
                      (company_name,location,legal_representative,date_of_establishment,operating_status,registered_capital,paid_in_capital,
                      unified_social_credit_code,business_registration_number,organization_code,taxpayer_identification_number,taxpayer_qualification,
                      type_of_enterprise,industry,operating_period_std,operating_period_edt,staff_size,number_of_participants,english_name,
                      former_name,registration_authority,approved_date,registered_address,business_scope,import_and_export_enterprise_code,
                      category,industry_category,credit_code,address,phone_number,bank,bank_account,origin,create_time,update_time)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      """

COMPANY_INFO_UPDATE = """UPDATE {db_name}.{table_name} SET
                      company_name=%s,location=%s,legal_representative=%s,date_of_establishment=%s,operating_status=%s,registered_capital=%s,paid_in_capital=%s,
                      unified_social_credit_code=%s,business_registration_number=%s,organization_code=%s,taxpayer_identification_number=%s,taxpayer_qualification=%s,
                      type_of_enterprise=%s,industry=%s,operating_period_std=%s,operating_period_edt=%s,staff_size=%s,number_of_participants=%s,english_name=%s,
                      former_name=%s,registration_authority=%s,approved_date=%s,registered_address=%s,business_scope=%s,import_and_export_enterprise_code=%s,
                      category=%s,industry_category=%s,credit_code=%s,address=%s,phone_number=%s,bank=%s,bank_account=%s,origin=%s,update_time=%s
                      WHERE company_name=
                      """

COMPANY_FETCH_BY_NAME = """SELECT COUNT(company_name) c FROM {db_name}.{table_name} WHERE company_name='%s'"""

COMPANY_NAMES_WITHOUT_ORIGIN = """SELECT company_name FROM {db_name}.{table_name} WHERE origin IS NULL"""            
COMPANY_NAMES_FROM_AGENT = """SELECT agency as company_name FROM {db_name}.{table_name}"""

# 检查代理机构信息是否补全  == 29350表示全部补全
AGENCY_IF_COMPLETE = """SELECT COUNT(qg.society_code) FROM data_collection.quanguo qg
                     WHERE EXISTS (
                         SELECT qcc.id FROM data_collection.QCC_qcc_crawler qcc
                         WHERE qcc.unified_social_credit_code=qg.society_code
                     )
                     """
                     
# 企业信息与代理机构连表查询
JOIN_FECTCH = """
              SELECT qcc.id, qcc.company_name, qg.liaison FROM data_collection.QCC_qcc_crawler qcc
              LEFT JOIN data_collection.quanguo qg 
              ON qcc.unified_social_credit_code=qg.society_code
              """

AGENCY_NOT_IN_QCC = """select qg.agency company_name from data_collection.quanguo qg
                    where qg.society_code not in (
                        select qcc.unified_social_credit_code from data_collection.QCC_qcc_crawler qcc
                    ) and qg.society_code != ''
                    """
