se2413 logout
se2413 login --username user1 --passw 12345
se2413 healthcheck
se2413 resetpasses
se2413 healthcheck
se2413 resetstations
se2413 healthcheck
se2413 admin --addpasses --source passes13.csv
se2413 healthcheck
se2413 tollstationpasses --station AM08 --from 20220131 --to 20220214 --format json
se2413 tollstationpasses --station NAO04 --from 20220131 --to 20220214 --format csv
se2413 tollstationpasses --station NO01 --from 20220131 --to 20220214 --format csv
se2413 tollstationpasses --station OO03 --from 20220131 --to 20220214 --format csv
se2413 tollstationpasses --station XXX --from 20220131 --to 20220214 --format csv
se2413 tollstationpasses --station OO03 --from 20220131 --to 20220214 --format YYY
se2413 errorparam --station OO03 --from 20220131 --to 20220214 --format csv
se2413 tollstationpasses --station AM08 --from 20220201 --to 20220212 --format json
se2413 tollstationpasses --station NAO04 --from 20220201 --to 20220212 --format csv
se2413 tollstationpasses --station NO01 --from 20220201 --to 20220212 --format csv
se2413 tollstationpasses --station OO03 --from 20220201 --to 20220212 --format csv
se2413 tollstationpasses --station XXX --from 20220201 --to 20220212 --format csv
se2413 tollstationpasses --station OO03 --from 20220201 --to 20220212 --format YYY
se2413 passanalysis --stationop AM --tagop NAO --from 20220131 --to 20220214 --format json
se2413 passanalysis --stationop NAO --tagop AM --from 20220131 --to 20220214 --format csv
se2413 passanalysis --stationop NO --tagop OO --from 20220131 --to 20220214 --format csv
se2413 passanalysis --stationop OO --tagop KO --from 20220131 --to 20220214 --format csv
se2413 passanalysis --stationop XXX --tagop KO --from 20220131 --to 20220214 --format csv
se2413 passanalysis --stationop AM --tagop NAO --from 20220201 --to 20220212 --format json
se2413 passanalysis --stationop NAO --tagop AM --from 20220201 --to 20220212 --format csv
se2413 passanalysis --stationop NO --tagop OO --from 20220201 --to 20220212 --format csv
se2413 passanalysis --stationop OO --tagop KO --from 20220201 --to 20220212 --format csv
se2413 passanalysis --stationop XXX --tagop KO --from 20220201 --to 20220212 --format csv
se2413 passescost --stationop AM --tagop NAO --from 20220131 --to 20220214 --format json
se2413 passescost --stationop NAO --tagop AM --from 20220131 --to 20220214 --format csv
se2413 passescost --stationop NO --tagop OO --from 20220131 --to 20220214 --format csv
se2413 passescost --stationop OO --tagop KO --from 20220131 --to 20220214 --format csv
se2413 passescost --stationop XXX --tagop KO --from 20220131 --to 20220214 --format csv
se2413 passescost --stationop AM --tagop NAO --from 20220201 --to 20220212 --format json
se2413 passescost --stationop NAO --tagop AM --from 20220201 --to 20220212 --format csv
se2413 passescost --stationop NO --tagop OO --from 20220201 --to 20220212 --format csv
se2413 passescost --stationop OO --tagop KO --from 20220201 --to 20220212 --format csv
se2413 passescost --stationop XXX --tagop KO --from 20220201 --to 20220212 --format csv
se2413 chargesby --opid NAO --from 20220131 --to 20220214 --format json
se2413 chargesby --opid GE --from 20220131 --to 20220214 --format csv
se2413 chargesby --opid OO --from 20220131 --to 20220214 --format csv
se2413 chargesby --opid KO --from 20220131 --to 20220214 --format csv
se2413 chargesby --opid NO --from 20220131 --to 20220214 --format csv
se2413 chargesby --opid NAO --from 20220201 --to 20220212 --format json
se2413 chargesby --opid GE --from 20220201 --to 20220212 --format csv
se2413 chargesby --opid OO --from 20220201 --to 20220212 --format csv
se2413 chargesby --opid KO --from 20220201 --to 20220212 --format csv
se2413 chargesby --opid NO --from 20220201 --to 20220212 --format csv
se2413 logout
exit