SELECT COUNT_BIG(*) FROM dbo.m_student WHERE class_id=? AND is_deleted=0 AND enrollment_status_code IN ('01','02') AND (? IS NULL OR student_id<>?);
