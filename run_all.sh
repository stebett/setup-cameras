source ~/miniconda3/bin/activate;
eval conda activate setup;

stty -echoctl # hide ^C

# function called by trap
kill_recordings() {
	printf "[!] Caught SIGINT\n"
	for pid in $(cat .pids); do
		kill -SIGINT $pid
	done
	rm .pids
	exit
}

trap 'kill_recordings' SIGINT

python record.py -c configs.json -o ~/data/cam0 -f -i 0 &
PID0=$!
python record.py -c configs.json -o ~/data/cam1 -f -i 1 &
PID1=$!
python record.py -c configs.json -o ~/data/cam2 -f -i 2 &
PID2=$!
python record.py -c configs.json -o ~/data/cam3 -f -i 3 &
PID3=$!
python record.py -c configs.json -o ~/data/cam4 -f -i 4 &
PID4=$!
python -m pasquetbox.run -o ~/data/out.csv --overwrite --silent &
PID5=$!
sleep 3.;

echo -e "$PID0\n$PID1\n$PID2\n$PID3\n$PID4\n$PID5" > .pids
wait $PID0
