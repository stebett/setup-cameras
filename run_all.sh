source ~/miniconda3/bin/activate;
eval conda activate setup;

stty -echoctl # hide ^C

# function called by trap
kill_recordings() {
	printf "\rSIGINT caught\n"
	kill -SIGINT $PID0
	kill -SIGINT $PID1
	kill -SIGINT $PID2
	kill -SIGINT $PID3
	kill -SIGINT $PID4
	exit
}


trap 'kill_recordings' SIGINT

python record.py -c configs.json -o ~/data/cam1 -f -i 0 &
PID0=$!
python record.py -c configs.json -o ~/data/cam2 -f -i 1 &
PID1=$!
python record.py -c configs.json -o ~/data/cam3 -f -i 2 &
PID2=$!
python record.py -c configs.json -o ~/data/cam4 -f -i 3 &
PID4=$!
python record.py -c configs.json -o ~/data/cam5 -f -i 4 &
PID5=$!
