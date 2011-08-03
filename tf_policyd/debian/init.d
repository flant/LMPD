#!/bin/sh

### BEGIN INIT INFO
# Provides:          tf-policyd
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start policyd at boot time
# Description:       Enable stmp policy service for postfix
### END INIT INFO

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

NAME="tf_policyd"
PATH_DAEMON="/usr/sbin/"
DAEMON="$PATH_DAEMON/$NAME"
PIDF="/tmp/tf_policyd.pid"
ARGS="-d -p $PIDF"

test() {
	
}

start() {
	if [ -f "$PIDF" ]; then
		PID=$(cat $PIDF)
		if [ `ps auwx|grep $NAME|grep $PID|grep -v -c grep` = 1 ]
		then
			echo "Starting tf_policyd: TF policyd working [pid: $PID]."
			exit 0
		else
			echo "Starting tf_policyd: TF policyd not running with dirty exit. Start new."
			$DAEMON $ARGS
		fi
	else
		$DAEMON $ARGS
	fi
	if [ -f "$PIDF" ]; then
		PID=$(cat $PIDF)
		if [ `ps auwx|grep $NAME|grep $PID|grep -v -c grep` = 1 ]
		then
			echo "Starting tf_policyd: OK."
			exit 0
		else
			echo "Starting tf_policyd: FAIL."
		fi
	fi
}
stop() {
	if [ -f "$PIDF" ]; then
		PID=$(cat $PIDF)
		if [ `ps auwx|grep $NAME|grep $PID|grep -v -c grep` = 1 ]
		then
			kill -2 $PID
			echo "Stoping tf_policyd: OK."
			exit 0
		else
			echo "Stoping tf_policyd: no tf_policyd running."
		fi
	fi
}
restart() {
    stop
    sleep 2
    start
}

if [ ! -x "$DAEMON" ]
then
   echo "No $DAEMON start script"
   exit 0
fi

case "$1" in
    start)
        start
;;
    stop)
        stop
;;
    restart)
        restart
;;
    status)
        if [ -f "$PIDF" ];
        then
            PID=$(cat $PIDF)
            if [ `ps auwx|grep $NAME|grep $PID|grep -v -c grep` = 1 ]
            then
                echo "TF policyd working [pid: $PID]."
                exit 0
            fi
            echo "TF policyd not running"
            exit 3
        fi
        echo "TF policyd not running."
        exit 3
;;
    *)
        echo "Usage {start|status|stop|restart}"
        exit 1
;;
esac
exit 0
