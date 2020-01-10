import mysql.connector

# constants

def dbquery(query):
    mydb = mysql.connector.connect(
      host="www.nordicraceanalysis.com",
      user="db_btmullin",
      passwd="mysql1sCool!",
      database="nrat_db"
    )

    mycursor = mydb.cursor()

    mycursor.execute(query)
    
    if mycursor.with_rows:
        return mycursor.fetchall()

    return true



if __name__== "__main__":

    # get a list of racers
    # initialize their score
    
    # drop the table of scores if it exists
    dbquery("DROP TABLE IF EXISTS EloScore")
    
    # create the table of scores again now empty
    dbquery("""CREATE TABLE EloScore (EloID int AUTO_INCREMENT,
                                    int RacerID NOT NULL,
                                    int EventID NOT NULL,
                                    PRIMARY KEY(EloID)""")
    
    # get a list of races
    # for each racer
        # for each racer in the race
            # compare them to all other racers to get an updated score
        # udpate all racers scores from the race
    print("Hello World")