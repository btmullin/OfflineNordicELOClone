import mysql.connector

# constants
DEFAULT_SCORE = 1000
K_FACTOR = 1
LOG_ODDS_DIFF = 200
MAX_SCORE_CHANGE = 200
MIN_SCORE = 100
MAX_SCORE = 3000

def dbquery(query):
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
    
    mycursor.close()
    mydb.close()
    
    return result



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
    
    # get a list of races
    #races = dbquery("SELECT EventID, EventDate FROM Event ORDER BY EventDate ASC")
    races = dbquery('SELECT * FROM Event WHERE Name LIKE "%Elm%" and Technique=1 ORDER BY EventDate ASC')
    # for each race
    for race in races:
        # get the results for the race
        race_id = race[0]
        race_query = "SELECT RacerID, TimeInSec From Result WHERE EventID={} ORDER BY TimeInSec ASC".format(race_id)
        print "Getting racers in RaceID:{}".format(race_id)
        racers = dbquery(race_query)
        
        # get all of the latest elo scores for anyone in the race
        print "Initializing points lists for {} racers".format(len(racers))
        racer_starting_points = list()
        racer_new_points = list()
        existing_points_count = 0
        for racer in racers:
            racer_pts_query = "SELECT Score FROM EloScore, Event WHERE RacerID={} And Event.EventID=EloScore.EventID ORDER BY Event.EventDate DESC LIMIT 1".format(racer[0])
            score = dbquery(racer_pts_query)
            if (len(score)>0):
                # append the score
                racer_starting_points.append(score[0][0])
                racer_new_points.append(score[0][0])
                existing_points_count += 1
            else:
                # set the default score
                racer_starting_points.append(DEFAULT_SCORE)
                racer_new_points.append(DEFAULT_SCORE)
        print "{} racers had existing points".format(existing_points_count)    
        
        # for each racer in the race
        for update_racer in range(len(racers)):
            scale_racer_score = 10 ** (racer_starting_points[update_racer] / LOG_ODDS_DIFF)
            for competitor in range(len(racers)):
                if (update_racer != competitor):
                    scale_competitor_score = 10 ** (racer_starting_points[competitor] / LOG_ODDS_DIFF)
                    p_win = scale_racer_score / (scale_racer_score + scale_competitor_score)
                    outcome = 1
                    if (racers[competitor][1] < racers[update_racer][1]):
                        outcome = 0
                    print outcome
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
        for i in range(len(racers)):
            print "Race: {} Racer {}: {} to {}".format(race_id,racers[i][0],racer_starting_points[i],racer_new_points[i])
            commit_pts_query = "INSERT INTO EloScore (RacerID, EventID, Score) VALUES ({},{},{})".format(racers[i][0],race_id,racer_new_points[i])
            dbquery(commit_pts_query)
    print "DONE!!"