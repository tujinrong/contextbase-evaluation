SELECT code_name,display_order,is_active,CONVERT(char(10),valid_from,23),CONVERT(char(10),valid_to,23),remarks,is_protected,row_version FROM dbo.m_code WHERE category_id=? AND code_value=?;
