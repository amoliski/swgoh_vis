## SWGOH Guild Visualiser

Scrapes Star Wars Galaxy of Heroes guild data and stores it in a terribly structured MySQL database. Then it digs through that site and makes some pretty charts.

Example: http://amoliski.pythonanywhere.com/swgoh/cotd

###Cron :

**update_db.py:**
Midnight and Noon
Updates the total Guild GP and the individual user GP

**update_rosters.py**
1:00 am
Updates the units/gear level/levels of half of the guild - split in half to avoid rate limits

**update_rosters2.py**
3:00 am
Updates the units/gear level/levels of the other half of the guild

### Database Setup
The tables are defined in structure.sql

### Database Connection Config:

Create a file called `db_connection` one directory up from the swgoh files

**Structure:**

     {
	 "user":"DATABASE_USERNAME", 
	 "password":"DATABASE_PASSWORD", 
	 "database":"DATABASE_NAME", 
	 "host":"DATABASE_HOST"
	 }
