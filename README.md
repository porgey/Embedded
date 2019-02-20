Embedded's product is Gamma, an IoT radiation-detecting watch network.

CPMHost.py s intended for use on the Raspberry Pi.

It uses the Radiation Watch Geiger sensor to detect background radiation (in Counts per Minute, CPM) while rejecting noise 
which would otherwise give false positive signal readings. (If noise detected, signal readings for previous 200ms are discarded)

20 minutes of past CPM readings are kept, in 240 5-second intervals, with the oldest records being overwritten when the max.
sampling interval is reached.

CPM is calculated by the number of counts over the past sample interval divided by the sample interval length. This CPM value
is sent to the broker along with the time as which it was recorded every second, to give an accurate measure of when the sample
was taken, as using the receipt time would be affeected by latency in the connection.

The host subscribes to emergency messages sent by the server and flashes the screen's LED backlight if one is received.

                                                #################################


CPMServer.py intended for use on a processing server subscribing to multiple hosts in each others' local area.

For the purposes of this project only one host was utilised but is easily adaptable for more host data to be received.
Host data is simulated by random number generation.

The average of 4 simulations and user1's CPM reading is taken every second and if this exceeds a set threshold (2 in this demo)
then an emergency message will be sent on the 'Emergency' topic, alerting the user of high radiation levels in their local area.



Encryption had previously been used with the Mosquitto Broker, however the new broker used, HiveMQ, does not support 
encryption so it was not implemented in this version of the software.
