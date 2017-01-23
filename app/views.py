import requests
from nba_py import player, team
import nba_py.constants
from flask import render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required
from app import app, forms, models, database, login_manager
import sys

db = database.Database()

# The user_load required by flask-login
@login_manager.user_loader
def load_user(user_id):
	user_info = db.get_user(int(user_id))
	if (user_info):
		return models.User(user_info[0], user_info[1])
	return None

# Render the page specified by [render]
# Also handle any submitted user queries
def renderPage(form, render):
	if (form.validate_on_submit()):
		# Check for valid database response
		response = db.process_user_query(form.query.data)	
		if (not response):
			flash('Your search %s did not match any players or teams!' % form.query.data)
			return render()
		# Handle team query
		elif (response[0] == "team"):
			response_team_id = response[1]
			return redirect(url_for("showTeam", team_name=form.query.data.replace(" ", ""), team_id=response_team_id))
		# Handle player query
		else:
			response_player_id = response[1]
			return redirect(url_for("showPlayer", player_name=form.query.data.replace(" ", ""), player_id=response_player_id))
	# Render the regular page
	return render()

# Index main page
@app.route("/index", methods=['GET', 'POST'])
def index():
	query_form = forms.QueryForm()	
	render_index = lambda: render_template("index.html", form=query_form)
	return renderPage(query_form, render_index);

# The user login page
@app.route("/login", methods=['GET', 'POST'])
def login():
	login_form = forms.LoginForm()
	if (login_form.validate_on_submit()):
		user_info = db.validate_login(login_form.username.data, login_form.password.data)
		if (user_info):
			login_user(models.User(user_info[0], user_info[1]))
			return redirect(url_for("admin"))
	return render_template("login.html", login_form=login_form)

# Logout a user and redirect to index
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# Admin page for creating, updating, and deleting records
@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
	add_form = forms.AddForm()
	update_form = forms.UpdateForm()
	delete_form = forms.DeleteForm()

	# Process player additions
	if (add_form.validate_on_submit()):
		player_to_add = add_form.add.data
		addition = db.add_player_records(player_to_add)
		if addition:
			flash('Succesfully added %s to database' % (player_to_add))
		else:
			flash('Could not add player %s' % (player_to_add))

	# Process player updates
	if (update_form.validate_on_submit()):
		player_to_update = update_form.update.data
		update = db.update_player_records(player_to_update)
		if update:
			flash('Succesfully updated %s in database' % (player_to_update))
		else:
			flash('Could not update %s in database' % (player_to_update))

	# Process player deletions
	if (delete_form.validate_on_submit()):
		deletion = db.delete_player_records(delete_form.delete.data)
		player_to_delete = delete_form.delete.data
		if deletion:
			flash('Succesfully deleted %s from database' % (player_to_delete))
		else:
			flash('Could not delete %s from database' % (player_to_delete))
	return render_template("admin.html", add_form=add_form, update_form=update_form, delete_form=delete_form)

# Render a specific team
@app.route("/team/<int:team_id>/<string:team_name>", methods=['GET', 'POST'])
def showTeam(team_name, team_id):
	query_form = forms.QueryForm()
	query_records = db.retrieve_team_records(team_id)
	tean_id = query_records[0]
	team_name = query_records[1]
	team_roster = query_records[2]

	render_team = lambda: render_template("team.html", form=query_form, 
		team_name=team_name, roster=team_roster)
	return renderPage(query_form, render_team)

# Render a specific player
@app.route("/player/<int:player_id>/<string:player_name>", methods=['GET', 'POST'])
def showPlayer(player_name, player_id):
	query_form = forms.QueryForm()
	query_records = db.retrieve_player_records(player_id)
	player_info = query_records[0]
	career_statistics = query_records[1]
	statistics_by_team = query_records[2]

	render_player = lambda: render_template("player.html", form=query_form, 
		player_info=player_info, career_statistics=career_statistics, statistics_by_team=statistics_by_team)
	return renderPage(query_form, render_player)


