import mysql.connector

mydb = mysql.connector.connect(
  host="www.nordicraceanalysis.com",
  user="db_btmullin",
  passwd="mysql1sCool!"
  database="nrat_db"
)

mycursor = mydb.cursor()

# 