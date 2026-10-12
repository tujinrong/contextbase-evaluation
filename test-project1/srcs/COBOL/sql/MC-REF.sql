SELECT COUNT_BIG(*),COALESCE(SUM(CONVERT(bigint,CASE WHEN is_deleted=0 AND enrollment_status_code IN ('01','02') THEN 1 ELSE 0 END)),0) FROM dbo.m_student WHERE class_id=?;
