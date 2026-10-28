-- COM-STU-010: five categories / 70 codes, no invented class/student data.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
DECLARE @lock int;
EXEC @lock=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public';
IF @lock<0 BEGIN ROLLBACK; THROW 51001,N'保存用ロック取得失敗',1; END;
DECLARE @now datetimeoffset(7)=TODATETIMEOFFSET(SYSUTCDATETIME(),'+00:00'),@actor nvarchar(128)=ORIGINAL_LOGIN();
DECLARE @categories TABLE(category_id varchar(24),category_name nvarchar(24),code_length smallint,allow_add bit);
INSERT @categories VALUES ('GENDER',N'性別',1,0),
('ENROLLMENT_STATUS',N'在籍区分',2,0),
('PREFECTURE',N'都道府県',2,0),
('RELATIONSHIP',N'緊急連絡先続柄',2,1),
('GRADE',N'学年',2,1);
DECLARE @codes TABLE(category_id varchar(24),code_value varchar(10),code_name nvarchar(24),display_order int,is_protected bit);
INSERT @codes VALUES ('GENDER','0',N'未回答',0,1),
('GENDER','1',N'男性',10,0),
('GENDER','2',N'女性',20,0),
('GENDER','9',N'その他',90,0),
('ENROLLMENT_STATUS','01',N'在学',10,1),
('ENROLLMENT_STATUS','02',N'休学',20,1),
('ENROLLMENT_STATUS','03',N'卒業',30,1),
('ENROLLMENT_STATUS','04',N'退学',40,1),
('PREFECTURE','01',N'北海道',10,1),
('PREFECTURE','02',N'青森県',20,1),
('PREFECTURE','03',N'岩手県',30,1),
('PREFECTURE','04',N'宮城県',40,1),
('PREFECTURE','05',N'秋田県',50,1),
('PREFECTURE','06',N'山形県',60,1),
('PREFECTURE','07',N'福島県',70,1),
('PREFECTURE','08',N'茨城県',80,1),
('PREFECTURE','09',N'栃木県',90,1),
('PREFECTURE','10',N'群馬県',100,1),
('PREFECTURE','11',N'埼玉県',110,1),
('PREFECTURE','12',N'千葉県',120,1),
('PREFECTURE','13',N'東京都',130,1),
('PREFECTURE','14',N'神奈川県',140,1),
('PREFECTURE','15',N'新潟県',150,1),
('PREFECTURE','16',N'富山県',160,1),
('PREFECTURE','17',N'石川県',170,1),
('PREFECTURE','18',N'福井県',180,1),
('PREFECTURE','19',N'山梨県',190,1),
('PREFECTURE','20',N'長野県',200,1),
('PREFECTURE','21',N'岐阜県',210,1),
('PREFECTURE','22',N'静岡県',220,1),
('PREFECTURE','23',N'愛知県',230,1),
('PREFECTURE','24',N'三重県',240,1),
('PREFECTURE','25',N'滋賀県',250,1),
('PREFECTURE','26',N'京都府',260,1),
('PREFECTURE','27',N'大阪府',270,1),
('PREFECTURE','28',N'兵庫県',280,1),
('PREFECTURE','29',N'奈良県',290,1),
('PREFECTURE','30',N'和歌山県',300,1),
('PREFECTURE','31',N'鳥取県',310,1),
('PREFECTURE','32',N'島根県',320,1),
('PREFECTURE','33',N'岡山県',330,1),
('PREFECTURE','34',N'広島県',340,1),
('PREFECTURE','35',N'山口県',350,1),
('PREFECTURE','36',N'徳島県',360,1),
('PREFECTURE','37',N'香川県',370,1),
('PREFECTURE','38',N'愛媛県',380,1),
('PREFECTURE','39',N'高知県',390,1),
('PREFECTURE','40',N'福岡県',400,1),
('PREFECTURE','41',N'佐賀県',410,1),
('PREFECTURE','42',N'長崎県',420,1),
('PREFECTURE','43',N'熊本県',430,1),
('PREFECTURE','44',N'大分県',440,1),
('PREFECTURE','45',N'宮崎県',450,1),
('PREFECTURE','46',N'鹿児島県',460,1),
('PREFECTURE','47',N'沖縄県',470,1),
('RELATIONSHIP','01',N'父',10,0),
('RELATIONSHIP','02',N'母',20,0),
('RELATIONSHIP','03',N'祖父',30,0),
('RELATIONSHIP','04',N'祖母',40,0),
('RELATIONSHIP','05',N'兄弟姉妹',50,0),
('RELATIONSHIP','06',N'配偶者',60,0),
('RELATIONSHIP','07',N'後見人',70,0),
('RELATIONSHIP','99',N'その他',990,0),
('GRADE','00',N'学年なし',0,1),
('GRADE','01',N'1年',10,0),
('GRADE','02',N'2年',20,0),
('GRADE','03',N'3年',30,0),
('GRADE','04',N'4年',40,0),
('GRADE','05',N'5年',50,0),
('GRADE','06',N'6年',60,0);
IF EXISTS(SELECT 1 FROM @categories i JOIN dbo.m_code_category c ON c.category_id=i.category_id WHERE c.category_name<>i.category_name OR c.code_length<>i.code_length OR c.allow_add<>i.allow_add OR c.is_active<>1)
 OR EXISTS(SELECT 1 FROM @codes i JOIN dbo.m_code c ON c.category_id=i.category_id AND c.code_value=i.code_value WHERE c.code_name<>i.code_name OR c.display_order<>i.display_order OR c.is_protected<>i.is_protected OR c.is_active<>1 OR c.valid_from<>'19000101' OR c.valid_to IS NOT NULL)
 BEGIN ROLLBACK; THROW 51002,N'初期コードに差分があります。既存値を上書きせず確認してください。',1; END;
INSERT dbo.m_code_category(category_id,category_name,code_length,allow_add,is_active,remarks,created_at,created_by,updated_at,updated_by,row_version)
 SELECT i.category_id,i.category_name,i.code_length,i.allow_add,1,NULL,@now,@actor,@now,@actor,1 FROM @categories i WHERE NOT EXISTS(SELECT 1 FROM dbo.m_code_category c WHERE c.category_id=i.category_id);
INSERT dbo.m_code(category_id,code_value,code_name,display_order,is_active,valid_from,valid_to,is_protected,remarks,created_at,created_by,updated_at,updated_by,row_version)
 SELECT i.category_id,i.code_value,i.code_name,i.display_order,1,'19000101',NULL,i.is_protected,NULL,@now,@actor,@now,@actor,1 FROM @codes i WHERE NOT EXISTS(SELECT 1 FROM dbo.m_code c WHERE c.category_id=i.category_id AND c.code_value=i.code_value);
COMMIT;
GO
