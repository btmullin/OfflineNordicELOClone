import mysql.connector
from datetime import date
from datetime import time
from datetime import datetime

# constants
DEFAULT_SCORE = 400.0
FACTOR = 800.0

def dbquery(query):

    success = False
    while not success:

        try:
            mydb = mysql.connector.connect(
              host="www.nordicraceanalysis.com",
              user="db_btmullin",
              passwd="mysql1sCool!",
              database="nrat_db"
            )

            mycursor = mydb.cursor()

            mycursor.execute(query)
            
            result = True
            if mycursor.with_rows:
                result = mycursor.fetchall()
        
            success = True

            mycursor.close()
            mydb.close()

        except mysql.connector.Error as err:
            print "Dealing with {}".format(err)
            
    
    return result


def getcurrentpoints(racer_id, current_date):
    # TODO - query for scores within 12 months of date
    # score is average of best five or
    # avg 4*1.1, avg 3*1.2, avg 2*1.3, avg 1*1.4
    #query = "SELECT EventID, EventDate, Points FROM NRATPoints, Event WHERE NRATPoints.EventID=Event.EventID AND Event.EventDate
    start_date = datetime.strptime(current_date, '%Y-%m-%d')
    start_date.replace(year=start_date.year-1)
    start_date_str = datetime.strftime(start_date, '%Y-%m-%d')
    print start_date_str + current_date
            
    return DEFAULT_SCORE


        # get all of the latest nrat points for anyone in the race
#        latest_scores_query = """SELECT OuterRacer.RacerID,
#								(SELECT Score
#									FROM EloScore, Event 
#									WHERE EloScore.RacerID=OuterRacer.RacerID AND 
#										Event.EventID=EloScore.EventID
#									ORDER BY Event.EventDate DESC LIMIT 1) as \"EScore\"
#							FROM EloScore, Racer as OuterRacer
#							WHERE EloScore.RacerID=OuterRacer.RacerID
#							GROUP BY OuterRacer.RacerID ORDER BY "EScore" DESC"""
#        latest_scores = dbquery(latest_scores_query)
        


if __name__== "__main__":

    # get a list of racers
    # initialize their score
    
    # drop the table of scores if it exists
    dbquery("DROP TABLE IF EXISTS NRATPoints")
    
    # create the table of scores again now empty
    dbquery("""CREATE TABLE NRATPoints (NRATPointID int AUTO_INCREMENT PRIMARY KEY,
                                    RacerID int NOT NULL,
                                    EventID int NOT NULL,
                                    Points float NOT NULL)""")
    dbquery("CREATE INDEX RacerIndex ON NRATPoints (RacerID)")
    dbquery("CREATE INDEX EventIndex ON NRATPoints (EventID)")
    dbquery("CREATE INDEX EventRacerIndex ON NRATPoints (EventID, RacerID)")
    
    # get a list of races
    
    #ALL RACES
    races = dbquery("SELECT EventID, EventDate FROM Event ORDER BY EventDate ASC")
    
    #ONLY ELM CREEK RACES
    #races = dbquery('SELECT EventID, EventDate FROM Event WHERE Name LIKE "%Elm%" and Technique=1 ORDER BY EventDate ASC')
    
    #ONLY RACES IN '19/'20 SEASON
    #races = dbquery('SELECT EventID, EventDate FROM Event WHERE EventDate>"2019-06-01" ORDER BY EventDate ASC')
    
    #ONLY RACES IN SINCE '18/'19 SEASON
    #races = dbquery('SELECT EventID, EventDate FROM Event WHERE EventDate>"2018-06-01" ORDER BY EventDate ASC')

    # for each race
    count = 0
    for race in races:
        count += 1
        # get the results for the race
        race_id = race[0]
        race_query = "SELECT RacerID, TimeInSec From Result WHERE EventID={} ORDER BY TimeInSec ASC".format(race_id)
        racers = dbquery(race_query)
        race_name_query = "SELECT FullName FROM EventView WHERE EventID={}".format(race_id)
        race_name = dbquery(race_name_query)
        print "Race {} of {} : {} - {}".format(count, len(races),race_id,race_name[0][0])
        
        # calculate the race penalty
        race_penalty = 0
        if ((race_name[0][0].find("Birkie") != -1) and (race_name[0][0].find("Pre") == -1)):
            race_penalty = 0
        else:
            # penalty = sum best 3 scores in top 5 / 3.75
            top_five = [DEFAULT_SCORE, DEFAULT_SCORE, DEFAULT_SCORE, DEFAULT_SCORE, DEFAULT_SCORE];
            for x in range(0,min(5,len(racers))):
                top_five[x] = getcurrentpoints(racers[x][0], race[1])
            top_five.sort(reverse = True)
            race_penalty = (top_five[0] + top_five[1] + top_five[2])/3.75
        
        # for each racer in the race
        # Calculate the points for each racer
        racer_new_points = list()
        for update_racer in range(len(racers)):
            racer_new_points.append(FACTOR*((float(racers[update_racer][1])/racers[0][1]) - 1)+race_penalty)

        # Save the new scores
        commit_pts_query = None
        for i in range(len(racers)):
            if commit_pts_query is None:
                commit_pts_query = "INSERT INTO NRATPoints (RacerID, EventID, Points) VALUES ({},{},{})".format(racers[i][0],race_id,racer_new_points[i])
            else:
                commit_pts_query += ",({},{},{})".format(racers[i][0],race_id,racer_new_points[i])
            if (i % 100) == 0:
                dbquery(commit_pts_query)
                commit_pts_query = None
        if not commit_pts_query is None:
            dbquery(commit_pts_query)
    print "DONE!!"