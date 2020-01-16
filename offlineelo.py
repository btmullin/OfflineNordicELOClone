import mysql.connector

# constants
DEFAULT_SCORE = 1000
K_FACTOR = 1
LOG_ODDS_DIFF = 200
MAX_SCORE_CHANGE = 200
MIN_SCORE = 100
MAX_SCORE = 3000

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


def getcurrentscore(scores, racer_id):

    for racer in scores:
        if (racer[0] == racer_id):
            return racer[1]
            
    return DEFAULT_SCORE


if __name__== "__main__":

    # get a list of racers
    # initialize their score
    
    # drop the table of scores if it exists
    dbquery("DROP TABLE IF EXISTS EloScore")
    
    # create the table of scores again now empty
    dbquery("""CREATE TABLE EloScore (EloID int AUTO_INCREMENT PRIMARY KEY,
                                    RacerID int NOT NULL,
                                    EventID int NOT NULL,
                                    Score int NOT NULL)""")
    dbquery("CREATE INDEX RacerIndex ON EloScore (RacerID)")
    dbquery("CREATE INDEX EventIndex ON EloScore (EventID)")
    dbquery("CREATE INDEX EventRacerIndex ON EloScore (EventID, RacerID)")
    
    # get a list of races
    
    #ALL RACES
    races = dbquery("SELECT EventID, EventDate FROM Event ORDER BY EventDate ASC")
    
    #ONLY ELM CREEK RACES
    #races = dbquery('SELECT * FROM Event WHERE Name LIKE "%Elm%" and Technique=1 ORDER BY EventDate ASC')
    
    #ONLY RACES IN '19/'20 SEASON
    #races = dbquery('SELECT * FROM Event WHERE EventDate>"2019-06-01" ORDER BY EventDate ASC')
    
    #ONLY RACES IN SINCE '18/'19 SEASON
    #races = dbquery('SELECT * FROM Event WHERE EventDate>"2018-06-01" ORDER BY EventDate ASC')

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
        
        # get all of the latest elo scores for anyone in the race
        racer_starting_points = list()
        racer_new_points = list()
        existing_points_count = 0
        latest_scores_query = """SELECT OuterRacer.RacerID,
								(SELECT Score
									FROM EloScore, Event 
									WHERE EloScore.RacerID=OuterRacer.RacerID AND 
										Event.EventID=EloScore.EventID
									ORDER BY Event.EventDate DESC LIMIT 1) as \"EScore\"
							FROM EloScore, Racer as OuterRacer
							WHERE EloScore.RacerID=OuterRacer.RacerID
							GROUP BY OuterRacer.RacerID ORDER BY "EScore" DESC"""
        latest_scores = dbquery(latest_scores_query)
        for racer in racers:
            rscore = getcurrentscore(latest_scores, racer[0])
            # append the score
            racer_starting_points.append(rscore)
            racer_new_points.append(rscore)
        
        # for each racer in the race
        for update_racer in range(len(racers)):
            scale_racer_score = 10 ** (float(racer_starting_points[update_racer]) / LOG_ODDS_DIFF)
            for competitor in range(len(racers)):
                if (update_racer != competitor):
                    scale_competitor_score = 10 ** (float(racer_starting_points[competitor]) / LOG_ODDS_DIFF)
                    p_win = scale_racer_score / (scale_racer_score + scale_competitor_score)
                    outcome = 1
                    if (racers[competitor][1] < racers[update_racer][1]):
                        outcome = 0
                    racer_new_points[update_racer] += K_FACTOR * (outcome - p_win)
            # cap the score change and absolute score
            if (racer_new_points[update_racer] - racer_starting_points[update_racer]) > MAX_SCORE_CHANGE:
                racer_new_points[update_racer] = racer_starting_points[update_racer] + MAX_SCORE_CHANGE
            if (racer_starting_points[update_racer] - racer_new_points[update_racer]) > MAX_SCORE_CHANGE:
                racer_new_points[update_racer] = racer_starting_points[update_racer] - MAX_SCORE_CHANGE
            if (racer_new_points[update_racer] > MAX_SCORE):
                racer_new_points[update_racer] = MAX_SCORE
            if (racer_new_points[update_racer] < MIN_SCORE):
                racer_new_points[update_racer] = MIN_SCORE
        commit_pts_query = None
        for i in range(len(racers)):
            print "i is {}".format(i)
            if commit_pts_query is None:
                commit_pts_query = "INSERT INTO EloScore (RacerID, EventID, Score) VALUES ({},{},{})".format(racers[i][0],race_id,int(racer_new_points[i]))
            else:
                commit_pts_query += ",({},{},{})".format(racers[i][0],race_id,int(racer_new_points[i]))
            if i % 10:
                print "  " + commit_pts_query
                dbquery(commit_pts_query)
                commit_pts_query = None
        if not commit_pts_query is None:
            print "  Committing the remainder of updates"
            dbquery(commit_pts_query)
    print "DONE!!"