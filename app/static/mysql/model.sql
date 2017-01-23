-- HoopBank model
-- Authors:
--     Orson Cheng
--     Alex Narayanan

CREATE DATABASE IF NOT EXISTS nba;
USE nba;

-- teams contains basic team information
CREATE TABLE IF NOT EXISTS teams (
	tid INT PRIMARY KEY,
    tname VARCHAR(128) NOT NULL UNIQUE
);

-- players contains basic player information
CREATE TABLE IF NOT EXISTS players (
	pid INT PRIMARY KEY,
    pname VARCHAR(128) NOT NULL,
    position VARCHAR(32) NOT NULL,
    number CHAR(2) NOT NULL
);

-- roster maps players to their current team
CREATE TABLE IF NOT EXISTS roster (
	tid INT,
    pid INT,
    PRIMARY KEY(tid, pid),
    FOREIGN KEY (tid) REFERENCES teams (tid),
    FOREIGN KEY (pid) REFERENCES players (pid)
		ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- player_stats_by_year contains a row of statistics for every season of a player's career
CREATE TABLE IF NOT EXISTS player_stats_by_year (
	pid INT,
    tid INT,
    season VARCHAR(12),
    gp INT,
    points DEC(3, 1),
    rebounds DEC(3, 1),
    assists DEC(3, 1),
    PRIMARY KEY (pid, tid, season),
    FOREIGN KEY(tid) REFERENCES teams (tid)
		ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (pid) REFERENCES players (pid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);

-- users table contains administrative credentials
CREATE TABLE IF NOT EXISTS users (
	uid INT AUTO_INCREMENT PRIMARY KEY,
    username CHAR(64) UNIQUE NOT NULL,
    password CHAR(64) NOT NULL
);

-- Insert root account information
INSERT INTO users (username, password) VALUES ('root', 'root');

-- Seed the teams table with static team information
INSERT INTO teams VALUES (1610612737, 'Atlanta Hawks'), (1610612738, 'Boston Celtics'),
(1610612751, 'Brooklyn Nets'), (1610612766, 'Charlotte Hornets'),
(1610612741, 'Chicago Bulls'), (1610612739, 'Cleveland Cavaliers'),
(1610612743, 'Denver Nuggets'), (1610612742, 'Dallas Mavericks'),
(1610612765, 'Detroit Pistons'), (1610612744, 'Golden State Warriors'), 
(1610612745, 'Houston Rockets'), (1610612754, 'Indiana Pacers'),
(1610612746, 'Los Angeles Clippers'), (1610612747, 'Los Angeles Lakers'),
(1610612763, 'Memphis Grizzlies'), (1610612748, 'Miami Heat'), 
(1610612749, 'Milwaukee Bucks'), (1610612750, 'Minnesota Timberwolves'),
(1610612740, 'New Orleans Pelicans'), (1610612752, 'New York Knicks'),
(1610612760, 'Oklahoma City Thunder'), (1610612753, 'Orlando Magic'), 
(1610612755, 'Philidelphia 76ers'), (1610612756, 'Phoenix Suns'),
(1610612757, 'Portland Trail Blazers'), (1610612758, 'Sacramento Kings'),
(1610612759, 'San Antonio Spurs'), (1610612761, 'Toronto Raptors'), 
(1610612762, 'Utah Jazz'), (1610612764, 'Washington Wizards');


-- ======================================================================================
-- Define stored procedures for the nba database application

-- PROCEDURE: get_player_info
-- returns basic information about a player
DELIMITER $$
CREATE PROCEDURE get_player_info(IN pid INT)
	BEGIN
    SELECT p.pid, p.pname, p.position, p.number, t.tid, t.tname 
    FROM players p, roster r, teams t
	WHERE p.pid = r.pid AND r.tid = t.tid AND p.pid = pid;
    END $$
DELIMITER ;

-- PROCEDURE: get_player_stats
-- returns a table of statistics for the given player id
-- each row contains aggregate statistics accumulated for a particular team
-- E.g. if a player played for 4 teams throughout his career then four rows would
-- be returned, 1 for each team
DELIMITER $$
CREATE PROCEDURE get_player_stats(IN pid INT)
	BEGIN
    SELECT stats.tid, tname, season, SUM(gp) AS gp, SUM(spoints) AS points, SUM(srebounds) AS rebounds, SUM(sassists) AS assists
	FROM (SELECT tid, season, gp, gp * points as spoints, gp * rebounds as srebounds, gp * assists as sassists
		FROM player_stats_by_year psby
		WHERE psby.pid = pid) AS stats, teams t
	WHERE stats.tid = t.tid
	GROUP BY tname
    ORDER BY season;
    END $$
DELIMITER ;

-- PROCEDURE: get_team_info
-- returns basic information about a team
DELIMITER $$
CREATE PROCEDURE get_team_info(IN tid INT)
	BEGIN
    SELECT t.tid, t.tname 
    FROM teams t 
    WHERE t.tid = tid;
    END $$
DELIMITER ;

-- PROCEDURE: get_team_roster
-- retrieve the player ids and player names associated with a particualr team
DELIMITER $$
CREATE PROCEDURE get_team_roster(IN tid INT)
	BEGIN
    SELECT p.pid, p.pname, p.position, p.number 
    FROM players p, roster r 
    WHERE p.pid = r.pid 
    AND r.tid = tid 
    ORDER BY p.pname;
    END $$
DELIMITER ;

-- PROCEDURe insert_player_info
-- insert information about a new player
DELIMITER $$
CREATE PROCEDURE insert_player_info(IN pid INT, IN pname VARCHAR(128), IN tid VARCHAR(128), 
IN position VARCHAR(32), IN number INT)
	BEGIN
    INSERT INTO players	VALUES(pid, pname, position, number);
    INSERT INTO roster VALUES(tid, pid);
    END $$
DELIMITER ;

-- PROCEDURE: insert_player_stats
-- insert a row of player statistics
-- if the specific row already exists, update the row instead
DELIMITER $$
CREATE PROCEDURE insert_player_stats(IN pid INT, IN tid INT, IN season CHAR(12), IN gp INT, 
IN pts DEC(3, 1), IN rbs DEC(3, 1), IN ast DEC(3, 1))
	BEGIN
    INSERT INTO player_stats_by_year 
    VALUES (pid, tid, season, gp, pts, rbs, ast)
    ON DUPLICATE KEY
    UPDATE gp = gp, points = pts, rebounds = rbs, assists = ast;
    END $$
DELIMITER ;

-- PROCEDURE: update_player_info
-- update the basic information and roster status on a player
DELIMITER $$
CREATE PROCEDURE update_player_info(IN pname VARCHAR(128), IN tname VARCHAR(128), IN pid INT)
	BEGIN
    UPDATE players p SET p.pname = pname WHERE p.pid = pid;
    UPDATE roster r SET r.tid = tid WHERE r.pid = pid;
    END $$
DELIMITER ;

-- PROCEDURE: delete_player_records
-- deletes all records associated with the given player
DELIMITER $$
CREATE PROCEDURE delete_player_records(IN pname VARCHAR(128))
	BEGIN
    DELETE FROM players 
    WHERE players.pname = pname;
    END $$
DELIMITER ;

-- PROCEDURE: find_player
-- finds the player id associated with the given name
DELIMITER $$
CREATE PROCEDURE find_player(IN pname VARCHAR(128))
	BEGIN
    SELECT pid 
    FROM players p
    WHERE LOWER(p.pname) = pname;
    END $$
DELIMITER ;

-- PROCEDURE: find_team
-- finds the team id associated with the given name
DELIMITER $$
CREATE PROCEDURE find_team(IN tname VARCHAR(128))
	BEGIN
    SELECT tid 
    FROM teams t
    WHERE LOWER(t.tname) = tname;
    END $$
DELIMITER ;

-- PROCEDURE: validate_login
-- validates user credentials
DELIMITER $$
CREATE PROCEDURE validate_login(IN username VARCHAR(64), IN password VARCHAR(64))
	BEGIN
    SELECT uid, username 
    FROM users u 
    WHERE u.username = username AND u.password = password;
    END $$
DELIMITER ;

-- PROCEDURE: get_user
-- retrieves information about a user given an id number
DELIMITER $$
CREATE PROCEDURE get_user(IN uid INT)
	BEGIN
    SELECT uid, username 
    FROM users u
    WHERE u.uid = uid;
    END $$
DELIMITER ;