-- Synthetic dataset ACCESS-REBUILDER-TRAINING-V1; basis 2026-10-27, class validity through 2027-03-31.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
DECLARE @seed nvarchar(128)=(SELECT CONVERT(nvarchar(128),value) FROM sys.extended_properties WHERE class=0 AND name=N'AccessRebuilderSeed');
IF @seed IS NOT NULL AND @seed<>N'ACCESS-REBUILDER-TRAINING-V1' THROW 51010,'Different dataset owner; no changes.',1;
IF @seed IS NULL AND ((SELECT COUNT_BIG(*) FROM dbo.[m_code_category])+(SELECT COUNT_BIG(*) FROM dbo.[m_code])+(SELECT COUNT_BIG(*) FROM dbo.[m_class])+(SELECT COUNT_BIG(*) FROM dbo.[m_student])+(SELECT COUNT_BIG(*) FROM dbo.[t_app_role])+(SELECT COUNT_BIG(*) FROM dbo.[t_write_guard]))<>0 THROW 51011,'Nonempty database without dataset marker; no changes.',1;

IF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES (N'GENDER',N'性別',1,0,1,NULL),(N'ENROLLMENT_STATUS',N'在籍区分',2,0,1,NULL),(N'PREFECTURE',N'都道府県',2,0,1,NULL),(N'RELATIONSHIP',N'緊急連絡先続柄',2,1,1,NULL),(N'GRADE',N'学年',2,1,1,NULL)) AS expected([category_id],[category_name],[code_length],[allow_add],[is_active],[remarks]) EXCEPT SELECT [category_id],[category_name],[code_length],[allow_add],[is_active],[remarks] FROM dbo.[m_code_category]) THROW 51012,'Seeded business values changed; no changes.',1;
IF @seed IS NULL BEGIN
INSERT dbo.[m_code_category] ([category_id],[category_name],[code_length],[allow_add],[is_active],[remarks],[created_at],[created_by],[updated_at],[updated_by],[row_version]) VALUES
(N'GENDER',N'性別',1,0,1,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'ENROLLMENT_STATUS',N'在籍区分',2,0,1,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'都道府県',2,0,1,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'緊急連絡先続柄',2,1,1,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'学年',2,1,1,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1);
END;

IF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES (N'GENDER',N'0',N'未回答',0,1,1,N'1900-01-01',NULL,NULL),(N'GENDER',N'1',N'男性',10,0,1,N'1900-01-01',NULL,NULL),(N'GENDER',N'2',N'女性',20,0,1,N'1900-01-01',NULL,NULL),(N'GENDER',N'9',N'その他',90,0,1,N'1900-01-01',NULL,NULL),(N'ENROLLMENT_STATUS',N'01',N'在学',10,1,1,N'1900-01-01',NULL,NULL),(N'ENROLLMENT_STATUS',N'02',N'休学',20,1,1,N'1900-01-01',NULL,NULL),(N'ENROLLMENT_STATUS',N'03',N'卒業',30,1,1,N'1900-01-01',NULL,NULL),(N'ENROLLMENT_STATUS',N'04',N'退学',40,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'01',N'北海道',10,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'02',N'青森県',20,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'03',N'岩手県',30,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'04',N'宮城県',40,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'05',N'秋田県',50,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'06',N'山形県',60,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'07',N'福島県',70,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'08',N'茨城県',80,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'09',N'栃木県',90,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'10',N'群馬県',100,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'11',N'埼玉県',110,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'12',N'千葉県',120,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'13',N'東京都',130,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'14',N'神奈川県',140,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'15',N'新潟県',150,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'16',N'富山県',160,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'17',N'石川県',170,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'18',N'福井県',180,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'19',N'山梨県',190,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'20',N'長野県',200,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'21',N'岐阜県',210,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'22',N'静岡県',220,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'23',N'愛知県',230,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'24',N'三重県',240,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'25',N'滋賀県',250,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'26',N'京都府',260,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'27',N'大阪府',270,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'28',N'兵庫県',280,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'29',N'奈良県',290,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'30',N'和歌山県',300,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'31',N'鳥取県',310,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'32',N'島根県',320,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'33',N'岡山県',330,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'34',N'広島県',340,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'35',N'山口県',350,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'36',N'徳島県',360,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'37',N'香川県',370,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'38',N'愛媛県',380,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'39',N'高知県',390,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'40',N'福岡県',400,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'41',N'佐賀県',410,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'42',N'長崎県',420,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'43',N'熊本県',430,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'44',N'大分県',440,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'45',N'宮崎県',450,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'46',N'鹿児島県',460,1,1,N'1900-01-01',NULL,NULL),(N'PREFECTURE',N'47',N'沖縄県',470,1,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'01',N'父',10,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'02',N'母',20,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'03',N'祖父',30,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'04',N'祖母',40,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'05',N'兄弟姉妹',50,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'06',N'配偶者',60,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'07',N'後見人',70,0,1,N'1900-01-01',NULL,NULL),(N'RELATIONSHIP',N'99',N'その他',990,0,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'00',N'学年なし',0,1,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'01',N'1年',10,0,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'02',N'2年',20,0,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'03',N'3年',30,0,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'04',N'4年',40,0,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'05',N'5年',50,0,1,N'1900-01-01',NULL,NULL),(N'GRADE',N'06',N'6年',60,0,1,N'1900-01-01',NULL,NULL)) AS expected([category_id],[code_value],[code_name],[display_order],[is_protected],[is_active],[valid_from],[valid_to],[remarks]) EXCEPT SELECT [category_id],[code_value],[code_name],[display_order],[is_protected],[is_active],[valid_from],[valid_to],[remarks] FROM dbo.[m_code]) THROW 51012,'Seeded business values changed; no changes.',1;
IF @seed IS NULL BEGIN
INSERT dbo.[m_code] ([category_id],[code_value],[code_name],[display_order],[is_protected],[is_active],[valid_from],[valid_to],[remarks],[created_at],[created_by],[updated_at],[updated_by],[row_version]) VALUES
(N'GENDER',N'0',N'未回答',0,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GENDER',N'1',N'男性',10,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GENDER',N'2',N'女性',20,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GENDER',N'9',N'その他',90,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'ENROLLMENT_STATUS',N'01',N'在学',10,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'ENROLLMENT_STATUS',N'02',N'休学',20,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'ENROLLMENT_STATUS',N'03',N'卒業',30,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'ENROLLMENT_STATUS',N'04',N'退学',40,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'01',N'北海道',10,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'02',N'青森県',20,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'03',N'岩手県',30,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'04',N'宮城県',40,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'05',N'秋田県',50,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'06',N'山形県',60,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'07',N'福島県',70,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'08',N'茨城県',80,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'09',N'栃木県',90,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'10',N'群馬県',100,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'11',N'埼玉県',110,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'12',N'千葉県',120,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'13',N'東京都',130,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'14',N'神奈川県',140,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'15',N'新潟県',150,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'16',N'富山県',160,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'17',N'石川県',170,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'18',N'福井県',180,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'19',N'山梨県',190,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'20',N'長野県',200,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'21',N'岐阜県',210,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'22',N'静岡県',220,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'23',N'愛知県',230,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'24',N'三重県',240,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'25',N'滋賀県',250,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'26',N'京都府',260,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'27',N'大阪府',270,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'28',N'兵庫県',280,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'29',N'奈良県',290,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'30',N'和歌山県',300,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'31',N'鳥取県',310,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'32',N'島根県',320,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'33',N'岡山県',330,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'34',N'広島県',340,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'35',N'山口県',350,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'36',N'徳島県',360,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'37',N'香川県',370,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'38',N'愛媛県',380,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'39',N'高知県',390,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'40',N'福岡県',400,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'41',N'佐賀県',410,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'42',N'長崎県',420,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'43',N'熊本県',430,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'44',N'大分県',440,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'45',N'宮崎県',450,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'46',N'鹿児島県',460,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'PREFECTURE',N'47',N'沖縄県',470,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'01',N'父',10,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'02',N'母',20,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'03',N'祖父',30,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'04',N'祖母',40,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'05',N'兄弟姉妹',50,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'06',N'配偶者',60,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'07',N'後見人',70,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'RELATIONSHIP',N'99',N'その他',990,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'00',N'学年なし',0,1,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'01',N'1年',10,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'02',N'2年',20,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'03',N'3年',30,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'04',N'4年',40,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'05',N'5年',50,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(N'GRADE',N'06',N'6年',60,0,1,N'1900-01-01',NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1);
END;

IF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES (1,2026,N'GRADE',N'01',N'TRN-A',N'訓練一組',N'2026-04-01',N'2027-03-31',30,10,1,NULL)) AS expected([class_id],[school_year],[grade_category],[grade_code],[class_code],[class_name],[valid_from],[valid_to],[capacity],[display_order],[is_active],[remarks]) EXCEPT SELECT [class_id],[school_year],[grade_category],[grade_code],[class_code],[class_name],[valid_from],[valid_to],[capacity],[display_order],[is_active],[remarks] FROM dbo.[m_class]) THROW 51012,'Seeded business values changed; no changes.',1;
IF @seed IS NULL BEGIN
SET IDENTITY_INSERT dbo.[m_class] ON;
INSERT dbo.[m_class] ([class_id],[school_year],[grade_category],[grade_code],[class_code],[class_name],[valid_from],[valid_to],[capacity],[display_order],[is_active],[remarks],[created_at],[created_by],[updated_at],[updated_by],[row_version]) VALUES
(1,2026,N'GRADE',N'01',N'TRN-A',N'訓練一組',N'2026-04-01',N'2027-03-31',30,10,1,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1);
SET IDENTITY_INSERT dbo.[m_class] OFF;
END;

IF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES (1,N'TRN001',N'検証太郎',N'ケンショウタロウ',N'検証太郎',N'ケンショウタロウ',N'1998-04-01',N'GENDER',N'1',N'0000000',N'PREFECTURE',N'13',N'架空住所1',NULL,N'0312345678',NULL,N'2026-04-01',N'ENROLLMENT_STATUS',N'01',NULL,1,NULL,NULL,NULL,NULL,N'架空の確認データ',0,NULL,NULL,NULL),(2,N'TRN002',N'検証花子',N'ケンショウハナコ',N'検証花子',N'ケンショウハナコ',N'1999-05-02',N'GENDER',N'2',N'0000000',N'PREFECTURE',N'13',N'架空住所2',NULL,N'0312345679',NULL,N'2026-04-01',N'ENROLLMENT_STATUS',N'01',NULL,1,NULL,NULL,NULL,NULL,N'架空の確認データ',0,NULL,NULL,NULL)) AS expected([student_id],[student_no],[student_name],[student_name_kana],[name_key],[kana_key],[birth_date],[gender_category],[gender_code],[postal_code],[prefecture_category],[prefecture_code],[address_line1],[address_line2],[phone_number],[email_address],[admission_date],[enrollment_category],[enrollment_status_code],[enrollment_end_date],[class_id],[emergency_contact_name],[relationship_category],[relationship_code],[emergency_phone_number],[remarks],[is_deleted],[deleted_at],[deleted_by],[delete_reason]) EXCEPT SELECT [student_id],[student_no],[student_name],[student_name_kana],[name_key],[kana_key],[birth_date],[gender_category],[gender_code],[postal_code],[prefecture_category],[prefecture_code],[address_line1],[address_line2],[phone_number],[email_address],[admission_date],[enrollment_category],[enrollment_status_code],[enrollment_end_date],[class_id],[emergency_contact_name],[relationship_category],[relationship_code],[emergency_phone_number],[remarks],[is_deleted],[deleted_at],[deleted_by],[delete_reason] FROM dbo.[m_student]) THROW 51012,'Seeded business values changed; no changes.',1;
IF @seed IS NULL BEGIN
SET IDENTITY_INSERT dbo.[m_student] ON;
INSERT dbo.[m_student] ([student_id],[student_no],[student_name],[student_name_kana],[name_key],[kana_key],[birth_date],[gender_category],[gender_code],[postal_code],[prefecture_category],[prefecture_code],[address_line1],[address_line2],[phone_number],[email_address],[admission_date],[enrollment_category],[enrollment_status_code],[enrollment_end_date],[class_id],[emergency_contact_name],[relationship_category],[relationship_code],[emergency_phone_number],[remarks],[is_deleted],[deleted_at],[deleted_by],[delete_reason],[created_at],[created_by],[updated_at],[updated_by],[row_version]) VALUES
(1,N'TRN001',N'検証太郎',N'ケンショウタロウ',N'検証太郎',N'ケンショウタロウ',N'1998-04-01',N'GENDER',N'1',N'0000000',N'PREFECTURE',N'13',N'架空住所1',NULL,N'0312345678',NULL,N'2026-04-01',N'ENROLLMENT_STATUS',N'01',NULL,1,NULL,NULL,NULL,NULL,N'架空の確認データ',0,NULL,NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1),
(2,N'TRN002',N'検証花子',N'ケンショウハナコ',N'検証花子',N'ケンショウハナコ',N'1999-05-02',N'GENDER',N'2',N'0000000',N'PREFECTURE',N'13',N'架空住所2',NULL,N'0312345679',NULL,N'2026-04-01',N'ENROLLMENT_STATUS',N'01',NULL,1,NULL,NULL,NULL,NULL,N'架空の確認データ',0,NULL,NULL,NULL,SYSUTCDATETIME(),N'verification-admin',SYSUTCDATETIME(),N'verification-admin',1);
SET IDENTITY_INSERT dbo.[m_student] OFF;
END;

IF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES (N'verification-admin',N'Admin'),(N'verification-staff',N'Staff'),(N'verification-reader',N'Reader')) AS expected([user_id],[role_name]) EXCEPT SELECT [user_id],[role_name] FROM dbo.[t_app_role]) THROW 51012,'Seeded business values changed; no changes.',1;
IF @seed IS NULL BEGIN
INSERT dbo.[t_app_role] ([user_id],[role_name]) VALUES
(N'verification-admin',N'Admin'),
(N'verification-staff',N'Staff'),
(N'verification-reader',N'Reader');
END;

IF @seed IS NOT NULL AND EXISTS (SELECT * FROM (VALUES (1,0)) AS expected([guard_id],[lock_bit]) EXCEPT SELECT [guard_id],[lock_bit] FROM dbo.[t_write_guard]) THROW 51012,'Seeded business values changed; no changes.',1;
IF @seed IS NULL BEGIN
INSERT dbo.[t_write_guard] ([guard_id],[lock_bit]) VALUES
(1,0);
END;
IF @seed IS NULL EXEC sys.sp_addextendedproperty @name=N'AccessRebuilderSeed',@value=N'ACCESS-REBUILDER-TRAINING-V1';
COMMIT TRANSACTION;
