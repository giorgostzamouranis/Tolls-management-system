se2413 login --username user1 --passw 12345
se2413 healthcheck
se2413 resetpasses
se2413 resetstations
se2413 admin --addpasses --source passes13.csv
se2413 healthcheck
se2413 tollstationpasses --station AM08 --from 20220131 --to 20220214 --format json
se2413 passanalysis --stationop AM --tagop NAO --from 20220131 --to 20220214 --format json
se2413 passescost --stationop AM --tagop NAO --from 20220131 --to 20220214 --format json
se2413 chargesby --opid NAO --from 20220131 --to 20220214 --format json
se2413 logout
exit


