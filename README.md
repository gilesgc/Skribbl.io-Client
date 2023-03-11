# Skribbl.io-Client
Scribbl.io-Client is a python client which can play the popular online drawing game *scribbl.io* by interfacing with the API via websockets.

Through the client, you can view the paintings of other players and guess what they are drawing. The client does not offer drawing functionality, but automatically downloads a relevant image for your word and attempts to draw it automatically.

## Features:
 - GUI with textbox and canvas to chat and see what other people paint
 - Connect to private games
 - Automatically download and draw images
 
 ## Dependencies:
 - PyQt5
 - PIL
 - socketio
 
 ## How to use:
 To start the GUI, run main.py. The game will connect automatically.
 <br>
 To get a custom name, edit main.py and change name="bot" accordingly
 <br>
 To join a custom game, copy the code from the invite url and paste it in code="" in main.py. For example, if you get the url "https://skribbl.io/?ABC123", the code would be ABC123.
 
 ## Images:
 Someone else drawing:
 <img src="https://imgur.com/gr7e4jP.png" />
 
 Client drawing automatically:
 <img src="https://imgur.com/wKR9v6o.png" />
