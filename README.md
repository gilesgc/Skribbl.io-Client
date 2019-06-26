# Skribbl.io-Client
Play Skribbl.io without a browser

## Features:
 - GUI with textbox and canvas to see what other people paint
 - Can connect to private games
 - Autodraw images
 
 ## Dependencies:
 - hitherdither
 - google_images_download
 - PyQt5
 - PIL
 - socketio
 
 ## How to use:
 To start the GUI, run main.py. The game will connect automatically.
 <br>
 To get a custom name, edit main.py and change name="bot" accordingly
 <br>
 To join a custom game, copy the code from the invite url and paste it in code="" in main.py. For example, if you get the url "https://skribbl.io/?ABC123", the code would be ABC123.