import sys
import mysql.connector
import MySQLdb
from datetime import date
from datetime import time
from datetime import datetime

# constants
DEFAULT_SCORE = 400.0
FACTOR = 1200.0
PENALTY_TOP_RESULTS = 2
PENALTY_TOP_SCORES_FACTOR = 3
POINTS_RACE_COUNT = 3



def dbquery(query):

    success = False
    while not success:

        try:
            mydb = mysql.connector.connect(
            #mydb = MySQLdb.connect(
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


def getcurrentpoints(racer_id, points):
    if racer_id in points:
        return points[racer_id]
    else:   
        return DEFAULT_SCORE

        
def getracestartingpoints(current_date):
    # score is average of best POINTS_RACE_COUNT or
    # 10% greater for every race less than POINTS_RACE_COUNT
    start_date = current_date.replace(year=current_date.year-1)
    start_date_str = datetime.strftime(start_date, '%Y-%m-%d')
    current_date_str = datetime.strftime(current_date, '%Y-%m-%d')
    query = "SELECT RacerID, avg(RacePoints) as \'Average\', count(RacePoints) as \'Count\', rank FROM (SELECT * FROM (SELECT NRATPoints.*, @racer_rank := IF(@racer_id = RacerID, @racer_rank+1, 1) AS Rank, @racer_id := RacerID FROM NRATPoints, Event WHERE Event.EventID=NRATPoints.EventID AND Event.EventDate >= \'{}\' AND Event.EventDate < \'{}\' ORDER BY RacerID, RacePoints ASC) ranked_points WHERE rank <= {}) filtered GROUP BY RacerID HAVING rank <= 3".format(start_date_str,current_date_str,POINTS_RACE_COUNT)
    point_scores = dbquery(query)
    points = dict()
    quit = False
    for i in range(len(point_scores)):
        if point_scores[i][2] > 0:
            points[point_scores[i][0]] = point_scores[i][1]*(1+(POINTS_RACE_COUNT-point_scores[i][2])/10.0)
        else:
            points[point_scores[i][0]] = DEFAULT_SCORE
        if point_scores[i][2] >= 3:
            print "WTH - counter bigger than three! rid: {} count: {} avg: {} score: {}".format(point_scores[i][0],point_scores[i][2],point_scores[i][1], points[point_scores[i][0]])
            quit = True
    if quit:
        print query
        exit()
    return points
    


if __name__== "__main__":

    # get a list of racers
    # initialize their score
    
    # drop the table of scores if it exists
    dbquery("DROP TABLE IF EXISTS NRATPoints")
    
    # create the table of scores again now empty
    dbquery("""CREATE TABLE NRATPoints (NRATPointID int AUTO_INCREMENT PRIMARY KEY,
                                    RacerID int NOT NULL,
                                    EventID int NOT NULL,
                                    RacePoints float NOT NULL,
                                    StartingPoints float NOT NULL,
                                    EndingPoints float NOT NULL)""")
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
        
        # Get the starting points
        starting_points = getracestartingpoints(race[1])
        
        # calculate the race penalty
        race_penalty = 0
        if ((race_name[0][0].find("Birkie") != -1) and (race_name[0][0].find("Pre") == -1)):
            race_penalty = 0
            print "Race Penalty: 0"
        else:
            # penalty = sum best PENALTY_TOP_RESULTS scores in top 5 / PENALTY_TOP_SCORES_FACTOR
            top_five = [DEFAULT_SCORE, DEFAULT_SCORE, DEFAULT_SCORE, DEFAULT_SCORE, DEFAULT_SCORE];
            for x in range(0,min(5,len(racers))):
                top_five[x] = getcurrentpoints(racers[x][0],starting_points)
            top_five.sort()
            race_penalty = 0
            for i in range(PENALTY_TOP_RESULTS):
                race_penalty += top_five[i]
            race_penalty /= PENALTY_TOP_SCORES_FACTOR
            print "Race Penalty: {}, {}, {}, {}, {}: {}".format(top_five[0],top_five[1],top_five[2],top_five[3],top_five[4],race_penalty)
        
        # for each racer in the race
        # Calculate the points for each racer
        racer_race_points = list()
        racer_starting_points = list()
        racer_ending_points = list()
        for update_racer in range(len(racers)):
            racer_race_points.append(FACTOR*((float(racers[update_racer][1])/racers[0][1]) - 1)+race_penalty)
            racer_starting_points.append(getcurrentpoints(racers[update_racer][0], starting_points))

        # Save the new scores
        commit_pts_query = None
        for i in range(len(racers)):
        # TODO - add the ending score
            if commit_pts_query is None:
                commit_pts_query = "INSERT INTO NRATPoints (RacerID, EventID, RacePoints, StartingPoints, EndingPoints) VALUES ({},{},{},{},{})".format(racers[i][0],race_id,racer_race_points[i],racer_starting_points[i],0.0)
            else:
                commit_pts_query += ",({},{},{},{},{})".format(racers[i][0],race_id,racer_race_points[i],racer_starting_points[i],0.0)
            if (i % 100) == 0:
                dbquery(commit_pts_query)
                commit_pts_query = None
        if not commit_pts_query is None:
            dbquery(commit_pts_query)
    print "DONE!!"