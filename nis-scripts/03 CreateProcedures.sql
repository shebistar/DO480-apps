--*******************


use DriveThruCorp

GO


CREATE OR ALTER PROCEDURE ApplicationLogHttpInsert
	@LogSource NVARCHAR(50),
	@HostName NVARCHAR(50),
	@OrderId NVARCHAR(50),
	@HttpRequestType NVARCHAR(20),
	@HttpRequestPath NVARCHAR(4000),
    @HttpRequestData NVARCHAR(4000),
	@HttpRequestHeaders NVARCHAR(4000) = NULL,
	@Sitecode NVARCHAR(50) = NULL,
	@InvoiceNo INT = NULL,
	@Fp INT = NULL
AS
	IF @HttpRequestData ='' SET @HttpRequestData = NULL

	IF NOT EXISTS (SELECT 1 FROM ApplicationLog al WHERE al.OrderId = @OrderId AND al.LogSource = @LogSource) BEGIN
	INSERT INTO ApplicationLog (LogSource, HostName, OrderId, HttpRequestType,HttpRequestPath, HttpRequestData, HttpRequestHeaders, DateHttpRequest, Sitecode, InvoiceNo, Fp)
	VALUES (@LogSource, @HostName, @OrderId, @HttpRequestType, @HttpRequestPath, @HttpRequestData, @HttpRequestHeaders, SYSDATETIME(), @Sitecode, @InvoiceNo, @Fp);
END ELSE BEGIN 
	UPDATE ApplicationLog SET 
		HostName = Hostname + ':' + @HostName,
		HttpRequestType = @HttpRequestType,
		HttpRequestPath = @HttpRequestPath,
		HttpRequestData = @HttpRequestData,
		DateHttpResponse = SYSDATETIME()
	WHERE OrderId = @OrderId AND LogSource = @LogSource
END
GO





--*******************

CREATE OR ALTER PROCEDURE ApplicationLogHttpUpdate
    @LogSource NVARCHAR(50),
	@HostName NVARCHAR(50),
	@OrderId NVARCHAR(50),
	@HttpResponseCode INT,
	@HttpResponseData NVARCHAR(4000),
	@Sitecode NVARCHAR(50) = NULL,
	@InvoiceNo INT = NULL,
	@Fp INT = NULL
AS
	DECLARE @time DATETIME2 = SYSDATETIME()

	IF NOT EXISTS(SELECT 1 FROM ApplicationLog al WHERE al.OrderId = @OrderId AND al.LogSource = @LogSource) BEGIN
		INSERT INTO ApplicationLog (LogSource, HostName, OrderId, HttpResponseCode, HttpResponseData, SiteCode , InvoiceNo, Fp)
		VALUES (@LogSource, @HostName, @OrderId, @HttpResponseCode, @HttpResponseData, @Sitecode, @InvoiceNo, @Fp);
	END ELSE BEGIN
		UPDATE ApplicationLog SET
		    HostName = Hostname + ':' + @HostName,
			HttpResponseCode = @HttpResponseCode,
			HttpResponseData = @HttpResponseData,
			DateHttpResponse = @time,
			HttpDurationMs = DATEDIFF(MILLISECOND, DateHttpRequest,  @time)
		WHERE OrderId = @OrderId AND LogSource = @LogSource
	END

GO




--*******************

CREATE OR ALTER PROCEDURE ApplicationLogInsert
    @LogSource NVARCHAR(50),
	@HostName NVARCHAR(50),
	@OrderId NVARCHAR(50),
	@Command NVARCHAR(500),
	@CommandRequest NVARCHAR(4000),
	@Sitecode NVARCHAR(50) = NULL,
	@InvoiceNo INT = NULL,
	@Fp INT = NULL
AS
	IF NOT EXISTS(SELECT 1 FROM ApplicationLog al WHERE al.OrderId = @OrderId AND al.LogSource = @LogSource) begin
		INSERT INTO ApplicationLog (LogSource, OrderId, Command, CommandRequest, DateRequest, SiteCode, InvoiceNo, Fp)
		VALUES (@LogSource, @OrderId, @Command, @CommandRequest, SYSDATETIME(), @Sitecode, @InvoiceNo, @Fp);
	END ELSE BEGIN
		UPDATE ApplicationLog SET
			Command = @Command,
			CommandRequest = @CommandRequest,
			DateRequest = SYSDATETIME()
		WHERE OrderId = @OrderId
	END

GO



--*******************

CREATE OR ALTER PROCEDURE ApplicationLogUpdate
	@LogSource NVARCHAR(50),
	@HostName NVARCHAR(50),
	@OrderId NVARCHAR(50),
	@CommandResult NVARCHAR(50),
	@CommandResponse NVARCHAR(4000),
	@CommandResponseCached BIT,
	@Sitecode NVARCHAR(50) = NULL,
	@InvoiceNo INT = NULL,
	@Fp INT = NULL
AS
	DECLARE @time DATETIME2 = SYSDATETIME()

	UPDATE ApplicationLog
	SET CommandResult = @CommandResult,
		CommandResponse = @CommandResponse,
		DateResponse = @time,
		CommandResponseCached = @CommandResponseCached,
		CommandDurationMs = DATEDIFF(MILLISECOND, DateRequest,  @time),
		SiteCode = @Sitecode,
		InvoiceNo = @InvoiceNo,
		Fp = @Fp
	WHERE OrderId = @OrderId AND LogSource = @LogSource

GO


--*******************
DROP PROCEDURE IF EXISTS ApplicationUserAddPaymentCard 
GO
CREATE PROCEDURE ApplicationUserAddPaymentCard
	@User_Id INT,
	@OrderId NVARCHAR(50),
	@CardToken NVARCHAR(50),
	@CardNumber NVARCHAR(50),
	@CardExpires NVARCHAR(50),
	@CardType NVARCHAR(50)

AS
	DECLARE @userid NVARCHAR(50)
	DECLARE @NumberOfCards INT

	SELECT @userid = au.UserId FROM ApplicationUser au WHERE au.Id = @User_Id

	IF NOT EXISTS(SELECT 1 FROM ApplicationUserPaymentCard aubc WHERE aubc.ApplicationUserId = @User_Id AND aubc.CardToken = @CardToken)
		INSERT INTO ApplicationUserPaymentCard (OrderId, CardToken, CardNumber, CardExpires, CardType, IsDefault, ApplicationUserId, DateCreated)
		VALUES (@OrderId, @CardToken, @CardNumber, @CardExpires, @CardType, 0, @User_Id, DEFAULT);

	SELECT @NumberOfCards = COUNT(*) FROM ApplicationUserPaymentCard WHERE ApplicationUserId = @User_Id

	IF(@NumberOfCards = 1)
		UPDATE ApplicationUserPaymentCard SET IsDefault = 1 WHERE ApplicationUserId = @User_Id

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND au.ApplicationUserStatusId = (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'ACTIVE')

GO




--*******************
DROP PROCEDURE IF EXISTS ApplicationUserByUserId 
GO
CREATE PROCEDURE ApplicationUserByUserId
	@userid NVARCHAR(36)
AS
	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	LEFT OUTER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND (au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE') OR au.ApplicationUserStatusId IS NULL)

GO




--*******************
DROP PROCEDURE IF EXISTS ApplicationUserByOrderId 
GO
CREATE PROCEDURE ApplicationUserByOrderId
	@orderid VARCHAR(36)
AS
	DECLARE @userid NVARCHAR(50)
	SELECT TOP 1 @userid = UserId FROM ApplicationUserPaymentCardRegistrationLog 
			WHERE OrderId = @orderid
			ORDER BY DateCreated DESC

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND au.ApplicationUserStatusId = (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'ACTIVE')

GO



--*******************
DROP PROCEDURE IF EXISTS ApplicationUserDeletePaymentCard 
GO
CREATE PROCEDURE ApplicationUserDeletePaymentCard
	@UserId NVARCHAR(50),
	@CardToken NVARCHAR(50)

AS
	DECLARE @id int

	SELECT @id = au.Id FROM ApplicationUser au WHERE au.UserId = @UserId AND au.ApplicationUserStatusId = (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='ACTIVE')

    DELETE FROM ApplicationUserPaymentCard WHERE ApplicationUserId = @id AND CardToken = @CardToken

	UPDATE ApplicationUserPaymentCard SET IsDefault = 0 WHERE ApplicationUserId = @id

	IF NOT EXISTS(SELECT 1 FROM ApplicationUserPaymentCard aupc WHERE aupc.ApplicationUserId= @id AND aupc.IsDefault = 1) BEGIN
		;WITH cte AS (
		SELECT TOP (1) *
		FROM ApplicationUserPaymentCard aubc
		WHERE aubc.ApplicationUserId = @id
		ORDER BY ID DESC
		)
		UPDATE cte SET IsDefault = 1 
	END

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')
GO



--*******************
DROP PROCEDURE IF EXISTS ApplicationUserDeletePaymentCards 
GO
CREATE PROCEDURE ApplicationUserDeletePaymentCards
	@UserId NVARCHAR(50)

AS
	DECLARE @id int

	SELECT @id = au.Id FROM ApplicationUser au WHERE au.UserId = @UserId AND au.ApplicationUserStatusId = (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='ACTIVE')

    DELETE FROM ApplicationUserPaymentCard WHERE ApplicationUserId = @id

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
		INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
		LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')
GO





--*******************
DROP PROCEDURE IF EXISTS ApplicationUserPreparePaymentCardRegistration 
GO
CREATE PROCEDURE [dbo].ApplicationUserPreparePaymentCardRegistration
	@userid NVARCHAR(50),
	@orderid NVARCHAR(50)

AS
	DECLARE @id NVARCHAR(50)

	INSERT INTO ApplicationUserPaymentCardRegistrationLog (UserId, OrderId)
	SELECT @userid, @orderid

GO




--*******************
DROP PROCEDURE IF EXISTS ApplicationUserSetDefaultPaymentCard 
GO
CREATE PROCEDURE ApplicationUserSetDefaultPaymentCard
	@UserId NVARCHAR(50),
	@CardToken NVARCHAR(50)

AS
	DECLARE @id int

	SELECT @id = au.Id FROM ApplicationUser au WHERE au.UserId = @UserId AND au.ApplicationUserStatusId = (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='ACTIVE')


	UPDATE ApplicationUserPaymentCard SET IsDefault = 0 WHERE ApplicationUserId = @id

	UPDATE ApplicationUserPaymentCard SET IsDefault = 1 WHERE ApplicationUserId = @id AND CardToken = @CardToken

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')


GO






--*******************
DROP PROCEDURE IF EXISTS ApplicationUserRegistration 
GO
CREATE PROCEDURE [dbo].[ApplicationUserRegistration]
	@deviceid VARCHAR(36),
	@token NVARCHAR(2000),
	@userid NVARCHAR(50),
	@email NVARCHAR(50) = null,
	@telephone NVARCHAR(50) = null
AS

DECLARE @deviceidexisting VARCHAR(36)

--new user
IF NOT EXISTS (SELECT 1 FROM ApplicationUser au WHERE au.UserId = @userid) BEGIN
	PRINT 'new user'
	INSERT INTO ApplicationUser (CompanyCode, UserId, DeviceId, Token, Email, Telephone, DateCreated)
	VALUES ('0001', @userid, @deviceid, @token, @email, @telephone, SYSDATETIME()
	--(SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='EMAIL_NOT_CONFIRMED')
	)

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	LEFT OUTER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND (au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE') OR au.ApplicationUserStatusId IS NULL)

	RETURN 0
END


SELECT @deviceidexisting = au.DeviceId FROM ApplicationUser au WHERE au.UserId = @UserId

--user exists on same deviceid, just return user 
IF EXISTS(SELECT 1 FROM ApplicationUser au WHERE au.UserId = @userid AND @deviceid = @deviceidexisting) BEGIN
	
	PRINT 'existing'
	
	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	LEFT OUTER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND (au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE') OR au.ApplicationUserStatusId IS NULL)

	RETURN 1
END 
	
--user exists new device id, preregistration
IF EXISTS(SELECT 1 FROM ApplicationUser au WHERE au.UserId = @userid and @deviceid <> @deviceidexisting) BEGIN
	PRINT 'pre-registration'
	DECLARE @id INT
	SELECT TOP (1) @id = id FROM ApplicationUser au WHERE au.UserId = @userid ORDER BY au.Id DESC

	DELETE FROM ApplicationUserPaymentCard WHERE ApplicationUserId = @id
	
	UPDATE ApplicationUser 
	SET DeviceId = @deviceid
		--,ApplicationUserStatusId = (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='EMAIL_NOT_CONFIRMED') 
	WHERE UserId = @userid



	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	LEFT OUTER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND (au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE') OR au.ApplicationUserStatusId IS NULL)

	RETURN 2
END 

GO



CREATE OR ALTER PROCEDURE ApplicationUserStatusFlowLogInsert 
	@user_id int,
	@command NVARCHAR(150),
	@statusDescription NVARCHAR(150)
AS

IF NOT EXISTS (SELECT 1 FROM ApplicationUserStatusFlowLog where [user_id] = @user_id AND Command =@command )
	INSERT INTO ApplicationUserStatusFlowLog (user_id, Command, StatusDescription)
	VALUES (@user_id, @command, @statusDescription);
GO


CREATE OR ALTER PROCEDURE ApplicationUserStatusFlowLogGet
	@user_id int,
	@command NVARCHAR(150)
AS

	SELECT TOP 1  ausfl.*, au.*, aus.*
	FROM ApplicationUserStatusFlowLog ausfl 
	INNER JOIN ApplicationUserStatus aus ON ausfl.StatusDescription = aus.StatusDescription
	INNER JOIN ApplicationUser au ON au.Id = ausfl.User_Id
	WHERE ausfl.[User_Id] = @user_id AND ausfl.Command = @command

GO



CREATE or ALTER PROCEDURE [dbo].ApplicationUserStatusGetNext
	@description NVARCHAR(50) = NULL	
AS

IF @description IS NULL BEGIN
	SELECT TOP 1 aus.*
	FROM ApplicationUserStatusFlow ausf
	INNER JOIN ApplicationUserStatus aus ON ausf.StatusDescription = aus.StatusDescription
	ORDER BY ausf.Id asc
	
	RETURN
END



DECLARE @currentid INT
DECLARE @maxid INT
DECLARE @nextStatusDescription NVARCHAR(150)

SELECT @maxid = MAX(id) FROM ApplicationUserStatusFlow ausf 
PRINT @maxid
SELECT @currentid = ausf.Id
FROM ApplicationUserStatusFlow ausf
INNER JOIN ApplicationUserStatus aus ON ausf.StatusDescription = aus.StatusDescription
WHERE aus.StatusDescription= @description

PRINT @currentid
--Status progess
IF @currentid < @maxid BEGIN 
	
	SELECT TOP 1 aus.*
		FROM ApplicationUserStatusFlow ausf
	INNER JOIN ApplicationUserStatus aus ON ausf.StatusDescription = aus.StatusDescription
	WHERE ausf.Id > @currentid
	ORDER BY ausf.Id ASC
END

--maximum status reached
IF @currentid = @maxid BEGIN 
	SELECT TOP 1 aus.*
	FROM ApplicationUserStatusFlow ausf
	INNER JOIN ApplicationUserStatus aus ON ausf.StatusDescription = aus.StatusDescription
	--WHERE ausf.Id = @currentid
	ORDER BY ausf.Id DESC
END


GO

--CREATE PROCEDURE ApplicationUserRegistration
--	@deviceid VARCHAR(36),
--	@token NVARCHAR(2000),
--	@userid NVARCHAR(50),
--	@otp NVARCHAR(4),
--	@otpexpirationdateutc DATETIME2
--AS

--DECLARE @deviceidexisting VARCHAR(36)

----new user
--IF NOT EXISTS (SELECT 1 FROM ApplicationUser au WHERE au.UserId = @userid) BEGIN
--	PRINT 'new user'
--	INSERT INTO ApplicationUser (CompanyCode, UserId, DeviceId, Token, ApplicationUserStatusId, EmailCode, EmailCodeValidationExpiryDateUtc, DateCreated)
--	VALUES ('0001', @userid, @deviceid, @token, (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='EMAIL_NOT_CONFIRMED'),
--	@otp,@otpexpirationdateutc ,GETDATE())

--	SELECT au.*, aus.*,aubc.*
--	FROM ApplicationUser au
--	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
--	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
--	WHERE 
--	au.UserId = @userid
--	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')

--	RETURN 0
--END


--SELECT @deviceidexisting = au.DeviceId FROM ApplicationUser au WHERE au.UserId = @UserId

----user exists on same deviceid, just return user 
--IF EXISTS(SELECT 1 FROM ApplicationUser au WHERE au.UserId = @userid AND @deviceid = @deviceidexisting) BEGIN
	
--	PRINT 'existing'
	
--	SELECT au.*, aus.*,aubc.*
--	FROM ApplicationUser au
--	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
--	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
--	WHERE 
--	au.UserId = @userid
--	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')

--	RETURN 1
--END 
	
----user exists new device id, preregistration
--IF EXISTS(SELECT 1 FROM ApplicationUser au WHERE au.UserId = @userid and @deviceid <> @deviceidexisting) BEGIN
--	PRINT 'pre-registration'
--	DECLARE @id INT
--	SELECT TOP (1) @id = id FROM ApplicationUser au WHERE au.UserId = @userid ORDER BY au.Id DESC

--	DELETE FROM ApplicationUserPaymentCard WHERE ApplicationUserId = @id
	
--	UPDATE ApplicationUser 
--	SET DeviceId = @deviceid
--		,ApplicationUserStatusId = (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='EMAIL_NOT_CONFIRMED') 
--	WHERE UserId = @userid



--	SELECT au.*, aus.*,aubc.*
--	FROM ApplicationUser au
--	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
--	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
--	WHERE 
--	au.UserId = @userid
--	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')

--	RETURN 2
--END 

--GO





--*******************
DROP PROCEDURE IF EXISTS ApplicationUserSaveOrUpdate 
GO
CREATE PROCEDURE ApplicationUserSaveOrUpdate
	@Id INT,
	@UserId NVARCHAR(50),
	@DeviceId VARCHAR(36),
	@Token NVARCHAR(2000),
	--@Email VARCHAR(100),
	@FirstName nvarchar(60),
	@LastName nvarchar(60),
	@City NVARCHAR(50),
	@DateOfBirth DATE,
	@Telephone nvarchar(50),
	@PersonalizedOffers bit,
	@Offers bit,
	@EmailCodeSent bit,
	@EmailCode nvarchar(6),
	@EmailCodeValidationExpiryDateUtc datetime2(7),
	@SmsCodeSent bit,
	@SmsCode nvarchar(6),
	@SmsCodeValidationExpiryDateUtc datetime2(7),
	@HasPin BIT,
	@ChangeEmailOrTelephone BIT,
	@ApplicationUserStatusId INT,
	@Address NVARCHAR(60)=NULL,
	@CardNumber NVARCHAR(60)=NULL,
	@LicensePlate NVARCHAR(60)=NULL,
	@NewCard BIT = NULL
AS

DECLARE @languageid NVARCHAR(2) = 'EN'



IF(@Id = 0 ) BEGIN --AND NOT exists(SELECT 1 FROM ApplicationUser au WHERE au.UserId =@useridgid)
	
	INSERT INTO ApplicationUser (CompanyCode, UserId, DeviceId, Token, ApplicationUserStatusId, EmailCode, EmailCodeValidationExpiryDateUtc, DateCreated)
	VALUES ('0001', @UserId, @deviceid, @token, (SELECT Id FROM ApplicationUserStatus aus WHERE aus.StatusDescription='EMAIL_NOT_CONFIRMED'),
	@EmailCode,@EmailCodeValidationExpiryDateUtc ,SYSDATETIME());

END ELSE BEGIN

	UPDATE ApplicationUser 
	SET 
	    FirstName = @FirstName
	   ,LastName = @LastName
	   ,City = @City
	   ,DateOfBirth = @DateOfBirth
	   ,Telephone = @Telephone
	   ,PersonalizedOffers = @PersonalizedOffers
	   ,Offers = @Offers
	   ,Token = @Token
	   ,UserId = @UserId
	   ,EmailCodeSent = @EmailCodeSent
	   ,EmailCode = @EmailCode
	   ,EmailCodeValidationExpiryDateUtc = @EmailCodeValidationExpiryDateUtc
	   ,SmsCodeSent = @SmsCodeSent
	   ,SmsCode = @SmsCode
	   ,SmsCodeValidationExpiryDateUtc = @SmsCodeValidationExpiryDateUtc
	   ,HasPin = @HasPin
	   ,ChangeEmailOrTelephone = @ChangeEmailOrTelephone
	   ,ApplicationUserStatusId = @ApplicationUserStatusId
	    ,Address = @Address
		,LicensePlate = @LicensePlate
		,NewCard = @NewCard
		,CardNumber = @CardNumber
	   ,DateModified = SYSDATETIME()
	WHERE Id = @Id --UserId = @UserId AND DeviceId = @DeviceId
END

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.Id = @Id
	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')


GO






--*******************
DROP PROCEDURE IF EXISTS ApplicationUserSetPin 
GO
CREATE PROCEDURE ApplicationUserSetPin
	@UserId NVARCHAR(50),
	@PinHash NVARCHAR(4000),
	@PinSalt NVARCHAR(4000)
AS
	UPDATE ApplicationUser SET 
		HasPin = 1,
		PinHash = @PinHash,
		PinSalt = @PinSalt
	WHERE UserId = @UserId
	AND ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')

	SELECT au.*, aus.*,aubc.*
	FROM ApplicationUser au
	INNER JOIN ApplicationUserStatus aus ON aus.Id = au.ApplicationUserStatusId
	LEFT OUTER JOIN ApplicationUserPaymentCard aubc ON au.Id = aubc.ApplicationUserId
	WHERE 
	au.UserId = @userid
	AND au.ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')
GO



--*******************
DROP PROCEDURE IF EXISTS ApplicationUserDeactivate 
GO
CREATE PROCEDURE ApplicationUserDeactivate
	@UserId NVARCHAR(50)
AS
	DECLARE @deactivatedstatus INT
	SELECT @deactivatedstatus = aus1.Id FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE'

	UPDATE ApplicationUser SET 
		ApplicationUserStatusId = @deactivatedstatus,
		Token = NULL,
		FirstName = NULL,
		LastName = NULL,
		Telephone= NULL,
		DateOfBirth = NULL,
		PersonalizedOffers = 0,
		Offers = 0
	WHERE UserId = @UserId
	AND ApplicationUserStatusId <> (SELECT aus1.Id  FROM ApplicationUserStatus aus1 WHERE aus1.StatusDescription = 'INACTIVE')

GO




--*******************
DROP PROCEDURE IF EXISTS ApplicationUserStatusByStatusDescription 
GO
CREATE PROCEDURE ApplicationUserStatusByStatusDescription
	@description NVARCHAR(50)
AS

SELECT * FROM ApplicationUserStatus aus WHERE aus.StatusDescription = @description

GO






--TRANSLATIONS
--*******************
DROP PROCEDURE IF EXISTS TranslationGetAll 
GO
CREATE PROCEDURE TranslationGetAll
	@source NVARCHAR(50) = NULL
AS

	SELECT * FROM Translation t 
	WHERE  (t.TranslationSource = @source OR @source IS NULL)

GO



--*******************
DROP PROCEDURE IF EXISTS TranslationGetById 
GO
CREATE PROCEDURE TranslationGetById
	@id INT
AS


	SELECT * FROM Translation t WHERE t.Id = @id

GO




--*******************
DROP PROCEDURE IF EXISTS TranslationGetByLabel 
GO
CREATE PROCEDURE TranslationGetByLabel
	@label NVARCHAR(50)
AS


	SELECT * FROM Translation t WHERE t.TranslationLabel = @label

GO

--*******************
DROP PROCEDURE IF EXISTS TranslationSaveOrUpdate 
GO
CREATE PROCEDURE [dbo].TranslationSaveOrUpdate
	@languageId CHAR(2),
	@translationLabel NVARCHAR(50),
	@translatedText NVARCHAR(4000),
	@translationSource NVARCHAR(50)  = NULL
AS

IF(@translationSource IS NULL) BEGIN
	SET @translationSource = 'MobileApp'
END

IF NOT EXISTS (SELECT 1 FROM Translation t WHERE t.LanguageId = @LanguageId AND t.TranslationLabel = @TranslationLabel) BEGIN 
	INSERT INTO Translation (LanguageId, TranslationLabel, TranslatedText, TranslationSource)
	VALUES (@LanguageId, @TranslationLabel, @TranslatedText, @translationSource);
END ELSE BEGIN
	UPDATE Translation 
		SET TranslatedText = @translatedText
	WHERE LanguageId = @LanguageId 
		AND TranslationLabel = @translationLabel
		AND TranslationSource = @translationSource
END

	SELECT * FROM Translation WHERE LanguageId = @LanguageId AND TranslationLabel = @TranslationLabel 

GO







--*******************
DROP PROCEDURE IF EXISTS TranslationDelete 
GO
CREATE PROCEDURE [dbo].TranslationDelete
	@languageId CHAR(2),
	@translationLabel NVARCHAR(50)
AS

	DELETE FROM Translation WHERE LanguageId = @languageId AND TranslationLabel = @translationLabel

GO

--*******************
DROP PROCEDURE IF EXISTS SiteGet 
GO
CREATE PROCEDURE [dbo].SiteGet
	@CompanyCode NVARCHAR(4),
	@SiteCode NVARCHAR(20)
AS
	SELECT *
	FROM Site s
	WHERE 
		s.SiteCode = @SiteCode
		AND (s.CompanyCode = @CompanyCode OR @CompanyCode IS NULL)

GO


--*******************
DROP PROCEDURE IF EXISTS GetSecretData
GO
CREATE PROCEDURE [dbo].GetSecretData
	@CompanyCode NVARCHAR(4),
	@SiteCode NVARCHAR(20)
AS
	SELECT ShopId, SecretKey
	FROM Site s
	WHERE 
		s.SiteCode = @SiteCode

GO

DROP PROCEDURE IF EXISTS GetSiteDetails
	GO
CREATE PROCEDURE [dbo].GetSiteDetails
    @sitecode NVARCHAR(50) = NULL,
	@companyCode NVARCHAR(50) = NULL
AS
SELECT s.Id, s.Address, s.Contact, s.SiteImage,swd.Id, swd.Day, swd.StartTime, swd.EndTime,ss.Id ,ss.ServiceName,ss.Image, ss.Color, ss.ServiceTypeId
FROM Site s INNER JOIN
     SiteWorkingDay swd ON s.SiteCode=swd.SiteCode INNER JOIN
     SiteServices sss ON s.Id=sss.SiteId INNER JOIN
     SiteService ss ON sss.SiteServiceId=ss.Id
WHERE s.SiteCode=@sitecode
GO

DROP PROCEDURE IF EXISTS SiteGetAll
    GO
CREATE PROCEDURE [dbo].SiteGetAll
AS
SELECT s.CompanyCode, s.SiteCode, S.SiteName, s.GpsLat, s.GpsLon
FROM Site s
GO

CREATE OR ALTER PROCEDURE [dbo].[ApplicationUserRetrieveFcmTokens]
@cards NVARCHAR(MAX)
AS
BEGIN
CREATE TABLE #TempTable (CardNumber NVARCHAR(MAX));

-- Ubacivanje razdvojenih vrednosti iz @cards u privremenu tabelu
    INSERT INTO #TempTable (CardNumber)
    SELECT value
    FROM STRING_SPLIT(@cards, ',');
    
    DECLARE @MergedString NVARCHAR(MAX);

		-- Spajanje pronađenih tokena nazad u string sa zarezima
    SELECT @MergedString = COALESCE(@MergedString + ',', '') + FcmToken
    FROM ApplicationUser
    WHERE CardNumber IN (SELECT CardNumber FROM #TempTable);

    -- Prikazivanje rezultata
    SELECT @MergedString AS MergedString;

    -- Brisanje privremene tabele
    DROP TABLE #TempTable;
    END
GO

CREATE OR ALTER PROCEDURE MarketingPromotionSaveOrUpdate
    @Id int = null,
    @Naslov NVARCHAR(255) = null,
    @Podnaslov NVARCHAR(255) = null,
    @Tekst NVARCHAR(MAX) = null,
    @Slika NVARCHAR(MAX) = null,
    @Pdf NVARCHAR(MAX) = null,
    @DatumKreiranja DATETIME = null,
    @DatumAzuriranja DATETIME = null,
    @Korisnik NVARCHAR(255) = null,
    @PoslataNotifikacija BIT = null,
    @TekstNotifikacije NVARCHAR(MAX) = null,
    @DatumOd DATETIME = null,
    @DatumDo DATETIME = null,
    @Prioritet INT = null,
    @TipPromocije NVARCHAR(20) = null,
    @BirthDayPromotion BIT = null,
    @Kupon bit = null,
    @Pravilo_id INT = null,
    @Promocija bit = null,
    @Benzinska_stanica NVARCHAR(255) = null,
    @Banner bit = null
    AS
BEGIN
	IF EXISTS(SELECT 1 FROM tMobMarketing WHERE ID = @Id)
    BEGIN
        UPDATE tMobMarketing
        SET Naslov = @Naslov, Podnaslov = @Podnaslov, Tekst=@Tekst, Pdf = @Pdf, DatumKreiranja = GETDATE(), DatumAzuriranja = GETDATE(),
            PoslataNotifikacija=0, TekstNotifikacije=@TekstNotifikacije, DatumOd=FORMAT(@DatumOd, 'yyyy-MM-dd'),
            DatumDo=FORMAT(@DatumDo, 'yyyy-MM-dd'),Prioritet = @Prioritet, TipPromocije=@TipPromocije, BirthDayPromotion=@BirthDayPromotion,
            Kupon=@Kupon,Pravilo_id = case when isnull(@Pravilo_id,0)=0 then null else @Pravilo_id end, Benzinska_stanica=@Benzinska_stanica,
            Promocija=@Promocija,Banner=@Banner
        WHERE ID = @Id

        SELECT 1
    END
ELSE
    BEGIN
        INSERT INTO tMobMarketing (Id, Naslov, Podnaslov, Tekst, Slika, Pdf, DatumKreiranja, DatumAzuriranja, Korisnik, PoslataNotifikacija,
                                   TekstNotifikacije, DatumOd, DatumDo, Prioritet, TipPromocije, BirthDayPromotion, Kupon, Pravilo_id, Promocija, Benzinska_stanica, Banner)
        VALUES (@Id, @Naslov, @Podnaslov, @Tekst, @Slika, @Pdf, @DatumKreiranja, @DatumAzuriranja, @Korisnik, @PoslataNotifikacija,
                @TekstNotifikacije, @DatumOd, @DatumDo, @Prioritet, @TipPromocije, @BirthDayPromotion, @Kupon, @Pravilo_id, @Promocija, @Benzinska_stanica, @Banner)
        
        SELECT 1
    END
END
GO
--***********************