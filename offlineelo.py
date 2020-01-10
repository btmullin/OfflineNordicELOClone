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
    
    return mycursor
    



if __name__== "__main__":

    # get a list of racers
    # initialize their score
    
    # get a list of races
    # for each racer
        # for each racer in the race
            # compare them to all other racers to get an updated score
        # udpate all racers scores from the race
    