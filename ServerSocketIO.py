from ast import Constant
from asyncio import constants
from email.message import Message
from operator import indexOf
import time
from aiohttp import web
import socketio

#Creating Lists
SocketList = []

# containing all the messages from all users
MessagesList = [] 


## creates a new Async Socket IO Server
sio = socketio.AsyncServer()
## Creates a new Aiohttp Web Application
app = web.Application()
# Binds our Socket.IO server to our Web App
## instance
sio.attach(app)

## we can define aiohttp endpoints just as we normally
## would with no change
async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

## If we wanted to create a new websocket endpoint,
## use this decorator, passing in the name of the
## event we wish to listen out for
@sio.on('message')
async def print_message(sid, message):

    #Building List of clients on base of SocketID, started above- after "import"----------------------------
    if ( str(sid) not in SocketList):
        SocketList.append(str(sid))
        print( message[1:message.find(" ")] + ", entered to the chat. Time:" + time.asctime() ) 
    
    if(message[0]=="2"):
        for line in MessagesList:
            await sio.emit('message', line, to=sid)  # to send to ALL- delete-->  to=sid
    
    MessagesList.append(message[1:]) 

    ## back to the client
    await sio.emit('message', message[1:])







## We bind our aiohttp endpoint to our app
## router
app.router.add_get('/', index)

## We kick off our server
if __name__ == '__main__':
    web.run_app(app)

