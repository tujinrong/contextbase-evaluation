SELECT COUNT_BIG(*) FROM dbo.m_class WHERE school_year=? AND grade_code=? AND class_name=? AND (? IS NULL OR class_id<>?);
