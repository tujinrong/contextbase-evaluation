IF DB_ID(N'contextbase_test_project1_wpf') IS NOT NULL THROW 51129,'Existing DB is preserved. Use Validate, or supply another approved fixture through a separate operation.',1;
EXEC(N'CREATE DATABASE [contextbase_test_project1_wpf]');
EXEC(N'ALTER DATABASE [contextbase_test_project1_wpf] SET COMPATIBILITY_LEVEL = 160');