to start broker: 
	.\mosquitto.exe -c mosquitto.conf -v
to subscribe:
	.\mosquitto_sub.exe -h 192.168.0.156 -p 1884 -u jan -P stappers -t testPubTopic -v
to publish:
	.\mosquitto_pub.exe -h 192.168.0.156 -p 1884 -t player -u jan -P stappers -m giggleC_00AA11BB22A6I_45H_aliveS_26HI_23SH_43T_3032G_

to start docker container
    docker run -it -p 1883:1883 -p 9001:9001 -v mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto
