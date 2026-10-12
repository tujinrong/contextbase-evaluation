IF DB_ID(N'contextbase_test_project1_vb') IS NOT NULL THROW 51129,'Existing DB is preserved. Use Validate, or supply another approved fixture through a separate operation.',1;
EXEC(N'CREATE DATABASE [contextbase_test_project1_vb]');
EXEC(N'ALTER DATABASE [contextbase_test_project1_vb] SET COMPATIBILITY_LEVEL = 160');