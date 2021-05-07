/*
 Navicat Premium Data Transfer

 Source Server         : ztx248-mysql
 Source Server Type    : MySQL
 Source Server Version : 50732
 Source Host           : 192.168.1.248:3306
 Source Schema         : test2_data_collection

 Target Server Type    : MySQL
 Target Server Version : 50732
 File Encoding         : 65001

 Date: 04/01/2021 17:15:29
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for area
-- ----------------------------
DROP TABLE IF EXISTS `area`;
CREATE TABLE `area` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `area` varchar(10) DEFAULT NULL COMMENT '地区',
  `address` varchar(30) DEFAULT NULL COMMENT '地址',
  `name` varchar(100) DEFAULT NULL COMMENT '名称',
  `url` varchar(200) NOT NULL COMMENT '网址',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=112 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of area
-- ----------------------------
BEGIN;
INSERT INTO `area` VALUES (0, '全国', '全国', '全国公共资源交易平台', 'http://www.ggzy.gov.cn/');
INSERT INTO `area` VALUES (1, '全国', '全国', '中国招标投标公共服务平台', 'http://www.cebpubservice.com/');
INSERT INTO `area` VALUES (2, '华北', '北京市', '北京市公共资源交易服务平台', 'http://ggzyfw.beijing.gov.cn');
INSERT INTO `area` VALUES (3, '华北', '天津市', '天津市公共资源交易网', 'http://ggzy.zwfwb.tj.gov.cn/');
INSERT INTO `area` VALUES (4, '华北', '河北省', '河北省政务服务管理办公室', 'http://ggzy.hebei.gov.cn/');
INSERT INTO `area` VALUES (5, '华北', '山西省', '山西省公共资源交易平台', 'http://prec.sxzwfw.gov.cn');
INSERT INTO `area` VALUES (6, '华北', '内蒙古', '内蒙古公共资源交易管理服务中心', 'http://ggzyjy.nmg.gov.cn');
INSERT INTO `area` VALUES (7, '东北', '辽宁省', '全国公共资源交易平台（辽宁省）', 'http://www.lnggzy.gov.cn/');
INSERT INTO `area` VALUES (8, '东北', '吉林省', '吉林省公共资源交易公共服务平台', 'http://www.jl.gov.cn/ggzy/');
INSERT INTO `area` VALUES (9, '东北', '吉林省', '吉林省公共资源交易中心', 'http://www.ggzyzx.jl.gov.cn/');
INSERT INTO `area` VALUES (10, '东北', '黑龙江省', '黑龙江省公共资源交易信息网', 'http://hljggzyjyw.gov.cn');
INSERT INTO `area` VALUES (11, '华东', '上海市', '上海市公共资源交易平台', 'http://www.shggzy.com');
INSERT INTO `area` VALUES (12, '华东', '上海市', '上海市建设工程交易服务中心', 'http://www.shcpe.cn/jyfw/xxfw/index.html');
INSERT INTO `area` VALUES (13, '华东', '江苏省', '江苏省公共资源交易网', 'http://jsggzy.jszwfw.gov.cn/');
INSERT INTO `area` VALUES (14, '华东', '浙江省', '浙江省公共资源交易服务平台', 'http://www.zjpubservice.com');
INSERT INTO `area` VALUES (15, '华东', '浙江省', '浙江省公共资源交易-交易信息', 'http://www.zmctc.com/zjgcjy/jyxx/');
INSERT INTO `area` VALUES (16, '华东', '安徽省', '安徽省公共资源交易监管网', 'http://ggzy.ah.gov.cn/');
INSERT INTO `area` VALUES (17, '华东', '福建省', '福建省公共资源交易电子公共服务平台', 'https://ggzyfw.fujian.gov.cn/');
INSERT INTO `area` VALUES (18, '华东', '福建省', '福建省公共资源交易网', 'http://www.fjggzyjy.cn/');
INSERT INTO `area` VALUES (19, '华东', '江西省', '江西公共资源交易网', 'https://www.jxsggzy.cn/web/');
INSERT INTO `area` VALUES (20, '华东', '江西省', '', 'http://ncztb.nc.gov.cn/nczbw/');
INSERT INTO `area` VALUES (21, '华东', '山东省', '山东省公共资源交易网', 'http://ggzyjy.shandong.gov.cn/');
INSERT INTO `area` VALUES (22, '华东', '山东省', '山东省公共资源交易中心', 'http://ggzyjyzx.shandong.gov.cn/');
INSERT INTO `area` VALUES (23, '华中', '河南省', '河南省公共资源交易公共服务平台', 'http://hnsggzyfwpt.hndrc.gov.cn/');
INSERT INTO `area` VALUES (24, '华中', '河南省', '河南省公共资源交易中心门户网', 'http://www.hnggzy.com/hnsggzy/');
INSERT INTO `area` VALUES (25, '华中', '河南省', '招投标信息_河南省水利厅', 'http://slt.henan.gov.cn/bmzl/jsgl/ztbxx/');
INSERT INTO `area` VALUES (26, '华中', '湖北省', '湖北省公共资源交易中心（湖北省政府采购中心）', 'http://jycg.hubei.gov.cn/');
INSERT INTO `area` VALUES (27, '华中', '湖北省', '湖北省公共资源电子交易服务系统', 'http://www.hbggzyfwpt.cn/');
INSERT INTO `area` VALUES (28, '华中', '湖南省', '湖南省公共资源交易中心', 'https://ggzy.hunan.gov.cn/');
INSERT INTO `area` VALUES (29, '华中', '湖南省', '湖南省公共资源交易服务平台', 'https://www.hnsggzy.com/');
INSERT INTO `area` VALUES (30, '华南', '广东省', '全国公共资源交易平台（广东省）', 'http://bs.gdggzy.org.cn/osh-web/');
INSERT INTO `area` VALUES (31, '华南', '广东省', '广州公共资源交易中心', 'http://www.gzggzy.cn/');
INSERT INTO `area` VALUES (32, '华南', '广东省', '安装信息网-建筑安装、工程项目、招标采购、产品供求、价格行情、企业库信息平台，建筑安装行业门户', 'http://www.zgazxxw.com/');
INSERT INTO `area` VALUES (33, '华南', '广西壮族自治区', '广西公共资源交易中心', 'http://gxggzy.gxzf.gov.cn/');
INSERT INTO `area` VALUES (34, '华南', '海南省', '全国公共资源交易平台（海南省）', 'http://zw.hainan.gov.cn/ggzy/');
INSERT INTO `area` VALUES (35, '华南', '海南省', '公共资源交易_海南省人民政府网', 'http://www.hainan.gov.cn/hainan/ggzy/list.shtml');
INSERT INTO `area` VALUES (36, '华南', '海南省', '海南公共资源交易中心', 'https://hng.zbytb.com/');
INSERT INTO `area` VALUES (37, '华南', '海南省', '海南省政府采购网', 'https://www.ccgp-hainan.gov.cn/zhuzhan/');
INSERT INTO `area` VALUES (38, '华南', '海南省', '海南产权交易网', 'http://www.hncq.cn/');
INSERT INTO `area` VALUES (39, '西南', '重庆市', '重庆市公共资源交易网_重庆市公共资源交易中心', 'https://www.cqggzy.com/');
INSERT INTO `area` VALUES (40, '西南', '四川省', '四川省公共资源交易信息网', 'http://ggzyjy.sc.gov.cn/');
INSERT INTO `area` VALUES (41, '西南', '贵州省', '贵州省公共资源交易云', 'http://ggzy.guizhou.gov.cn/');
INSERT INTO `area` VALUES (42, '西南', '云南省', '云南省公共资源交易电子服务系统', 'http://ggzy.yn.gov.cn/');
INSERT INTO `area` VALUES (43, '西南', '云南省', '云南省公共资源交易中心', 'https://www.ynggzy.com/');
INSERT INTO `area` VALUES (44, '西南', '西藏自治区', '西藏公共资源交易信息网', 'http://ggzy.xizang.gov.cn:9090/');
INSERT INTO `area` VALUES (45, '西北', '陕西省', '全国公共资源交易平台（陕西省）陕西省公共资源交易中心', 'http://www.sxggzyjy.cn/');
INSERT INTO `area` VALUES (46, '西北', '甘肃省', '甘肃省公共资源交易网', 'https://ggzyjy.gansu.gov.cn');
INSERT INTO `area` VALUES (47, '西北', '青海省', '青海省公共资源交易服务平台', 'https://www.qhdzzbfw.gov.cn/');
INSERT INTO `area` VALUES (48, '西北', '青海省', '青海省公共资源交易服务平台', 'http://www.qhggzyjy.gov.cn/');
INSERT INTO `area` VALUES (49, '西北', '宁夏回族自治区', '宁夏回族自治区公共资源交易网', 'http://www.nxggzyjy.org/');
INSERT INTO `area` VALUES (50, '西北', '新疆维吾尔自治区', '新疆公共资源交易网', 'http://zwfw.xinjiang.gov.cn/xinjiangggzy/');
INSERT INTO `area` VALUES (51, '西北', '兵团', '新疆生产建设兵团公共资源交易信息网', 'http://ggzy.xjbt.gov.cn/');
INSERT INTO `area` VALUES (52, '', '', '品茗-嗨招', 'https://www.hibidding.com/');
INSERT INTO `area` VALUES (53, '', '', '必联', 'https://www.ebnew.com/');
INSERT INTO `area` VALUES (54, '', '', 'E共享交易平台', 'http://ebid.okap.com/');
INSERT INTO `area` VALUES (55, '', '', '天工招采平台', 'http://zhaobiao.tgcw.net.cn/cms/index.htm');
INSERT INTO `area` VALUES (56, '', '', '建投商务网', 'https://www.jtsww.com/');
INSERT INTO `area` VALUES (57, '', '', '精彩纵横', 'http://jczh.jczh100.com/');
INSERT INTO `area` VALUES (58, '', '', '明信阳光', 'http://www.51ygcg.com/');
INSERT INTO `area` VALUES (59, '', '', '鑫智链招标', 'http://www.njxic.cn/');
INSERT INTO `area` VALUES (60, '', '', '安阳公共资源交易', 'http://www.ayggzy.cn/');
INSERT INTO `area` VALUES (61, '', '', '优质采电子交易', 'https://www.youzhicai.com/MScene/Mtender');
INSERT INTO `area` VALUES (62, '', '', '新点平台', 'https://www.etrading.cn/');
INSERT INTO `area` VALUES (63, '', '', '广咨E招', 'https://www.gzebid.cn/');
INSERT INTO `area` VALUES (64, '', '', '国信创新电子交易平台', 'http://www.e-bidding.org/');
INSERT INTO `area` VALUES (65, '', '', '国e平台', 'https://www.ebidding.com/portal/html/index.html#page=main:announcement');
INSERT INTO `area` VALUES (66, '', '', '阳光一路', 'http://www.ahggzyjt.com/');
INSERT INTO `area` VALUES (67, '', '', '阳光易招', 'http://www.sunbidding.com/');
INSERT INTO `area` VALUES (68, '', '', '齐鲁招采网', 'http://www.qlebid.com/');
INSERT INTO `area` VALUES (69, '', '', '广东电子招标平台', 'https://www.bidnews.cn/gdbid/');
INSERT INTO `area` VALUES (70, '', '', '易招标-招采进宝（全国）', 'http://china.zcjb.com.cn/cms/index.htm');
INSERT INTO `area` VALUES (71, '', '', '易招标-招采进宝（河北）', 'http://hb.zcjb.com.cn/cms/index.htm');
INSERT INTO `area` VALUES (72, '', '', '易招标-招采进宝（山西）', 'http://sxty.ebidding.net.cn/cms/index.htm');
INSERT INTO `area` VALUES (73, '', '', '易招标-招采进宝（山东）', 'http://sd.zcjb.com.cn/cms/index.htm');
INSERT INTO `area` VALUES (74, '', '', '易招标-招采进宝（安徽）', 'http://ah.zcjb.com.cn/cms/index.htm');
INSERT INTO `area` VALUES (75, '', '', '易招标-招采进宝（新疆）', 'http://xj.zcjb.com.cn/cms/index.htm');
INSERT INTO `area` VALUES (76, '', '', 'E招冀成', 'http://www.hebeibidding.com/');
INSERT INTO `area` VALUES (77, '', '', '招必得', 'https://www.zhaobide.com/');
INSERT INTO `area` VALUES (78, '', '', '住宅修缮工程招投标', 'http://xsjypt.fgj.sh.gov.cn/');
INSERT INTO `area` VALUES (79, '', '', '信e采', 'https://www.ahbidding.com/');
INSERT INTO `area` VALUES (80, '', '', '兖矿招采平台', 'http://www.ykjtzb.com/');
INSERT INTO `area` VALUES (81, '', '', '—联易招交易平台', 'http://www.ebid.sh.cn/');
INSERT INTO `area` VALUES (82, '', '', '比德电子采购平台', 'http://www.bdebid.com/');
INSERT INTO `area` VALUES (83, '', '', '旺采网', 'https://sx.5ibid.net/');
INSERT INTO `area` VALUES (84, '', '', '中国铁路上海局集团有限公司物资采购商务平台', 'http://222.44.91.31/index.jsp');
INSERT INTO `area` VALUES (85, '', '', '安装信息网', 'http://m.zgazxxw.com/');
INSERT INTO `area` VALUES (86, '', '', '中国联通招标网', 'http://m.zgazxxw.com/da-010001l772-0.html');
INSERT INTO `area` VALUES (87, '', '', '中国电子招标网', 'https://www.ztb365.cn/');
INSERT INTO `area` VALUES (88, '', '', '中国电子招标网-铁路', 'https://www.ztb365.cn/tlzb/');
INSERT INTO `area` VALUES (89, '', '', '铁路招标', 'http://www.tieluzb.com/');
INSERT INTO `area` VALUES (90, '', '', '上海地铁', 'http://www.shmetro.com/');
INSERT INTO `area` VALUES (91, '', '', '广州地铁', 'http://bid.gzmtr.com/');
INSERT INTO `area` VALUES (92, '', '', '广州地铁招标投标网站', 'http://www.gzmtr.com/bid/bizzbgg/');
INSERT INTO `area` VALUES (93, '', '', '杭州地铁', 'http://www.hzmetro.com/tender_0.aspx#midc');
INSERT INTO `area` VALUES (94, '', '', '深圳地铁', 'https://www.szmc.net/zhaobiaozhaoshang/');
INSERT INTO `area` VALUES (95, '', '', '北京地铁', 'http://www.bjmetro.com.cn/ecp/');
INSERT INTO `area` VALUES (96, '', '', '成都地铁', 'https://ep.cdmetro.cn:1443/suneps/login.jsp;jsessionid=Vv7-UGSjKF18XSk5V9wUcYEjXwLwhmKYRggEM4JR2MwVh4W35wTj!2090317832');
INSERT INTO `area` VALUES (97, '', '', '西安地铁', 'https://www.xianrail.com/#/biddingProcurement');
INSERT INTO `area` VALUES (98, '', '', '武汉地铁', 'http://www.whrtyycg.com/#!web/homePage.jsx');
INSERT INTO `area` VALUES (99, '', '', '沈阳地铁', 'http://www.symtc.com/contentlist.php?301');
INSERT INTO `area` VALUES (100, '', '', '青岛地铁', 'http://www.qd-metro.com/tender/list.php?sid=49');
INSERT INTO `area` VALUES (101, '', '', '济南地铁', 'http://www.jngdjt.cn/html/zbtb/');
INSERT INTO `area` VALUES (102, '', '', '苏州轨道交通', 'http://www.sz-mtr.com/tender/notice/');
INSERT INTO `area` VALUES (103, '', '', '合肥地铁', 'http://www.hfgdjt.com/category/notice/pur_notice/');
INSERT INTO `area` VALUES (104, '', '', '郑州地铁', 'https://www.zzmetro.cn/page/id/37.html');
INSERT INTO `area` VALUES (105, '', '', '石家庄轨交', 'http://www.sjzmetro.cn/cyportal2.3/template/site00_Tender_Notice@gdb.jsp?a1b2dd=7xaac');
INSERT INTO `area` VALUES (106, '', '', '绍兴地铁', 'http://www.sxsmtr.cn/index.php?m=content&c=index&a=lists&catid=16');
INSERT INTO `area` VALUES (107, '', '', '宁波轨交', 'http://www.nbmetro.com/tender_report.php');
INSERT INTO `area` VALUES (108, '', '', '温州轨交', 'https://www.wzmtr.com/Col/Col109/Index.aspx');
INSERT INTO `area` VALUES (109, '', '', '福州地铁', 'http://www.fzmtr.com/html/fzdt/pagenoticelist/1596446278.html');
INSERT INTO `area` VALUES (110, '', '', '厦门地铁', 'https://www.xmgdjt.com.cn/Modules/ControlHtml/Bidding.aspx');
INSERT INTO `area` VALUES (111, '', '', '长沙轨交', 'http://www.hncsmtr.com/zbtb/index.html');
COMMIT;

-- ----------------------------
-- Table structure for notices
-- ----------------------------
DROP TABLE IF EXISTS `notices`;
CREATE TABLE `notices` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `origin` varchar(500) NOT NULL COMMENT '原始链接',
  `title_name` varchar(2000) NOT NULL COMMENT '标题',
  `pub_time` datetime NOT NULL DEFAULT '1970-01-01 00:00:00' COMMENT '发布时间',
  `info_source` varchar(50) NOT NULL COMMENT '来源（省级）',
  `content` longtext NOT NULL COMMENT '文本',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_have_file` int(4) NOT NULL DEFAULT '0' COMMENT '是否包含文件',
  `files_path` text NOT NULL COMMENT '文件路径，按英文逗号,分割',
  `notice_type` int(4) NOT NULL COMMENT '0#招标公告 1#招标预告 2#招标变更 3#招标异常 4#中标预告 5#中标公告 6#资格预审结果公告 7#其他公告',
  `area_id` int(7) NOT NULL COMMENT '地区ID',
  PRIMARY KEY (`id`),
  KEY `area_id` (`area_id`) USING HASH
) ENGINE=InnoDB AUTO_INCREMENT=2935 DEFAULT CHARSET=utf8mb4 COMMENT='其他公告';

SET FOREIGN_KEY_CHECKS = 1;
