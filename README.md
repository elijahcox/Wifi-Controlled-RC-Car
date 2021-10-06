# Wifi-Controlled-RC-Car
This is a solo project that I completed for CSCE-462 (Microcontroller systems) last semester. 
It involves taking an original RC car from amazon and converting it to be controlled remotely via SSH. It also features camera streaming capabilities.

I achieved this by using a Raspberry Pi, two L298N motor drivers, a 12V rechargeable batttery, and a 3000 mAH portable power supply for the Pi.
For video streaming, I used Mjpg-streamer (https://github.com/jacksonliam/mjpg-streamer).

This script governs every aspect of control. Startup initiates an SSH request, starts MJPG-streamer, and automatically opens the stream on the client side.
It then forks to a few processes in order to simultaneously take forward/reverse, left/right, and stop stream controls.
