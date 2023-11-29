


--if not exists(select * from sys.database_principals where name = 'orfappl') BEGIN
--	CREATE LOGIN orfappl WITH PASSWORD = 'sx350cdi',
--	CHECK_POLICY     = OFF,
--    CHECK_EXPIRATION = OFF;
--	EXEC sp_addsrvrolemember 
--    @loginame = N'orfappl', 
--    @rolename = N'sysadmin';
--END





IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'Site') BEGIN
   -- DROP TABLE Site	
CREATE TABLE dbo.Site
(
    CompanyCode NVARCHAR(5),
    SiteCode NVARCHAR(10),
    SiteName NVARCHAR(50),
    SiteSqlInstance NVARCHAR(50),
    GpsLat DECIMAL(10,8),
    GpsLon DECIMAL(10,8),
    ShopId NVARCHAR(50),
    SecretKey NVARCHAR(50),
    WorkTime NVARCHAR(50),
    Address NVARCHAR(50),
    Contact NVARCHAR(50),
    SiteImage nvarchar(400),
    --LanguageName NVARCHAR(50),
    Id INT NOT NULL IDENTITY(1,1),
    CONSTRAINT PK_Site_Id PRIMARY KEY (Id)
) ON [PRIMARY]

END
GO



IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'Translation') BEGIN
   -- DROP TABLE Translation	
CREATE TABLE dbo.Translation
(
    LanguageId CHAR(2),
    TranslationLabel NVARCHAR(50),
    TranslatedText NVARCHAR(4000),
    TranslationSource NVARCHAR(50),
    --LanguageName NVARCHAR(50),
    Id INT NOT NULL IDENTITY(1,1),
    CONSTRAINT PK_Translation_Id PRIMARY KEY (Id),
    CONSTRAINT UQ_LangLabel UNIQUE(LanguageId, TranslationLabel)
) ON [PRIMARY]

END
GO


IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'ApplicationLog') BEGIN
   -- DROP TABLE ApplicationLog
CREATE TABLE dbo.ApplicationLog
(
    Id INT NOT NULL IDENTITY(1,1),
    HostName NVARCHAR(50),
    SiteCode NVARCHAR(50),
    InvoiceNo INT,
    Fp INT,
    OrderId NVARCHAR(50),
    LogSource NVARCHAR(50),
    HttpRequestType NVARCHAR(20),
    HttpRequestPath NVARCHAR(4000),
    HttpRequestData NVARCHAR(4000),
    HttpRequestHeaders NVARCHAR(4000),
    HttpResponseCode int,
    HttpResponseData NVARCHAR(4000),
    Command NVARCHAR(500),
    CommandRequest NVARCHAR(4000),
    CommandResult NVARCHAR(50),
    CommandResponse NVARCHAR(4000),
    CommandResponseCached BIT NOT NULL DEFAULT 0,
    DateHttpRequest DATETIME2 NULL,
    DateHttpResponse DATETIME2 NULL,
    DateRequest DATETIME2 NULL,
    DateResponse DATETIME2 NULL,
    HttpDurationMs INT,
    CommandDurationMs INT
        CONSTRAINT PK_ApplicationLog_Id PRIMARY KEY (Id)
) ON [PRIMARY]
END

GO

IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'DriveThruConfiguration') BEGIN
   -- DROP TABLE DriveThruConfiguration	
CREATE TABLE dbo.DriveThruConfiguration
(
    Id INT NOT NULL IDENTITY(1,1),
    ParameterName NVARCHAR(50),
    ParameterDescription NVARCHAR(4000),
    ParameterValue1 NVARCHAR(500),
    ParameterValue2 INT
) ON [PRIMARY]
END
GO














IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'ApplicationUserStatus') BEGIN
   -- DROP TABLE ApplicationUserStatus	
CREATE TABLE dbo.[ApplicationUserStatus]
(
    Id INT NOT NULL IDENTITY(1,1),
    StatusId INT,
    StatusDescription NVARCHAR(150),
    EmailConfirmed BIT NOT NULL DEFAULT 0,
    SmsConfirmed BIT NOT NULL DEFAULT 0,
    LegalConfirmed BIT NOT NULL DEFAULT 0,
    PersonalDataConfirmed BIT NOT NULL DEFAULT 0,
    Active BIT NOT NULL DEFAULT 0,
    TranslationLabel NVARCHAR(50),
    CONSTRAINT PK_ApplicationUserStatus_Id PRIMARY KEY (Id)
    ) ON [PRIMARY]
END

GO

IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'ApplicationUserStatusFlow') BEGIN
   -- DROP TABLE ApplicationUserStatusFlow	

CREATE TABLE [dbo].[ApplicationUserStatusFlow](
    [Id] [int] IDENTITY(1,1) NOT NULL,
    [StatusDescription] NVARCHAR(150)
    CONSTRAINT [PK_ApplicationUserStatusFlow_Id] PRIMARY KEY CLUSTERED
(
[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END
GO




IF NOT EXISTS (SELECT 1 FROM sys.tables t WHERE t.name = 'ApplicationUserStatusFlowLog') BEGIN
  -- DROP TABLE [ApplicationUserStatusFlowLog]	
CREATE TABLE [dbo].[ApplicationUserStatusFlowLog](
    [Id] [int] IDENTITY(1,1) NOT NULL,
    [User_Id] INT NULL,
    [Command] [nvarchar](150) NULL,
    [StatusDescription] NVARCHAR(150) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    CONSTRAINT [PK_ApplicationUserStatusFlowLog_Id] PRIMARY KEY CLUSTERED
(
[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]

END
GO




IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'ApplicationUser') BEGIN

   -- DROP TABLE ApplicationUser

CREATE TABLE dbo.[ApplicationUser]
(
    Id INT NOT NULL IDENTITY(1,1),
    CompanyCode NVARCHAR(4),
    UserId NVARCHAR(50),
    DeviceId VARCHAR(36),
    Token NVARCHAR(2000),
    FirstName NVARCHAR(60),
    LastName NVARCHAR(60),
    Email NVARCHAR(50),
    Telephone NVARCHAR(50),
    City NVARCHAR(50),
    DateOfBirth DATE,
    PersonalizedOffers BIT,
    Offers BIT,
    EmailCodeSent BIT NOT NULL DEFAULT 0,
    EmailCode NVARCHAR(6),
    EmailCodeValidationExpiryDateUtc DATETIME2,
    SmsCodeSent BIT NOT NULL DEFAULT 0,
    SmsCode NVARCHAR(6),
    SmsCodeValidationExpiryDateUtc DATETIME2,
    LicensePlate NVARCHAR(60),
    NewCard BIT,
    HasPin BIT,
    PinHash NVARCHAR(4000),
    PinSalt NVARCHAR(4000),
    ChangeEmailOrTelephone BIT,
    ApplicationUserStatusId INT,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    DateModified DATETIME2
    CONSTRAINT PK_ApplicationUser_Id PRIMARY KEY (Id)
    CONSTRAINT FK_ApplicationUserStatus FOREIGN KEY(ApplicationUserStatusId) REFERENCES ApplicationUserStatus(Id)
    ) ON [PRIMARY]

END
GO






IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'ApplicationUserPaymentCard') BEGIN

   -- DROP TABLE ApplicationUserPaymentCard

CREATE TABLE dbo.ApplicationUserPaymentCard
(
    Id INT NOT NULL IDENTITY(1,1),
    UserId NVARCHAR(50),
    OrderId NVARCHAR(50),
    CardToken NVARCHAR(50),
    CardNumber NVARCHAR(50),
    CardExpires NVARCHAR(50),
    CardType NVARCHAR(50),
    IsDefault BIT,
    ApplicationUserId INT,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    DateModified DATETIME2
        CONSTRAINT PK_ApplicationUserPaymentCard_Id PRIMARY KEY (Id),
    CONSTRAINT FK_ApplicationUser FOREIGN KEY (ApplicationUserId) REFERENCES ApplicationUser(Id) ON DELETE CASCADE
) ON [PRIMARY]

END
GO



IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'ApplicationUserPaymentCardRegistrationLog') BEGIN

   -- DROP TABLE ApplicationUserPaymentCardRegistrationLog

CREATE TABLE dbo.ApplicationUserPaymentCardRegistrationLog
(
    Id INT NOT NULL IDENTITY(1,1),
    UserId NVARCHAR(50),
    OrderId NVARCHAR(50),
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_ApplicationUserPaymentCardRegistrationLog_Id PRIMARY KEY (Id)
) ON [PRIMARY]

END
GO


if (select count(*) from sys.tables t where t.name = 'ServiceType') = 0
begin
create table ServiceType
(
    Id int IDENTITY(1,1) not null,
    TypeName nvarchar(50) null,
    CONSTRAINT [PK_ServiceType] PRIMARY KEY CLUSTERED
        (
        [Id] ASC
        ) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [primary]
end
GO

if (select count(*) from sys.tables t where t.name = 'SiteWorkingDay') = 0
begin
create table SiteWorkingDay
(
    Id int IDENTITY(1,1) not null,
    SiteCode nvarchar(50) null,
    Day nvarchar(50) null,
    StartTime nvarchar(20) null,
    EndTime nvarchar(20) null
        CONSTRAINT [PK_SiteWorkingDay] PRIMARY KEY CLUSTERED
        (
        [Id] ASC
        ) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [primary]
end
GO

if (select count(*) from sys.tables t where t.name = 'SiteService') = 0
begin
create table SiteService
(
    Id int IDENTITY(1,1) not null,
    ServiceName nvarchar(50) null,
    Image nvarchar(400) null,
    Color nvarchar(50) null,
    ServiceTypeId INT NOT NULL,
    CONSTRAINT [FK_SiteService_ServiceType] FOREIGN KEY ([ServiceTypeId]) REFERENCES [dbo].[ServiceType] ([Id]),
    CONSTRAINT [PK_SiteService] PRIMARY KEY CLUSTERED
        (
        [Id] ASC
        ) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [primary]
end
GO
    
IF (SELECT COUNT(*) FROM sys.tables t WHERE t.name = 'SiteServices') = 0
BEGIN
CREATE TABLE [dbo].[SiteServices]
(
    Id int IDENTITY(1,1) not null,
    SiteId int NOT NULL,
    SiteServiceId int NOT NULL,
    CONSTRAINT [FK_SiteServices_Site] FOREIGN KEY ([SiteId]) REFERENCES [dbo].[Site] ([Id]),
    CONSTRAINT [FK_SiteServices_SiteServices] FOREIGN KEY ([SiteServiceId]) REFERENCES [dbo].[SiteService] ([Id])
    ) ON [PRIMARY]
end
GO
if (select COUNT(*) from sys.all_columns c where c.name = 'FcmToken' and object_id = object_id('ApplicationUser')) = 0
begin
alter table ApplicationUser add FcmToken nvarchar(255) null;
end
go

IF NOT EXISTS(SELECT 1 FROM sys.tables t WHERE name = 'tMobMarketing') BEGIN
CREATE TABLE [dbo].[tMobMarketing](
    [ID] [int] IDENTITY(1,1) NOT NULL,
    [Naslov] [nvarchar](100) NULL,
    [Podnaslov] [nvarchar](200) NULL,
    [Tekst] [nvarchar](max) NULL,
    [Slika] [nvarchar](255) NULL,
    [Pdf] [nvarchar](255) NULL,
    [DatumKreiranja] [datetime] NULL,
    [DatumAzuriranja] [datetime] NULL,
    [Korisnik] [nvarchar](100) NULL,
    [PoslataNotifikacija] [bit] NULL,
    [DatumOd] [date] NULL,
    [DatumDo] [date] NULL,
    [Prioritet] [int] NULL,
    [TipPromocije] [int] NULL,
    [BirthDayPromotion] [bit] NULL,
    [Kupon] [bit] NULL,
    [Pravilo_id] [int] NULL,
    [Promocija] [bit] NULL,
    [Benzinska_stanica] [nvarchar](10) NULL,
    [Banner] [bit] NULL,
    PRIMARY KEY CLUSTERED
(
[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
END
GO
--IF EXISTS (SELECT 1 FROM sys.procedures p WHERE p.name ='ApplicationUserUpdate')
--	DROP PROCEDURE ApplicationUserUpdate

--GO

--CREATE PROCEDURE ApplicationUserUpdate	
--	@Id INT,
--	@UserId VARCHAR(36),
--	@DeviceId NVARCHAR(36),
--	@Token NVARCHAR(36),
--	@Email NVARCHAR(50),
--	@FirstName NVARCHAR(50),
--	@LastName NVARCHAR(50),
--	@Telephone NVARCHAR(50),
--	@UserStatus INT
--AS


--UPDATE ApplicationUser SET 
--	UserId = @UserId,
--	DeviceId = @DeviceId,
--	Token = @Token,
--	Email = @Email,
--	FirstName = @FirstName,
--	Telephone = @Telephone,
--	UserStatus = @UserStatus

--SELECT u.Id
--	  ,u.CompanyCode
--	  ,u.UserId
--	  ,u.DeviceId
--	  ,u.Token
--	  ,u.Email
--	  ,u.FirstName
--	  ,u.LastName
--	  ,u.Telephone
--	  ,u.EMailCode
--	  ,u.EMailCodeValidationExpiryDate
--	  ,u.SmsCode
--	  ,u.SmsCodeValidationExpiryDate
--	  ,u.ApplicationUserStatus
--FROM ApplicationUser u


--GO


