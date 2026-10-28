SELECT COUNT_BIG(*) FROM dbo.m_student WHERE student_no=? AND (? IS NULL OR student_id<>?);
