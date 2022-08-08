to start broker: 
	.\mosquitto.exe -c mosquitto.conf -v
to subscribe:
	.\mosquitto_sub.exe -h 192.168.0.156 -p 1884 -u jan -P stappers -t testPubTopic -v
to publish:
	.\mosquitto_pub.exe -h 192.168.0.156 -p 1884 -t player -u jan -P stappers -m giggleC_00AA11BB22A6I_45H_aliveS_26HI_23SH_43T_3032G_