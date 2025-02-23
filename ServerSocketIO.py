import os
import time
from aiohttp import web
import socketio

import consts # type: ignore

# Lists to store socket connections, users, and messages
socket_list = []
users_list = []
messages_list = []


# Create a new Async Socket IO Server
sio = socketio.AsyncServer()

# Create a new Aiohttp Web Application
app = web.Application()

# Bind our Socket.IO server to our Web App instance
sio.attach(app)

# This allows requests from any IP, including 127.0.0.1, 192.168.X.X, and 10.0.0.X.
# sio = socketio.AsyncServer(cors_allowed_origins="*") 


#==========================================================================================
#removing the following code take affect after a while- the index.html will failed with 404 error 
# add path to solitted index.html
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of ServerSocketIo.py
STATIC_DIR = os.path.join(BASE_DIR, consts.static_folder_name)  # Path to the static folder
app.router.add_static('/static/', STATIC_DIR)  # Add the static folder to the app
#==========================================================================================


# Serve the "index.html" file for the root path
async def index(request):
    file_path = os.path.join(os.path.dirname(__file__), consts.main_chat_html_file_name)
    with open(file_path) as f:
        return web.Response(text=f.read(), content_type='text/html')

# Serve the "Private_chat.html" file for the "/prChat" path
async def private_chat(request):
    file_path = os.path.join(os.path.dirname(__file__), consts.private_chat_html_file_name)
    with open(file_path) as f:
        return web.Response(text=f.read(), content_type='text/html')



# Bind our aiohttp endpoints to our app router
app.router.add_get(consts.main_chat_indicator, index)
app.router.add_get(consts.private_chat_indicator, private_chat)





# Handle incoming messages
@sio.on('message')
async def handle_message(sid, message):
    # Get the nickname and password from the message
    nickname = message[1:message.find(consts.nickname_delimiter)]
    start_position = len(nickname) + len(consts.nickname_delimiter) + 2
    password = message[start_position:message.find(consts.password_delimiter, start_position)]

    # Handle new user entry
    if message[0] == consts.main_chat_first:
        # Check the nickname does not exist
        if all(nickname != item[0] for item in users_list):
            users_list.append([nickname, password])
            print(f"{nickname} entered the chat. Time: {time.asctime()}")
        else: # the nickname exists
            for item in users_list:
                #if the nickname exist but the password is wrong
                if item[0] == nickname and item[1] != password:
                    await sio.emit('message', "Wrong Password", to=sid)
                    return

    # Remove password from the first message
    if message[0] == consts.main_chat_first:
        message = message.replace(consts.nickname_delimiter + " " + password, "", 1)

    # Send chat history to new clients
    if message[0] in [consts.main_chat_first, consts.private_chat_first]:
        for line in messages_list:
            await sio.emit('message', line, to=sid)

    messages_list.append(message)

    # Send the message back to the client
    await sio.emit('message', message)

# Start the server
if __name__ == '__main__':
    web.run_app(app)