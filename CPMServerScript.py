import paho.mqtt.client as mqtt
import json
import sys
import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from collections import deque
import random

client = mqtt.Client()
connect=client.connect("broker.hivemq.com",port=1883)                  #connect to hiveMQ broker, encryption not supported on this broker
#connect=client.connect("ee-estott-octo.ee.ic.ac.uk",port=1883)        #encryption working previously on mosquitto broker

if connect==0:
    print('connected',file=sys.stdout)                                 #notify when connection is successful

def on_message(client, userdata, message):                             #callback when MQTT published code is received                      
        global timeList
        global CPMList
        dictDumps=json.loads(message.payload)                          #decode MQTT message into a Python dictionary of time and CPM values
        vals = list(dictDumps.values())[0]                             #create a list of value from the dictionary
        vals = vals[0]                                                 #access and store decoded message in vals 

        x = []
        for i in range(0,4):                                           #simulating CPM readings from nearby users 
            x.append(random.gauss(1,1))                                #generate 4 random numbers for simulated CPM readings 

        x.append(vals['currentCPM'])                                   #add user1's data to user array                                 
        
        mean = sum(x)/5                                                #average CPM values
        if mean > 2:                                                   #CPM=2 is set as unsafe threshold
            emergMessage = 1                                           #set emergency flag to 1 
            payload = json.dumps([{"emergencyMessage":emergMessage}])  #create JSON array with counts
            publish = client.publish("IC.embedded/Embedded/Emergency",payload,qos=0)     #publish emergency to broker
            if publish.rc != 0:
                print(mqtt.error_string(publish.rc))                   #notify if error in publishing
        #print(vals['time'])
        #print(vals['currentCPM'])
        timeList.append(vals['time'])                                  #append time values
        CPMList.append(vals['currentCPM'])                             #append corresponding CPM values
        #print(timeList)
        #print(CPMList,file=sys.stderr)

client.on_message = on_message                                      
client.subscribe("IC.embedded/Embedded/user1")  
client.loop_start()                        
 
X = deque(maxlen=20)
X.append(0)
timeList = deque(maxlen=1000000)                                       #double-ended queue to store time values                            
timeList.append(0)                                  
CPMList = deque(maxlen=1000000)                                        #double-ended queue to store CPM values
CPMList.append(0)

    
app = dash.Dash(__name__)                                              #initialise application layout
app.layout = html.Div(
            [
                    dcc.Graph(id='live-graph', animate=True),          
                    dcc.Interval(                                      #specify updating frequency to once per second
                            id='graph-update',
                            interval=1*1000
                            ),
                            ]
            )

#callback function updating id:live-graph by appending timeList and CPMList.
#Event required to update graph
#here event is id:'interval' 
#retruns updated graph values
@app.callback(Output('live-graph', 'figure'), events=[Event('graph-update', 'interval')])      

#wrapper function to app.callback
#called on every interval
#updates new values into the graph
def update_graph():
    global timeList
    global CPMList
    #print(timeList,file=sys.stderr)
    #print(CPMList,file=sys.stderr)
    X.append(X[-1]+1)                                                    #array to manage range of x-axis
    data = plotly.graph_objs.Scatter(                                    #plots a scatter graph
    x=list(timeList),                                                    #x-axis is time
    y=list(CPMList),                                                     #y-axis is CPM
    name='Scatter',
    mode= 'lines+markers')
    #print(data,file=sys.stderr)
    
    #returns updated x and y axis data
    #updates axis range depending on max CPM values to suitably fit the plot
    return {'data': [data],'layout' : go.Layout(title='CPM over time', xaxis=dict(title='Time',range=[min(X),max(X)]),
                                                    yaxis=dict(title='CPM',range=[min(CPMList)-1,max(CPMList)+1]),)}

if __name__ == '__main__':                                                #run Dash app
    app.run_server(debug=True)
