SELECT school_year,grade_code,CONVERT(char(10),valid_from,23),CONVERT(char(10),valid_to,23),is_active,capacity FROM dbo.m_class WHERE class_id=?;
