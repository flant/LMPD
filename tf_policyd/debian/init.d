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

NAME="server.py"
PATH_DAEMON="/usr/local/share/tf-policyd"
DAEMON="$PATH_DAEMON/$NAME"
PIDF="/tmp/policyd.pid"
ARGS="-d -p $PIDF"

USER="root"

start() {
    echo -n "Starting tf-policyd: "
    cd $PATH_DAEMON
    ./$NAME $ARGS
    echo "OK"
}
stop() {
    echo -n "Stopping $NAME: "
    PID=$(cat $PIDF)
    echo $PID
    kill -2 $PID
    rm -f "$PIDF"
    echo "OK"
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
