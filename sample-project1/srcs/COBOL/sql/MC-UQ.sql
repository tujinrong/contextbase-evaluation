SELECT COUNT_BIG(*) FROM dbo.m_class WHERE school_year=? AND class_code=? AND (? IS NULL OR class_id<>?);
