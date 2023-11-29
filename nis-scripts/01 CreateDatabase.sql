USE [master]
GO

IF DB_ID('DriveThruCorp') IS NULL BEGIN
	CREATE DATABASE [DriveThruCorp]
		ON PRIMARY (
			NAME = DriveThruCorp_data,
			FILENAME =  N'/var/opt/sqlserver/data/DriveThruCorp.mdf',
			SIZE = 1 MB,
			MAXSIZE = UNLIMITED,
			FILEGROWTH = 10%
		) 
		LOG ON
		(
			NAME = DriveThruCorp_log,
			FILENAME =  N'/var/opt/sqlserver/data/DriveThruCorp.ldf',
			SIZE = 1 MB,
			MAXSIZE = UNLIMITED,
			FILEGROWTH = 10%
		)
		COLLATE Latin1_General_CI_AS

END
GO


if not exists(select * from sys.server_principals sp where name = 'orfappl') BEGIN
	CREATE LOGIN orfappl WITH PASSWORD = 'sx350cdi',
	CHECK_POLICY     = OFF,
    CHECK_EXPIRATION = OFF;
	EXEC sp_addsrvrolemember 
    @loginame = N'orfappl', 
    @rolename = N'sysadmin';
END

