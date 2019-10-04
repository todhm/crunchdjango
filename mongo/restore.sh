  
#!/bin/sh
mongoimport -d crunchprice -c goods_search_table --file /docker-entrypoint-initdb.d/datajson.json --jsonArray --port 27017
