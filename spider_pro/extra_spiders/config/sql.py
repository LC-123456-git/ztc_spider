# @Time : 2021/5/31 17:59 
# @Author : miaokela
# @File : sql.py 
# @Description: sql


COMPANY_NAMES = """SELECT QYMC FROM {db_name}.{table_name}"""
COMPANY_INFO_INSERT = """
                      INSERT INTO {db_name}.{table_name}
                      (QYMC,SSDQ,FDDBR,CLRQ,DJZT,ZCZB,SJZB,TYSHXYDM,GSZCH,ZZJGDM,NSRSBH,NSRZZ,QYLX,HY,YYQXS,YYQXM,RYGM,CBRY,YWM,CYM,DJJG,HZRQ,ZCDZ,JYFW,JCKQYDM,QYFL,HYDL,
                      QYSH,QYDZ,DHHM,KHYH,YHZH,origin,create_time,update_time)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      """

COMPANY_INFO_UPDATE = """
                      UPDATE {db_name}.{table_name} SET
                      QYMC=%s,SSDQ=%s,FDDBR=%s,CLRQ=%s,DJZT=%s,ZCZB=%s,SJZB=%s,TYSHXYDM=%s,GSZCH=%s,ZZJGDM=%s,NSRSBH=%s,NSRZZ=%s,QYLX=%s,
                      HY=%s,YYQXS=%s,YYQXM=%s,RYGM=%s,CBRY=%s,YWM=%s,CYM=%s,DJJG=%s,HZRQ=%s,ZCDZ=%s,JYFW=%s,JCKQYDM=%s,QYFL=%s,HYDL=%s,
                      QYSH=%s,QYDZ=%s,DHHM=%s,KHYH=%s,YHZH=%s,origin=%s,update_time=%s
                      WHERE QYMC=
                      """

COMPANY_FETCH_BY_NAME = """SELECT COUNT(QYMC) c FROM {db_name}.{table_name} WHERE QYMC='%s'"""

# 新增发票信息
ADD_INVOICES = """
               ALTER TABLE `test2_data_collection`.`QCC_qcc_crawler`
               ADD COLUMN `QYSH` VARCHAR(512) NULL DEFAULT NULL COMMENT '企业税号' AFTER `HYDL`,
               ADD COLUMN `QYDZ` VARCHAR(512) NULL DEFAULT NULL COMMENT '企业地址' AFTER `QYSH`,
               ADD COLUMN `DHHM` VARCHAR(512) NULL DEFAULT NULL COMMENT '电话号码' AFTER `QYDZ`,
               ADD COLUMN `KHYH` VARCHAR(512) NULL DEFAULT NULL COMMENT '开户银行' AFTER `DHHM`,
               ADD COLUMN `YHZH` VARCHAR(45) NULL DEFAULT NULL COMMENT '银行账户' AFTER `KHYH`;
               ADD COLUMN `origin` VARCHAR(45) NULL DEFAULT NULL COMMENT '网站地址' AFTER `origin`;
               """
