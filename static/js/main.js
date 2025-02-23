
// The code for the main chat page is in the HTML file.
//===========  Global Scope ========================

//                Server I.P(my PC)
const socket = io("http://" + window.location.hostname + ":8080"); // Automatically use the correct host


socket.on("connect", () => {
    console.log("Connected to server with ID:", socket.id);
});


var flag = 2; // First tranzaction 


//list of colors to be assigned to users
listOfcolors = ["red ", "blue ", "brown ", "OrangeRed ", "black ", "green ", "pink ", "grey ", "purpule ",
    "orange ", "DeepPink ", "Indigo ", "DarkRed ", "LimeGreen ", "Aqua ", "CadetBlue ", "RosyBrown "
]

listOfClients = []
listOfWaitingClients = []

var privateWindows = []
colorIndex = 0
blockPeriod_MilSec = 2000 //disables the sendMessage button for several seconds
current_private_nick = ""
let interval_arr = [];
const MaxLineSize = 170
let Password = ""

//============================= FUNCTIONS  ==================================
//Users instruction how to use the chat  
function MainOpen(){
    alert("Fill in your Nickname and Password in the left pane.\n" + 
        "The password is used for re-entry.\n\n" + 
        "Double-click a username in the right pane for a private conversation.\n" + 
        "The username will blink when a new private message arrives.");
}

//===========================================================================
function HidePassword(){
    if (event.inputType === 'deleteContentBackward') {
        Password = Password.slice(0, -1); // Remove the last character from Password
    } else {
    Password = Password + passWord.value.substring(passWord.value.length - 1, passWord.value.length);
    passWord.value = passWord.value.substring(0, passWord.value.length - 1) + "*"
}
}
//===========================================================================
function freezPassword(){
    if (passWord.value != "")
    passWord.disabled = true
}

//===========================================================================
//the nickName textBox will be locked after the correct nickName inserted
function freezNickName() {
    //replace spaces with underscore
    nickName.value = nickName.value.replaceAll(' ', '_')
    if (nickName.value != "")
        nickName.disabled = true
}
//=========================================================================
//Extract the nickName from left panel, even when clicking on blank space
function GetNickName(userID, entireText) {
    console.log("User ID:", userID, "| All Text:", entireText);
        let selectedText = userID.trim();
        let allText = entireText.trim(); 
        let lines = allText.split("\n"); // Split paragraph into lines

        // If user clicked on the right (empty space) or no text is selected
        if (!selectedText) {
            let range = document.createRange();
            selection.removeAllRanges();
    
            // Find the closest text node to the clicked position
            let node = document.getSelection().anchorNode;
            if (node && node.nodeType === 3) { // Ensure it's a text node
                let clickedText = node.textContent.trim();
                let matchedLine = lines.find(line => line.includes(clickedText));
    
                if (matchedLine) {
                    selectedText = matchedLine;
                    range.selectNodeContents(node.parentElement); // Select full text
                    selection.addRange(range); // Highlight the entire line
                }
            }
        }
        OpenPrivetWindow(userID, selectedText);
    }
    
//=========================================================================
//doubleClick on user name in the nickName list will
//open a new window for private chat
function OpenPrivetWindow(userID, entireText) {
    console.log("User ID:", userID, "| All Text:", entireText);

    // update the current private chat nick
    current_private_nick= userID
    // Integer number of this user in chat- starts from 0
    i = listOfClients.indexOf(userID)

    //Stop user in list blincking after private chat window opened 
    if (listOfWaitingClients.includes(userID)){
        listOfWaitingClients = listOfWaitingClients.filter(client => client !== userID);
        StopBlincking(userID)
    }
    
        //the window is closed
    if (!privateWindows[i] || privateWindows[i].closed) {
        privateWindows[i] = window.open("/prChat", "width = 800, height = 600 ")
    } else { //the window is open
        privateWindows[i].focus()
    }

}
//==========================================================================
//==================Stop blinking effect on the username in list
function StopBlincking(userID)
{
    const users = UsersColumn.innerText.split("\n"); // Split UsersColumn into lines            
    let index = users.indexOf(userID); // Find the index of the user
    index = Math.floor(index / 2)
   
    // Select all child elements in UsersColumn
    const lines = UsersColumn.querySelectorAll("p, span");
    for (const line of lines) {
        //Stops Blicking on all lines!!! the blikcing on active lines 
        // will return because of interval mechanizm
        line.style.setProperty("background-color", "", "important");
        for (const { userName, interval } of interval_arr) {
            if (userName === userID){   
                // Clear the interval
            clearInterval(interval);
            //once more -probably- Not needed
            line.style.setProperty("background-color", "", "important");
            interval_arr.splice(interval_arr.findIndex(obj => obj.userName === userID), 1);
           
        }
    }
}
}

//=========================================================================
//closes privet windows when main chat closed
function ChatClosed() {
    for (let i = 0; i < privateWindows.length; i++)
        privateWindows[i].close()
}
//==============================================================================
// Emmitate clicking the "Send the Message" by pressing "Enter" button
document.addEventListener("keydown", function(event) {
// Check if "Enter" key is pressed and that the SendButtot enabled-SPAM Blocking
if (event.key === "Enter" && SendMsgButton.disabled === false) {
    event.preventDefault(); // Prevent any default action, such as form submission
    myText.focus()
    sendMsg(); // Call the send message function
    SendMsgButton.disabled = true
    }  });
//=========================================================================
//SEND messages TO Server======================================================
function sendMsg() {
    //  nickName text-box disabled, meanning that nick name imputed
    if (nickName.disabled == true  && passWord.disabled == true) 
    {
        if (myText.value.length >=MaxLineSize){
            alert("This message is too long!!!")
        }

    if (SendMsgButton.disabled == false && myText.value.length < MaxLineSize){
        if(flag == 2){
            socket.emit("message", String(flag) + nickName.value + " : " + Password + " :    " + myText.value);
        } 
        else{
            socket.emit("message", String(flag) + nickName.value + " :    " + myText.value);}
            flag = 1;
            myText.value = ""
        }
    } else{
        alert("Input Valid nickName and password") }

        //block spumming, lock the send button fo several seconds,sleep function
        SendMsgButton.disabled = true
        setTimeout(function() {
        SendMsgButton.disabled = false
    }, blockPeriod_MilSec);
}

//=========Signalig to user in main chat that a private message arrive==============================
function blinkUser(userName) {
    const users = UsersColumn.innerText.split("\n"); // Split UsersColumn into lines
    
    let index = users.indexOf(userName); // Find the index of the user
    index = Math.floor(index / 2)
    
    if (index === -1) {
        alert(`User "${userName}" not found!`);
        return;
    }
    
    // Select all child elements in UsersColumn
    const lines = UsersColumn.querySelectorAll("p, span");                      
    const targetLine = lines[index];
    
    // Start blinking effect
    let isHighlighted = false;
    interval = setInterval(() => {
        targetLine.style.backgroundColor = isHighlighted ? "" : "red";
        isHighlighted = !isHighlighted;
    }, 500); // Toggle every 500ms
    // Store the interval and the line in the global array
    interval_arr.push({ userName, interval });
    
}



//GET messages FROM server==========================================================
socket.on("message", function(data) {
    // "This user aready exist! The Password is wrong"
    if (data == "Wrong Password")
    {
        alert("This user aready exist! The Password is wrong")
        nickName.value = ""
        passWord.value = ""
        passWord.disabled = false
        nickName.disabled = false
        flag = 2
        Password = ""
    }

    //discard private chat
    if (data.substring(0,1) == "2" || data.substring(0,1) == "1" ){
        line = document.createElement("p");
        line.innerText = data.substring(1) //Writes to the text box
        NickNameline = document.createElement("p");
        
        //AllText.appendChild(line); //Adds text to buttom
        AllText.insertAdjacentElement("afterbegin", line); //Adds text to Head
    }

    nick = String(data)
    nick = nick.substring(1, nick.indexOf(" "));
   
    // It is a Private messages to ME
    if (data.substring(0,1) == "3" && extract_user_name(data) === nickName.value){
        if (! listOfWaitingClients.includes(nick)){
            listOfWaitingClients.push(nick)
            blinkUser(nick)
        }
    }

    // Users list for private chat(right pane)- exclude current user from list of users
    if (!listOfClients.includes(nick) && nick !=nickName.value) {      
        listOfClients.push(nick)
        NickNameline.style.color = listOfcolors[listOfClients.indexOf(nick) % listOfcolors.length];
        NickNameline.innerText = nick;
        
        UsersColumn.insertAdjacentElement("afterbegin", NickNameline);
    }
        
    line.style.color = listOfcolors[listOfClients.indexOf(nick) % listOfcolors.length];
});

//================ Extract the DESTINATION username from private message
function extract_user_name(data){
   // Private message example: "3ccc to: bbb :    11111"
    const to_delemiter = "to: ";
    const index_of_to_delimeter = data.indexOf(to_delemiter);

    // Find the start of the destination username
    const index_of_dest_user_name = index_of_to_delimeter + to_delemiter.length;
    const username_end_delimiter = " :";
    const index_of_username_end = data.indexOf(username_end_delimiter, index_of_dest_user_name);
    
    // Extract the destination username
    const destination_user_name = data.substring(index_of_dest_user_name, index_of_username_end);
    return (destination_user_name)
}
