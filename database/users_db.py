DROP TABLE IF EXISTS `identity`;
CREATE TABLE `identity` (`identity_id` CHAR(64) NOT NULL PRIMARY KEY COMMENT 'id of a human being, known here as identity.',
  `username` VARCHAR(50) NULL COMMENT 'A unique string used to login.',
  `password_hash` CHAR(60) NULL COMMENT 'BCrypt hash of the password.',
  `first_name` VARCHAR(50) NULL COMMENT 'The given name of the human being.',
  `last_name` VARCHAR(50) NULL COMMENT 'The surname or family name of the human being.',
  `email` VARCHAR(50) NULL COMMENT 'The email address of the human being.',
  `phone_number` VARCHAR(50) NULL COMMENT 'The telephone number of the human being.',
  `birth_date` DATE NULL COMMENT 'The date the human being was born.',
  `gender` CHAR(1) NULL COMMENT 'The sex the human being - can be non-binary.',
  `invite_code` VARCHAR(50) NULL COMMENT 'The sex the human being - can be non-binary.',
  `admin` BOOL NOT NULL DEFAULT 0 COMMENT 'A flag to indicate this identity has rights to modify other identitites and request access to other identities.',
  `totp_secret` CHAR(16) NULL COMMENT 'Secret key for multi-factor authentication - https://tools.ietf.org/html/rfc6238.',
  `totp_enabled` BOOL NOT NULL DEFAULT 0 COMMENT 'A flag indicating if multi-factor should be enforced. A `totp_secret` could be set but not yet verified.',
  `temp_password_hash` CHAR(60) NULL COMMENT 'BCrypt hash of the temporary access password.',
  `temp_password_expire` TIMESTAMP NULL COMMENT 'Expiration date of the temporary access password.',
  `reset_token` CHAR(64) NULL COMMENT 'Token for password reset - populated when a reset is requested.',
  `reset_token_expire` TIMESTAMP NULL COMMENT 'Expiration date of the password reset token.',
  `last_auth_attempt` TIMESTAMP NULL COMMENT 'The date/time when the last unsuccessful authentication attempt was made for this identity.',
  `auth_attempt_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'The number of times an unsuccessful authentication attempt was made for this identity.',
  `locked` BOOL NOT NULL DEFAULT 0 COMMENT 'A flag preventing successful authentication to the identity even when proper credentials are provided. Currently only gets manually set.',
  `inserted` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY(`username`),
  UNIQUE KEY(`reset_token`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

DROP TABLE IF EXISTS `device`;
CREATE TABLE `device` (`device_id` VARCHAR(100) NOT NULL PRIMARY KEY COMMENT "id of device being used by identity. Provided by device manufacturer",
  `identity_id` CHAR(64) NOT NULL COMMENT 'The identity associated with this device.',
  `push_token` VARCHAR(100) NOT NULL COMMENT 'token used for sending pushes to device.',
  `os` TINYINT NOT NULL COMMENT 'Device OS - iOS, Android, etc.',
  `inserted` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY(`push_token`),
  CONSTRAINT FOREIGN KEY(`identity_id`) REFERENCES `identity` (`identity_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

DROP TABLE IF EXISTS `session`;
CREATE TABLE `session` (`session_id` CHAR(64) NOT NULL COMMENT 'An random number used to identify the user with each API call.',
  `identity_id` CHAR(64) NOT NULL COMMENT 'Identity associated with the session.',
  `active` BOOL NOT NULL DEFAULT 0 COMMENT 'Whether the session is allowed to be used. Used when an identity has multiple challenges and not all have been met yet.',
  `expires` TIMESTAMP NULL COMMENT 'Some sessions expire. This is the date that happens. NULL is an indefinite session.',
  `inserted` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY(`session_id`, `identity_id`),
  INDEX(`identity_id`),
  CONSTRAINT FOREIGN KEY(`identity_id`) REFERENCES `identity` (`identity_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (`role_id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'A scope of permissions an identity is allowed to access.',
  `name` VARCHAR(20) NOT NULL COMMENT 'A user-facing string to identify role.',
  `inserted` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY(`name`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

DROP TABLE IF EXISTS `identity_role`;
CREATE TABLE `identity_role` (`identity_id` CHAR(64) NOT NULL COMMENT 'Identity to join with role.',
  `role_id` INT UNSIGNED NOT NULL COMMENT 'Role to join with identity.',
  `account_id` CHAR(64) NOT NULL COMMENT 'The account an identity is allowed to access with specified role. All zeros means any account.',
  `inserted` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY(`identity_id`, `account_id`, `role_id`),
  CONSTRAINT FOREIGN KEY(`identity_id`) REFERENCES `identity` (`identity_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT FOREIGN KEY(`role_id`) REFERENCES `role` (`role_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `create_identity` (
  IN in_identity_id CHAR(64),
  IN in_username VARCHAR(50),
  IN in_password_hash CHAR(60)
)
BEGIN

CALL abort_if_identity_username_exists(in_username);

INSERT INTO
  `identity`
  (`identity_id`, `username`, `password_hash`)
VALUES
  (in_identity_id, in_username, in_password_hash);

CALL fetch_identity(in_identity_id);

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `fetch_identity` (
  IN in_identity_id CHAR(64)
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);

SELECT
  `first_name`,
  `last_name`,
  `gender`,
  `invite_code`
FROM
  `identity`
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity` (
  IN in_identity_id CHAR(64),
  IN in_username VARCHAR(50),
  IN in_first_name VARCHAR(50),
  IN in_last_name VARCHAR(50),
  IN in_email VARCHAR(50),
  IN in_phone_number VARCHAR(50),
  IN in_birth_date DATE,
  IN in_gender CHAR(1),
  IN in_invite_code VARCHAR(50),
  IN in_password_hash CHAR(60)
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);

UPDATE
  `identity`
SET
  `username` = COALESCE(in_username, `username`),
  `first_name` = COALESCE(in_first_name, `first_name`),
  `last_name` = COALESCE(in_last_name, `last_name`),
  `email` = COALESCE(in_email, `email`),
  `phone_number` = COALESCE(in_phone_number, `phone_number`),
  `birth_date` = COALESCE(in_birth_date, `birth_date`),
  `gender` = COALESCE(in_gender, `gender`),
  `invite_code` = COALESCE(in_invite_code, `invite_code`),
  `password_hash` = COALESCE(in_password_hash, `password_hash`)
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

-- If we're changing the password, we should expire all
-- the existing sessions that were created with the
-- previous password.
IF in_password_hash IS NOT NULL THEN
  CALL delete_sessions_for_identity(in_identity_id);
END IF;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_totp_secret` (
  IN in_identity_id CHAR(64),
  IN in_totp_secret CHAR(16)
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);

UPDATE
  `identity`
SET
  `totp_secret` = COALESCE(in_totp_secret, `totp_secret`),
  `totp_enabled` = 0
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_enable_totp` (
  IN in_identity_id CHAR(64),
  IN in_enabled BOOL
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);

UPDATE
  `identity`
SET
  `totp_enabled` = in_enabled
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_request_reset` (
  IN in_username VARCHAR(50),
  IN in_reset_token CHAR(64)
)
BEGIN

CALL abort_if_identity_username_no_exists(in_username);
CALL abort_if_username_is_admin(in_username);

UPDATE
  `identity`
SET
  `reset_token` = in_reset_token,
  `reset_token_expire` = DATE_ADD(NOW(), INTERVAL 1 HOUR)
WHERE
  `username` = in_username
LIMIT 1;

SELECT
  `email`
FROM
  `identity`
WHERE
  `username` = in_username
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_redeem_reset` (
  IN in_reset_token CHAR(64),
  IN in_password_hash CHAR(60)
)
BEGIN

DECLARE token_expires TIMESTAMP;
DECLARE token_valid BOOL;

SET token_valid = FALSE;

SELECT
  `reset_token_expire` INTO token_expires
FROM
  `identity`
WHERE
  `reset_token` = in_reset_token
LIMIT 1;

IF token_expires IS NULL THEN - - reset_token does not exist.
  SIGNAL SQLSTATE '45000' - - 45000 is a user - generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'reset_token', MYSQL_ERRNO = 10001;
ELSEIF CURRENT_TIMESTAMP < token_expires THEN
  SET token_valid = TRUE; -- timestamp is valid.
END IF;

IF token_valid = TRUE THEN
  UPDATE
    `identity`
  SET
    `password_hash` = in_password_hash
  WHERE
    `reset_token` = in_reset_token
  LIMIT 1;
END IF;

UPDATE
  `identity`
SET
  `reset_token` = NULL,
  `reset_token_expire` = NULL
WHERE
  `reset_token` = in_reset_token
LIMIT 1;

COMMIT; -- Want to do this because we want the above UPDATE to update
        -- even if exception is thrown.

IF token_valid = FALSE THEN
  SIGNAL SQLSTATE '45000' - - 45000 is a user - generic number.
  -- Throw exception using code 10003 which is zapi defined as
  -- 'expired'
  -- We pass the key name so app can handle it appropriately.
  SET MESSAGE_TEXT = 'reset_token', MYSQL_ERRNO = 10003;
END IF;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_password_hash` (
  IN in_identity_id CHAR(64),
  IN in_password_hash CHAR(60)
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);

UPDATE
  `identity`
SET
  `password_hash` = in_password_hash
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_temp_password_hash` (
  IN in_identity_id CHAR(64),
  IN in_password_hash CHAR(60)
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);
CALL abort_if_identity_is_admin(in_identity_id);

UPDATE
  `identity`
SET
  `temp_password_hash` = in_password_hash,
  `temp_password_expire` = DATE_ADD(NOW(), INTERVAL 10 MINUTE)
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `delete_sessions_for_identity` (
  IN in_identity_id CHAR(64)
)
BEGIN

CALL check_if_identity_id_exists(in_identity_id);

DELETE FROM
  `session`
WHERE
  `identity_id` = identity_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `create_session` (
  IN in_session_id CHAR(64),
  IN in_identity_id CHAR(64),
  IN in_expires TIMESTAMP
)
BEGIN

INSERT INTO
  `session`
  (`session_id`, `identity_id`, `expires`)
VALUES
  (in_session_id, in_identity_id, in_expires);

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `delete_session` (
  IN in_session_id CHAR(64)
)
BEGIN

CALL check_if_session_is_valid(in_session_id);

DELETE FROM
  `session`
WHERE
  `session_id` = in_session_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_session` (
  IN in_session_id CHAR(64),
  IN in_active BOOL
)
BEGIN

CALL check_if_session_is_valid(in_session_id);

UPDATE
  `session`
SET
  `active` = in_active
WHERE
  `session_id` = in_session_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `create_role` (
  IN in_name VARCHAR(20)
)
BEGIN

CALL abort_if_role_name_exists(in_name);

INSERT INTO
  `role`
  (`name`)
VALUES
  (in_name);

CALL fetch_role(LAST_INSERT_ID());

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `delete_role` (
  IN in_role_id INT UNSIGNED
)
BEGIN

CALL check_if_role_exists(in_role_id);

DELETE FROM
  `role`
WHERE
  `role_id` = in_role_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_role` (
  IN in_role_id INT UNSIGNED,
  IN in_name VARCHAR(20)
)
BEGIN

CALL check_if_role_exists(in_role_id);

UPDATE
  `role`
SET
  `name` = in_name
WHERE
  `role_id` = in_role_id
LIMIT 1;

CALL fetch_role(in_role_id);

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `fetch_role` (
  IN in_role_id INT UNSIGNED
)
BEGIN

CALL check_if_role_exists(in_role_id);

SELECT
  `role_id`,
  `name`
FROM
  `role`
WHERE
  `role_id` = in_role_id
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

-- This procedure exists so I don't have to rely on
-- hard - coding role id for 'user'
DELIMITER $$
CREATE PROCEDURE `role_for_user` ()
BEGIN

SELECT
  `role_id`
FROM
  `role`
WHERE
  `name` = 'user'
LIMIT 1;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `fetch_all_roles` ()
BEGIN

SELECT
  `role_id`,
  `name`
FROM
  `role`
ORDER BY `role_id`;

END$$
DELIMITER;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `add_role_to_identity` (
  IN in_identity_id CHAR(64),
  IN in_account_id CHAR(64),
  IN in_role_id INT UNSIGNED
)
BEGIN

DECLARE key_exists BOOL;

CALL check_if_identity_id_exists(in_identity_id);
CALL check_if_role_exists(in_role_id);

IF in_account_id = '0000000000000000000000000000000000000000000000000000000000000000' THEN
  SELECT
    `admin` INTO key_exists
  FROM
    `identity`
  WHERE
    `identity_id` = in_identity_id
  LIMIT 1;

  -- If the request is to add a role for account 0000...0000
  -- (which is a wildcard for all accounts), then we need to
  -- check and see if that identity is an admin. Fail if not.
  IF key_exists = FALSE THEN
      SIGNAL SQLSTATE '45000' - - 45000 is a user - generic number.
    -- Throw exception using code 10004 which is zapi defined as
    -- 'forbidden'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'identity_id', MYSQL_ERRNO = 10004;
  END IF;
END IF;

SELECT
  COUNT(*) INTO key_exists
FROM
  `identity_role`
WHERE
  `identity_id` = in_identity_id
AND
  `account_id` = in_account_id
AND
  `role_id` = in_role_id
LIMIT 1;

IF key_exists = 0 THEN
  INSERT INTO
    `identity_role`
    (`identity_id`, `account_id`, `role_id`)
  VALUES
    (in_identity_id, in_account_id, in_role_id);
END IF;

CALL fetch_identity_roles(in_identity_id);

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `fetch_identity_roles` (
  IN in_identity_id CHAR(64)
  )
BEGIN

SELECT
  `identity_role`.`account_id`,
  GROUP_CONCAT(`role`.`name` SEPARATOR ',') as `roles`
FROM
  `identity_role`, `role`
WHERE
  `identity_role`.`role_id` = `role`.`role_id`
AND
  `identity_role`.`identity_id` = in_identity_id
GROUP BY `identity_role`.`account_id`;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `fetch_identity_roles_for_account` (
  IN in_identity_id CHAR(64),
  IN in_account_id CHAR(64)
  )
BEGIN

SELECT
  GROUP_CONCAT(`role`.`name` SEPARATOR ',') as `roles`
FROM
  `identity`, `identity_role`, `role`
WHERE
  `identity_role`.`role_id` = `role`.`role_id`
AND
  `identity_role`.`identity_id` = in_identity_id
AND
  `identity`.`identity_id` = in_identity_id
AND
  -- We match here if there is an entry for this account
  (`identity_role`.`account_id` = in_account_id
    OR
  ( -- or if there is an entry for account id 000...000
    -- *and* identity is flagged as admin.
    `identity`.`admin` = 1
      AND
    `identity_role`.`account_id` = '0000000000000000000000000000000000000000000000000000000000000000'
  )
);

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `update_identity_reset_auth_count` (
  IN in_identity_id CHAR(64)
)
BEGIN

-- For now, I assume we don't care if this actually exists or not
-- This doesn't get called until user logs in successfully, so
-- we can just assume the identity exists. Calling the stored
-- procedure before doing the reset was causing count not to get
-- reset for some reason.
-- CALL check_if_identity_id_exists(in_identity_id);

UPDATE
  `identity`
SET
  `auth_attempt_count` = 0
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `identity_from_session` (
  IN in_session_id CHAR(64)
)
BEGIN

CALL check_if_session_is_valid(in_session_id);

SELECT
  `identity`.`identity_id`,
  `identity`.`username`,
  `identity`.`admin`,
  `identity`.`totp_secret`,
  `session`.`expires`
FROM
  `session`
INNER JOIN
  `identity`
ON
  `identity`.`identity_id` = `session`.`identity_id`
WHERE
  `session`.`session_id` = in_session_id
LIMIT 1;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `fetch_identity_credentials` (
  IN in_username VARCHAR(50)
  )
BEGIN

DECLARE a_identity_id CHAR(64);
DECLARE a_password_hash CHAR(60);
DECLARE a_temp_password_hash CHAR(60);
DECLARE a_temp_password_expire TIMESTAMP;
DECLARE a_last_auth_attempt TIMESTAMP;
DECLARE a_auth_attempt_count INT UNSIGNED DEFAULT 0;
DECLARE a_locked BOOL DEFAULT 0;
DECLARE a_totp_secret CHAR(16);
DECLARE a_totp_enabled BOOL DEFAULT 0;

DECLARE next_valid_auth_date TIMESTAMP;
DECLARE identity_delay_seconds INT UNSIGNED;

CALL check_if_identity_username_exists(in_username);

SELECT
  `identity_id`,
  `password_hash`,
  `temp_password_hash`,
  `temp_password_expire`,
  `last_auth_attempt`,
  `auth_attempt_count`,
  `locked`,
  `totp_secret`,
  `totp_enabled`
INTO
  a_identity_id,
  a_password_hash,
  a_temp_password_hash,
  a_temp_password_expire,
  a_last_auth_attempt,
  a_auth_attempt_count,
  a_locked,
  a_totp_secret,
  a_totp_enabled
FROM
  `identity`
WHERE
  `username` = in_username
LIMIT 1;

-- Update auth attempt counter
UPDATE
  `identity`
SET
  `auth_attempt_count` = `auth_attempt_count` + 1,
  `last_auth_attempt` = CURRENT_TIMESTAMP
WHERE
  `username` = in_username
LIMIT 1;

IF a_temp_password_expire < CURRENT_TIMESTAMP THEN
  -- Delete temp password if it's expired.
  -- It's convenient to just delete it here rather
  -- than return it and let the app's code check
  -- the expire date. We would have to make a db
  -- call anyway to delete it.
  CALL delete_identity_temp_password(in_username);
  SET a_temp_password_hash = NULL;
END IF;

-- If totp is disabled, then don't return secret.
-- This makes checking it in code easier.
IF a_totp_enabled = FALSE THEN
  SET a_totp_secret = NULL;
END IF;

-- Lock identity if timeout is not met.
-- It's debatable whether this logic belongs
-- in SQL. It's convenient to have it here, thogugh.
-- This way, all the identity lock-out logic lives in
-- this one procedure.
SET identity_delay_seconds = (a_auth_attempt_count * 2);
SET next_valid_auth_date = DATE_ADD(a_last_auth_attempt,
  INTERVAL identity_delay_seconds SECOND);
IF CURRENT_TIMESTAMP < next_valid_auth_date THEN
  SET a_locked = TRUE;
END IF;

-- The final output.
SELECT
  a_identity_id as `identity_id`,
  in_username as `username`,
  a_password_hash as `password_hash`,
  a_temp_password_hash as `temp_password_hash`,
  a_locked as `locked`,
  a_totp_secret as `totp_secret`;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `delete_identity_temp_password` (
  IN in_username VARCHAR(50)
  )
BEGIN

UPDATE
  `identity`
SET
  `temp_password_hash` = NULL,
  `temp_password_expire` = NULL
WHERE
  `username` = in_username
LIMIT 1;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `check_if_identity_id_exists` (
  IN in_identity_id CHAR(64)
  )
BEGIN

DECLARE key_exists BOOL;

-- Check if `identity_id` exists in `identity` table.
SELECT
  COUNT(*) INTO key_exists -- Item exists in `identity` if count > 0.
FROM
  `identity`
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

IF key_exists = FALSE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'identity_id', MYSQL_ERRNO = 10001;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `abort_if_role_name_exists` (
  IN in_name VARCHAR(20)
  )
BEGIN

DECLARE role_exists BOOL;

-- Check if `role` exists in `role` table.
SELECT
  COUNT(*) INTO role_exists -- Item exists in `role` if count > 0.
FROM
  `role`
WHERE
  `name` = in_name
LIMIT 1;

IF role_exists THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'role', MYSQL_ERRNO = 10002;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `check_if_role_exists` (
  IN in_role_id INT UNSIGNED
  )
BEGIN

DECLARE role_exists BOOL;

-- Check if `role` exists in `role` table.
SELECT
  COUNT(*) INTO role_exists -- Item exists in `role` if count > 0.
FROM
  `role`
WHERE
  `role_id` = in_role_id
LIMIT 1;

IF role_exists = FALSE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'role', MYSQL_ERRNO = 10001;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `check_if_identity_username_exists` (
  IN in_username VARCHAR(50)
  )
BEGIN

DECLARE username_exists BOOL;

-- Check if `username` exists in `identity` table.
SELECT
  COUNT(*) INTO username_exists -- Item exists in `identity` if count > 0.
FROM
  `identity`
WHERE
  `username` = in_username
LIMIT 1;

IF username_exists = FALSE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'username', MYSQL_ERRNO = 10001;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `abort_if_identity_username_exists` (
  IN in_username VARCHAR(50)
  )
BEGIN

DECLARE username_exists BOOL;

-- Check if `username` exists in `identity` table.
SELECT
  COUNT(*) INTO username_exists -- Item exists in `identity` if count > 0.
FROM
  `identity`
WHERE
  `username` = in_username
LIMIT 1;

IF username_exists = TRUE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'username', MYSQL_ERRNO = 10002;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `abort_if_identity_username_no_exists` (
  IN in_username VARCHAR(50)
  )
BEGIN

DECLARE username_exists BOOL;

-- Check if `username` exists in `identity` table.
SELECT
  COUNT(*) INTO username_exists -- Item exists in `identity` if count > 0.
FROM
  `identity`
WHERE
  `username` = in_username
LIMIT 1;

IF username_exists = FALSE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'username', MYSQL_ERRNO = 10001;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `check_if_session_is_valid` (
  IN in_session_id CHAR(64)
  )
BEGIN

DECLARE session_expires TIMESTAMP;

-- Check if `session_id` exists in `session` table.
SELECT
  `expires`
INTO
  session_expires -- Get expiration date.
FROM
  `session`
WHERE
  `session_id` = in_session_id
LIMIT 1;

IF session_expires IS NULL THEN -- session_id does not exist.
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10001 which is zapi defined as
    -- 'key does not exist'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'session_id', MYSQL_ERRNO = 10001;
END IF;

-- Check if session is expired. If so, delete it and
-- throw exception.
IF session_expires < CURRENT_TIMESTAMP THEN
  DELETE FROM
    `session`
  WHERE
    `session_id` = in_session_id
  LIMIT 1;

  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10003 which is zapi defined as
    -- 'expired'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'session_id', MYSQL_ERRNO = 10003;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `abort_if_identity_is_admin` (
  IN in_identity_id CHAR(64)
  )
BEGIN

DECLARE is_admin BOOL;

SELECT
  `admin` INTO is_admin
FROM
  `identity`
WHERE
  `identity_id` = in_identity_id
LIMIT 1;

-- Make sure user isn't admin. Temp passwords are not
-- allowed for admins.
IF is_admin = TRUE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10004 which is zapi defined as
    -- 'not allowed'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'identity_id', MYSQL_ERRNO = 10004;
END IF;

END$$
DELIMITER ;

-- ----------------------------------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `abort_if_username_is_admin` (
  IN in_username VARCHAR(20)
  )
BEGIN

DECLARE is_admin BOOL;

SELECT
  `admin` INTO is_admin
FROM
  `identity`
WHERE
  `username` = in_username
LIMIT 1;

-- Make sure user isn't admin. Temp passwords are not
-- allowed for admins.
IF is_admin = TRUE THEN
  SIGNAL SQLSTATE '45000' -- 45000 is a user-generic number.
    -- Throw exception using code 10004 which is zapi defined as
    -- 'not allowed'
    -- We pass the key name so app can handle it appropriately.
    SET MESSAGE_TEXT = 'username', MYSQL_ERRNO = 10004;
END IF;

END$$
DELIMITER ;
