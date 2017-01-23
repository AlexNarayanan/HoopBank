from nba_py import player, team
import MySQLdb
import sys

class Database:

	# Initialize the connection and cursor
	def __init__(self):
		try:
			# To configure name of mysql instance change 'nba' in the following line
			self.host = "localhost"
			self.user = "root"
			self.pw = "root"
			self.mysql_instance_name = "nba"
			self.db = MySQLdb.connect(self.host, self.user, self.pw, self.mysql_instance_name)
			self.cursor = self.db.cursor()

		except Exception as e:
			print("Could not connect to database \"" + self.mysql_instance_name + "\"")
			sys.exit(e)

	# Process the user-entered query
	def process_user_query(self, query):
		query = query.lower()

		# Match queries against teams
		team_id = self.validate_team_query(query)
		if (team_id):
			return team_id

		# Match queries against players, if unsucessful add new player
		player_id = self.validate_player_query(query)
		if (player_id):
			return player_id
		else:
			return self.add_player_records(query)

	# Check for existence of the given team in the database
	# Return team_id if exists, otherwise return false
	def validate_team_query(self, query):
		# Check if query exists in teams table
		try:
			self.cursor.callproc('find_team', args=[query])
			team_id = self.cursor.fetchall()
			self.cursor.nextset()
			if (team_id):
				return ("team", team_id[0][0])

		except Exception as e:
			print("Error while querying teams: " + str(e))
			return False

	# Check for existence of the given player in the database
	def validate_player_query(self, query):
		try:
			self.cursor.callproc('find_player', args=[query])
			player_id = self.cursor.fetchall()
			self.cursor.nextset()
			if (player_id):
				return ("player", player_id[0][0])

		except Exception as e:
			print("Error while querying players: " + str(e))
			return False

	# Adds new player to the db, but checks if they already exist first
	def add_player_records(self, query):
		try:
			split_query = query.split(" ")
			player_data = player.get_player(split_query[0], split_query[1], just_id=False).values[0]
			player_roster_status = player_data[3]
			if (player_roster_status):
				player_id = player_data[0]
				player_name = player_data[2]
				player_team = player_data[7]
				print("Adding new player to database!!!!")
				self.insert_new_player(player_id, player_name, player_team)
				return ("player", player_id)
			else:
				return False
		except Exception as e:
			print("Error while adding player to database: " + str(e))
			return False


	# Retrieve and aggregate player records from the database
	def retrieve_player_records(self, pid):
		try:
			self.cursor.callproc('get_player_info', args=[pid])
			player_records = self.cursor.fetchall()[0]
			self.cursor.nextset()
			self.cursor.callproc('get_player_stats', args=[pid])
			player_stats = self.cursor.fetchall()
			self.cursor.nextset()

			# Calculate player career averages
			total_points = 0
			total_rebounds = 0
			total_assists = 0
			total_games = 0
			statistics_by_team = []
			for row in player_stats:
				team_games = float(row[3])
				team_points = float(row[4])
				team_rebounds = float(row[5])
				team_assists = float(row[6])

				total_games += team_games
				total_points += team_points
				total_rebounds += team_rebounds
				total_assists += team_assists

				statistics_by_team.append(list(row[0:2]) + list(map(lambda x: round(x / team_games, 1), [team_points, team_rebounds, team_assists])))

			# Return as tuple (player_info, career_statistics, statistics_by_team)
			career_statistics = list(map(lambda x: round(x / total_games, 1), [total_points, total_rebounds, total_assists]))
			return (player_records,) + (career_statistics, statistics_by_team)

		except Exception as e:
			print("Something went wrong while fetching statistics: " + str(e))
			return False

	# Retrieve team records from the database
	def retrieve_team_records(self, tid):
		try:
			self.cursor.callproc('get_team_info', args=[tid])
			team_records = self.cursor.fetchall()[0]
			self.cursor.nextset()
			self.cursor.callproc('get_team_roster', args=[tid])
			team_roster = self.cursor.fetchall()
			self.cursor.nextset()
		except Exception as e:
			print("Something went wrong while fetching statistics: " + str(e))

		# Return as tuple (team_id, team_name, team_roster)
		return team_records + (team_roster,)

	# Insert the records for a new player into the database
	def insert_new_player(self, pid, pname, pteam):
		try:
			# Add player to players table and roster
			player_summary = player.PlayerSummary(pid).info().values[0]
			self.cursor.callproc('insert_player_info', args=[pid, pname, pteam, player_summary[14], player_summary[13]])
			self.cursor.nextset()
			
			# Then grab their statistics by year
			player_statistics = player.PlayerCareer(pid).regular_season_totals().values
			for row in player_statistics:
				team_id = row[3]
				# Filter out aggregate rows that show up if a player plays for 2 or more teams in a single season
				if (not team_id == 0):
					season = row[1]
					games_played = row[6]
					points = row[26]
					rebounds = row[20]
					assists = row[21]
					self.cursor.callproc('insert_player_stats', args=[pid, team_id, season, games_played, points, rebounds, assists])
					self.cursor.nextset()
			
			self.db.commit()
			print("Succesfully inserted player %s into the database" % pname)
		
		except Exception as e:
			print(e) 
			self.db.rollback()

	# Delete the records associated with the given player from the database
	def delete_player_records(self, player_name):
		try:
			self.cursor.callproc('delete_player_records', args=[player_name])
			self.cursor.nextset()
			self.db.commit()
			return True
		except Exception as e:
			print("Something went wrong when trying to delete player records: " + str(e))
			self.db.rollback()
			return False

	# Update the database records associated with the given player
	def update_player_records(self, player_name):
		try:
			# Fetch basic player info and update in db
			split_query = player_name.split(" ")
			player_data = player.get_player(split_query[0], split_query[1], just_id=False).values[0]
			player_id = player_data[0]
			player_name = player_data[2]
			player_team = player_data[7]
			self.cursor.callproc('update_player_info', args=[player_name, player_team, player_id])
			self.cursor.nextset()
			
			# Fetch statistics and update in db
			player_statistics = player.PlayerCareer(player_id).regular_season_totals().values
			for row in player_statistics:
				team_id = row[3]
				if (not team_id == 0):
					season = row[1]
					games_played = row[6]
					points = row[26]
					rebounds = row[20]
					assists = row[21]
					self.cursor.callproc('insert_player_stats', args=[player_id, team_id, season, games_played, points, rebounds, assists])
					self.cursor.nextset()
			self.db.commit()
			return True

		except Exception as e:
			print("Something went wrong when trying to update player records: " + str(e))
			self.db.rollback()
			return False

	# Get user information given an id number
	def get_user(self, id):
		try:
			self.cursor.callproc('get_user', args=[id])
			user_info = self.cursor.fetchall()[0]
			self.cursor.nextset()
			if (user_info):
				return user_info

		except Exception as e:
			print("Could not fetch user %s" + str(id))

		return False;

	# Validate a user login 
	def validate_login(self, username, password):
		try:
			self.cursor.callproc('validate_login', args=[username, password])
			authentication = self.cursor.fetchall()[0]
			self.cursor.nextset()			
			if (authentication):
				return authentication
				
		except Exception as e:
			print("Could not authenticate user %s" + username)
		
		return False


