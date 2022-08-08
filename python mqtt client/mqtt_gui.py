from paho.mqtt import client as mqtt_client
from tkinter import *

import threading
from dataclasses import dataclass
import datetime
import time
import random
#example string flag data: "blueC_100H_aliveS_456T_2354G"
#example string player data: "greenC_00AA11BB22CCI_100H_aliveS_14HI_58SH__456T_2354G"

#game statistics
hiding_time = 60*1
playing_time = 60*5
hit_damage = 30
hit_timeout = 5
shot_ammo = 0
practicing_channel = 2
#playing_channel = 3
invalid_channel = 15

@dataclass
class Flag:
    color: str
    health: str
    status: str
    timeOfDeath: str
    gameId: str
@dataclass
class Player:
    color: str
    playerId: str
    health: str
    status: str
    hits: str
    shots: str
    timeOfDeath: str
    gameId: str
    
currentGameId = 0

green_flag_data = Flag("green", "0%", "death", "0", "0")
red_flag_data = Flag("red", "0%", "death", "0", "0")
blue_flag_data = Flag("blue", "0%", "death", "0", "0")

player_list_data_green = []
player_list_data_red = []
player_list_data_blue = []

program_running = True

#broker details
#broker = "192.168.1.206"
broker = "192.168.0.140"
port = 1883

#mss niet nodig?
client = 0
client_id = "whatismyid"
username = "jan"
password = "stappers"
deviceId = "python_mqtt_dashboard"

#topics
topic_pub = "testPubTopic"
topic_sub = "testTopic"
topic_sub2 = "testTopic2"

topic_flag = "flag"
topic_player = "player"

topic_flag_pub_prestart = "flag_prestart"
topic_player_pub_prestart = "player_prestart"

topic_stop = "device_stop"

#subscription data
sub_data = ["sample"]



def thread_gui(name):
    print("Thread starting")
    
    global green_flag_data
    global red_flag_data
    global blue_flag_data
    
    #gui
    window = Tk()
    window.title("MQTT Blaster Dashboard")
    window.geometry('768x700')
    window.resizable(True,True)
    window.configure(bg="white")
       
    #canvas config
    c = Canvas(window, width = 768, height = 700)
    c.config(highlightthickness=0)
    #scrolbar config
    v = Scrollbar(window, orient=VERTICAL)
    v.config(command=c.yview)
    v.pack(side = RIGHT, fill = Y)

    c.config(yscrollcommand=v.set)
    #c.place(x=0,y=0)
    c.pack(side=LEFT, expand=YES, fill=BOTH)
    c.config(scrollregion=(0,0,0,2000))
    
    #frame config
    f = Frame(c, background="#ffffff", width=768, height=2000)
    c.create_window((0,260), window=f, anchor="nw",tags="f")

    
    #flag blue
    #canvas = Canvas(window,width=256,height=256)
    #canvas.place(x=0,y=0)
    flag_blue_img = PhotoImage(file="flag_blue.png")
    c.create_image(0,0,anchor=NW,image=flag_blue_img)
    
    #health_blue
    health_blue = Label(f,
                     text="health",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    health_blue.place(x=0,y=0)
    
    #status_blue
    status_blue = Label(f,
                     text="status",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    status_blue.place(x=0,y=40)

    #time_blue
    time_blue = Label(f,
                     text="status",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    time_blue.place(x=0,y=80)
    
    #aantal_spelers_blue
    aantal_spelers_blue = Label(f,
                     text="spelers: 0",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    aantal_spelers_blue.place(x=0,y=120)
    
    #flag red
    #canvas2 = Canvas(c,width=256,height=256)
    #canvas2.place(x=256,y=0)
    flag_red_img = PhotoImage(file="flag_red.png")
    c.create_image(256,0,anchor=NW,image=flag_red_img)
    
    #health_red
    health_red = Label(f,
                     text="health",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    health_red.place(x=256,y=0)
    
    #status_red
    status_red = Label(f,
                     text="status",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    status_red.place(x=256,y=40)
    
    #time_red
    time_red = Label(f,
                     text="status",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    time_red.place(x=256,y=80)
    
    #aantal_spelers_red
    aantal_spelers_red = Label(f,
                     text="spelers: 0",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    aantal_spelers_red.place(x=256,y=120)
    
    #flag green
    #canvas3 = Canvas(c,width=256,height=256)
    #canvas3.place(x=512,y=0)
    flag_green_img = PhotoImage(file="flag_green.png")
    c.create_image(512,0,anchor=NW,image=flag_green_img)

    #health_green
    health_green = Label(f,
                     text="health",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    health_green.place(x=512,y=0)
    
    #status_green
    status_green = Label(f,
                     text="status",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    status_green.place(x=512,y=40)
    
    #status_green
    time_green = Label(f,
                     text="status",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    time_green.place(x=512,y=80)
    
    #aantal_spelers_green
    aantal_spelers_green = Label(f,
                     text="spelers: 0",
                     bg="white",
                     fg="grey",
                     font=("Helvetica", 20))
    aantal_spelers_green.place(x=512,y=120)
    
    # start_Button
    start_button = Button(c, text="start spel", font=("Helvetica", 20), bd=0,command=startGame)
    start_button.place(x=0,y=600)
    # stop_Button
    stop_button = Button(c, text="stop spel", font=("Helvetica", 20), bd=0,command=stopGame)
    stop_button.place(x=256,y=600)
    # reset_Button
    reset_button = Button(c, text="reset tel. data", font=("Helvetica", 20), bd=0,command=resetGameTelemetry)
    reset_button.place(x=512,y=600)
    
    #gui elements players color flag
    players_green_gui = []
    players_red_gui = []
    players_blue_gui = []
    
    def clock():
        time = datetime.datetime.now().strftime("Time: %H:%M:%S")
        #update flag data in gui
        health_green.config(text=green_flag_data.health + "%")
        status_green.config(text=green_flag_data.status)
        time_green.config(text="time: " + green_flag_data.timeOfDeath + "s")
        health_red.config(text=red_flag_data.health + "%")
        status_red.config(text=red_flag_data.status)
        time_red.config(text="time: " + red_flag_data.timeOfDeath + "s")
        health_blue.config(text=blue_flag_data.health + "%")
        status_blue.config(text=blue_flag_data.status)
        time_blue.config(text="time: " + blue_flag_data.timeOfDeath + "s")
        
        #player label parameters
        textSize = 10
        textSpace = textSize * 2
        numberPlayerStats = 6
        multiplier = textSpace * numberPlayerStats
        yOffset = 160
        
        #update green player data in gui
        for i in range(len(players_green_gui)):
            for j in range(len(players_green_gui[i])):
                    players_green_gui[i][j].destroy()
            players_green_gui[i].clear()
        players_green_gui.clear()
        
        aantal_spelers_green.config(text="spelers: " + str(len(player_list_data_green)))
        
        for i in range(len(player_list_data_green)):
            #print(str(Label(window, "player " + i, bg="white", fg="grey", font=("Helvetica", 20))))      
            playerX_green_gui = []
            playerX_green_gui.append(Label(f, text="speler " + str(i+1), bg="white", fg="grey", font=("Helvetica", textSize)))
            playerX_green_gui.append(Label(f, text="leven: " + str(player_list_data_green[i].health), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_green_gui.append(Label(f, text="status: " + str(player_list_data_green[i].status), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_green_gui.append(Label(f, text="hits: " + str(player_list_data_green[i].hits), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_green_gui.append(Label(f, text="shots: " + str(player_list_data_green[i].shots), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_green_gui.append(Label(f, text="time: " + str(player_list_data_green[i].timeOfDeath), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_green_gui[0].place(x=512,y=yOffset + i*multiplier)
            playerX_green_gui[1].place(x=532,y=yOffset + textSpace + i*multiplier)
            playerX_green_gui[2].place(x=532,y=yOffset + textSpace*2 + i*multiplier)
            playerX_green_gui[3].place(x=532,y=yOffset + textSpace*3 + i*multiplier)
            playerX_green_gui[4].place(x=532,y=yOffset + textSpace*4 + i*multiplier)
            playerX_green_gui[5].place(x=532,y=yOffset + textSpace*5 + i*multiplier)
            players_green_gui.append(playerX_green_gui)
        
        #update red players data in gui
        for i in range(len(players_red_gui)):
            for j in range(len(players_red_gui[i])):
                    players_red_gui[i][j].destroy()
            players_red_gui[i].clear()
        players_red_gui.clear()
        
        aantal_spelers_red.config(text="spelers: " + str(len(player_list_data_red)))
        
        for i in range(len(player_list_data_red)):
            #print(str(Label(window, "player " + i, bg="white", fg="grey", font=("Helvetica", 20))))      
            playerX_red_gui = []
            playerX_red_gui.append(Label(f, text="speler " + str(i+1), bg="white", fg="grey", font=("Helvetica", textSize)))
            playerX_red_gui.append(Label(f, text="leven: " + str(player_list_data_red[i].health), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_red_gui.append(Label(f, text="status: " + str(player_list_data_red[i].status), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_red_gui.append(Label(f, text="hits: " + str(player_list_data_red[i].hits), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_red_gui.append(Label(f, text="shots: " + str(player_list_data_red[i].shots), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_red_gui.append(Label(f, text="time: " + str(player_list_data_red[i].timeOfDeath), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_red_gui[0].place(x=256,y=yOffset + i*multiplier)
            playerX_red_gui[1].place(x=276,y=yOffset + textSpace + i*multiplier)
            playerX_red_gui[2].place(x=276,y=yOffset + textSpace*2 + i*multiplier)
            playerX_red_gui[3].place(x=276,y=yOffset + textSpace*3 + i*multiplier)
            playerX_red_gui[4].place(x=276,y=yOffset + textSpace*4 + i*multiplier)
            playerX_red_gui[5].place(x=276,y=yOffset + textSpace*5 + i*multiplier)
            players_red_gui.append(playerX_red_gui)

        #update red players data in gui
        for i in range(len(players_blue_gui)):
            for j in range(len(players_blue_gui[i])):
                    players_blue_gui[i][j].destroy()
            players_blue_gui[i].clear()
        players_blue_gui.clear()
        
        aantal_spelers_blue.config(text="spelers: " + str(len(player_list_data_blue)))
        
        for i in range(len(player_list_data_blue)):
            #print(str(Label(window, "player " + i, bg="white", fg="grey", font=("Helvetica", 20))))      
            playerX_blue_gui = []
            playerX_blue_gui.append(Label(f, text="speler " + str(i+1), bg="white", fg="grey", font=("Helvetica", textSize)))
            playerX_blue_gui.append(Label(f, text="leven: " + str(player_list_data_blue[i].health), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_blue_gui.append(Label(f, text="status: " + str(player_list_data_blue[i].status), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_blue_gui.append(Label(f, text="hits: " + str(player_list_data_blue[i].hits), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_blue_gui.append(Label(f, text="shots: " + str(player_list_data_blue[i].shots), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_blue_gui.append(Label(f, text="time: " + str(player_list_data_blue[i].timeOfDeath), bg="white", fg="grey", font=("Helvetica", textSize)))            
            playerX_blue_gui[0].place(x=0,y=yOffset + i*multiplier)
            playerX_blue_gui[1].place(x=20,y=yOffset + textSpace + i*multiplier)
            playerX_blue_gui[2].place(x=20,y=yOffset + textSpace*2 + i*multiplier)
            playerX_blue_gui[3].place(x=20,y=yOffset + textSpace*3 + i*multiplier)
            playerX_blue_gui[4].place(x=20,y=yOffset + textSpace*4 + i*multiplier)
            playerX_blue_gui[5].place(x=20,y=yOffset + textSpace*5 + i*multiplier)
            players_blue_gui.append(playerX_blue_gui)

        window.after(1000, clock) # run itself again after 1000 ms

    
    clock()
    
    def on_closing():
        global program_running
        program_running = False
        print("closing program")
        window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()
    print("Thread stopping")

is_on=False

def startGame():
    #flag_60HT_300PT_30HD_2PRC_4PLC_0374G_
    #player_60HT_300PT_30HD_5HT_0SA_2PRC_4PLC_0374G_
    global currentGameId
    playing_channel = random.randint(3,14)
    print("playing channel: " + str(playing_channel))
    pub_flag_data = "flag_prestart_" + str(hiding_time) + "HT_" + str(playing_time) + "PT_" + str(hit_damage) + "HD_" + str(practicing_channel) + "PRC_" + str(playing_channel) + "PLC_" + str(currentGameId) + "G_"
    pub_player_data = "player_prestart_" + str(hiding_time) + "HT_" + str(playing_time) + "PT_" + str(hit_damage) + "HD_" + str(hit_timeout) + "HT_" + str(shot_ammo) + "SA_" + str(practicing_channel) + "PRC_" + str(playing_channel) + "PLC_" + str(currentGameId) + "G_"
    
    global client
    status = 0
    publish(client, topic_player_pub_prestart, status, pub_player_data)
    time.sleep(0.1)
    publish(client, topic_flag_pub_prestart, status, pub_flag_data)

def stopGame():
    stop_data = "stop"
    status = 0
    publish(client, topic_stop, status, stop_data)

def resetGameTelemetry():
    player_list_data_blue.clear()
    player_list_data_red.clear()
    player_list_data_green.clear()
    
    health: str
    status: str
    timeOfDeath: str
    gameId: str
    
    green_flag_data.health = "0%"
    green_flag_data.status = "death"
    green_flag_data.timeOfDeath = "0s"
    green_flag_data.gameId = "0"
    red_flag_data.health = "0%"
    red_flag_data.status = "death"
    red_flag_data.timeOfDeath = "0s"
    red_flag_data.gameId = "0"
    blue_flag_data.health = "0%"
    blue_flag_data.status = "death"
    blue_flag_data.timeOfDeath = "0s"
    blue_flag_data.gameId = "0"
    
def connect_mqtt():
    global client
    def on_connect(client, cuserdata, flags, rc):
        if rc==0:
            print("Succesfully connected to MQTT broker")
        else:
            print("failed to connect to MQTT broker, return code: %d", rc)
    
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client
    
def publish(client, topic, status, msg):
    #msg = "hello world to jan stappers"
    #"{\"action\":\"command/insert\",\"deviceId\":\""+deviceId+"\",\"command\":{\"command\":\"LED_control\",\"parameters\":{\"led\":\""+status+"\"}}}"
    result = client.publish(topic, msg)
    msg_status = result[0]
    if msg_status ==0:
        #print(f"message : {msg} sent to topic {topic_pub}")
        pass
    else:
        pass
        #print(f"Failed to send message to topic {topic_pub}")

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(msg)
        print(msg.topic)
        data = msg.payload.decode()
        if msg.topic == topic_flag:
            data = "flag: " + data
        if msg.topic == topic_player:
            data = "player: " + data
        #if msg.topic == topic_player:
        #    data = "player: " + data
        print(data)
        global sub_data
        sub_data.append(data)
        #y = json.loads(msg.payload.decode())
        #temp = y["notification"]["parameters"]["temp"]
        #hum = y["notification"]["parameters"]["humi"]
        #print("temperature: ",temp,", humidity:",hum)
    print ("bla")
    
    #client.subscribe(topic_sub)
    #client.subscribe(topic_sub2)
    
    #subscription flags contains flag color, health, status
    client.subscribe(topic_flag)
    
    #subscription players contains player-id (mac), flag color, health, status, hits, shots
    client.subscribe(topic_player)
    print ("blabla")
    client.on_message = on_message
    print ("blablabla")

def searchList(list, input):
    for i in range(len(list)):
        if list[i].find(input) >= 0:
            return i       
    return False

def searchPlayerList(player_list_data, input):
    for i in range(len(player_list_data)):
        print(player_list_data[i].playerId + " VS " + input + " result: " + str(player_list_data[i].playerId.find(input)))
        if player_list_data[i].playerId.find(input) >= 0:
            return i       
    return -1

def main():
    global green_flag_data
    global red_flag_data
    global blue_flag_data
    global player_list
    status = "0"
    client_local = connect_mqtt()
    #time.sleep(1)
    #print("trying to send something?")
    publish(client_local, topic_pub, status, "hello test from jan stappers")
    subscribe(client_local)
    client_local.loop_start()
    seconds = str(round(time.time()))
    global currentGameId 
    currentGameId = seconds[len(seconds)-4:]
    print("currentGameId: " + str(currentGameId))
    gui_thread = threading.Thread(target=thread_gui, args=(1,))
    gui_thread.start()
    global program_running
    global sub_data
    
    while(program_running == True):
        #print("we are waiting")
        publish(client_local, topic_pub, status, "hello test from jan stappers")
        print(sub_data)
        
        #process flag data
        #process green flag data
        index = searchList(sub_data, "flag: green")
        #print("index i:" + str(index))
        if index != False:
            green_flag_data.gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
            if green_flag_data.gameId == currentGameId:
                green_flag_data.health = sub_data[index][ sub_data[index].find("greenC_")+7 : sub_data[index].find("H_") ]
                green_flag_data.status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                green_flag_data.timeOfDeath = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("T_") ]
            else:
                print("this green FLAG is not in the current game: ")
            sub_data.remove(sub_data[index])
            
        #process blue flag data
        index = searchList(sub_data, "flag: blue")
        #print("index i:" + str(index))
        if index != False:
            blue_flag_data.gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
            if blue_flag_data.gameId == currentGameId:
                blue_flag_data.health = sub_data[index][ sub_data[index].find("blueC_")+6 : sub_data[index].find("H_") ]
                blue_flag_data.status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                blue_flag_data.timeOfDeath = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("T_") ]
            else:
                print("this blue FLAG is not in the current game: ")
            sub_data.remove(sub_data[index])
            
        #process red flag data
        index = searchList(sub_data, "flag: red")
        #print("index i:" + str(index))
        if index != False:
            red_flag_data.gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
            if red_flag_data.gameId == currentGameId:
                red_flag_data.health = sub_data[index][ sub_data[index].find("redC_")+5 : sub_data[index].find("H_") ]
                red_flag_data.status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                red_flag_data.timeOfDeath = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("T_") ]
            else:
                print("this red FLAG is not in the current game: ")
            sub_data.remove(sub_data[index])
            #print("red health" + red_flag_data.health)
            
        #greenC_00AA11BB22CCI_100H_aliveS_14HI_58SH_    
        #player_list_data_green
        
        #process green player data
        green_player_data_temp = Player("green", "00AA11BB22CC", "0", "death", "0", "0", "0", "0")
        index = searchList(sub_data, "player: green")
        #print("index i:" + str(index))
        print ("search green flag index: " + str(index))
        print ("len of player list: " + str(len(player_list_data_green)))
        if index != False:
            green_player_data_temp.playerId = sub_data[index][ sub_data[index].find("C_")+2 : sub_data[index].find("I_") ]
            #print("player id: " + green_player_data_temp.playerId)
            playerIndex = searchPlayerList(player_list_data_green, green_player_data_temp.playerId)
            #index = False
            print ("search index new players: " + str(index))
            if playerIndex == -1:
                #player doesn't exist in list ==> create new entry
                green_player_data_temp.color = "green"
                green_player_data_temp.health = sub_data[index][ sub_data[index].find("I_")+2 : sub_data[index].find("H_") ]
                green_player_data_temp.status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                green_player_data_temp.hits = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("HI_") ]
                green_player_data_temp.shots = sub_data[index][ sub_data[index].find("HI_")+3 : sub_data[index].find("SH_") ]
                green_player_data_temp.timeOfDeath = sub_data[index][ sub_data[index].find("SH_")+3 : sub_data[index].find("T_") ]
                green_player_data_temp.gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
                if green_player_data_temp.gameId == currentGameId:
                    player_list_data_green.append(green_player_data_temp)
                else:
                    print("this green PLAYER is not in the current game: " + green_player_data_temp.playerId)
                    pass
                #print("color player" + player_list_data_green[len(player_list_data_green)-1].color)
            else:
                #player exists in list ==> udpate existing entry
                player_list_data_green[playerIndex].color = "green"
                player_list_data_green[playerIndex].health = sub_data[index][ sub_data[index].find("I_")+2 : sub_data[index].find("H_") ]
                player_list_data_green[playerIndex].status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                player_list_data_green[playerIndex].hits = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("HI_") ]
                player_list_data_green[playerIndex].shots = sub_data[index][ sub_data[index].find("HI_")+3 : sub_data[index].find("SH_") ]
                player_list_data_green[playerIndex].timeOfDeath = sub_data[index][ sub_data[index].find("SH_")+3 : sub_data[index].find("T_") ]
                player_list_data_green[playerIndex].gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
                
            sub_data.remove(sub_data[index])
        
        #process red player data
        red_player_data_temp = Player("red", "00AA11BB22CC", "0", "death", "0", "0", "0", "0")
        index = searchList(sub_data, "player: red")
        #print("index i:" + str(index))
        print ("search red flag index: " + str(index))
        print ("len of player list: " + str(len(player_list_data_red)))
        if index != False:
            red_player_data_temp.playerId = sub_data[index][ sub_data[index].find("C_")+2 : sub_data[index].find("I_") ]
            #print("player id: " + red_player_data_temp.playerId)
            playerIndex = searchPlayerList(player_list_data_red, red_player_data_temp.playerId)
            #index = False
            print ("search index new players: " + str(index))
            if playerIndex == -1:
                #player doesn't exist in list ==> create new entry
                red_player_data_temp.color = "red"
                red_player_data_temp.health = sub_data[index][ sub_data[index].find("I_")+2 : sub_data[index].find("H_") ]
                red_player_data_temp.status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                red_player_data_temp.hits = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("HI_") ]
                red_player_data_temp.shots = sub_data[index][ sub_data[index].find("HI_")+3 : sub_data[index].find("SH_") ]
                red_player_data_temp.timeOfDeath = sub_data[index][ sub_data[index].find("SH_")+3 : sub_data[index].find("T_") ]
                red_player_data_temp.gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
                if red_player_data_temp.gameId == currentGameId:
                    player_list_data_red.append(red_player_data_temp)
                else:
                    print("this red PLAYER is not in the current game: " + red_player_data_temp.playerId)
                    pass
                #print("color player" + player_list_data_red[len(player_list_data_red)-1].color)
            else:
                #player exists in list ==> udpate existing entry
                player_list_data_red[playerIndex].color = "red"
                player_list_data_red[playerIndex].health = sub_data[index][ sub_data[index].find("I_")+2 : sub_data[index].find("H_") ]
                player_list_data_red[playerIndex].status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                player_list_data_red[playerIndex].hits = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("HI_") ]
                player_list_data_red[playerIndex].shots = sub_data[index][ sub_data[index].find("HI_")+3 : sub_data[index].find("SH_") ]
                player_list_data_red[playerIndex].timeOfDeath = sub_data[index][ sub_data[index].find("SH_")+3 : sub_data[index].find("T_") ]
                player_list_data_red[playerIndex].gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
                
            sub_data.remove(sub_data[index])
            print ("len of player list: " + str(len(player_list_data_red)))
        
        
        #process blue player data
        blue_player_data_temp = Player("blue", "00AA11BB22CC", "0", "death", "0", "0", "0", "0")
        index = searchList(sub_data, "player: blue")
        #print("index i:" + str(index))
        print ("search blue flag index: " + str(index))
        print ("len of player list: " + str(len(player_list_data_blue)))
        if index != False:
            blue_player_data_temp.playerId = sub_data[index][ sub_data[index].find("C_")+2 : sub_data[index].find("I_") ]
            #print("player id: " + blue_player_data_temp.playerId)
            playerIndex = searchPlayerList(player_list_data_blue, blue_player_data_temp.playerId)
            #index = False
            print ("search index new players: " + str(index))
            if playerIndex == -1:
                #player doesn't exist in list ==> create new entry
                blue_player_data_temp.color = "blue"
                blue_player_data_temp.health = sub_data[index][ sub_data[index].find("I_")+2 : sub_data[index].find("H_") ]
                blue_player_data_temp.status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                blue_player_data_temp.hits = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("HI_") ]
                blue_player_data_temp.shots = sub_data[index][ sub_data[index].find("HI_")+3 : sub_data[index].find("SH_") ]
                blue_player_data_temp.timeOfDeath = sub_data[index][ sub_data[index].find("SH_")+3 : sub_data[index].find("T_") ]
                blue_player_data_temp.gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
                if blue_player_data_temp.gameId == currentGameId:
                    player_list_data_blue.append(blue_player_data_temp)
                else:
                    print("this blue PLAYER is not in the current game: " + blue_player_data_temp.playerId)
                    pass
                #print("color player" + player_list_data_blue[len(player_list_data_blue)-1].color)
            else:
                #player exists in list ==> udpate existing entry
                player_list_data_blue[playerIndex].color = "blue"
                player_list_data_blue[playerIndex].health = sub_data[index][ sub_data[index].find("I_")+2 : sub_data[index].find("H_") ]
                player_list_data_blue[playerIndex].status = sub_data[index][ sub_data[index].find("H_")+2 : sub_data[index].find("S_") ]
                player_list_data_blue[playerIndex].hits = sub_data[index][ sub_data[index].find("S_")+2 : sub_data[index].find("HI_") ]
                player_list_data_blue[playerIndex].shots = sub_data[index][ sub_data[index].find("HI_")+3 : sub_data[index].find("SH_") ]
                player_list_data_blue[playerIndex].timeOfDeath = sub_data[index][ sub_data[index].find("SH_")+3 : sub_data[index].find("T_") ]
                player_list_data_blue[playerIndex].gameId = sub_data[index][ sub_data[index].find("T_")+2 : sub_data[index].find("G_") ]
                
            sub_data.remove(sub_data[index])
            print ("len of player list: " + str(len(player_list_data_blue)))
        time.sleep(.5)
if __name__ == '__main__':
    main()
