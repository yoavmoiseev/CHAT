const socket = io("http://" + window.location.hostname + ":8080"); // Automatically use the correct host
var flag = 3; // Private chat
parentNickName =""
toNickName =""

//=========================================================================
// Emmitate clicking the "Send the Message" by pressing "Enter" button
document.addEventListener("keydown", function(event) {
        // Check if "Enter" key is pressed
        if (event.key === "Enter") {
            event.preventDefault(); // Prevent any default action, such as form submission
            sendPrivate(); // Call the send message function
        }  });

//SEND messages TO Server======================================================
function sendPrivate() {
    //alert(myText.value)
    socket.emit("message", String(flag) + parentNickName + " to: " + toNickName + " :    " + myText.value);
    myText.value = ""     
        }

function PrivateOpen(){
    //Get the sender-nick from parent window
    parentNickName = window.opener ? window.opener.nickName.value : "Defaul Source Name";
    //Get the destination-nick from parent window
    toNickName = window.opener ? window.opener.current_private_nick : "Defaul destination Name";
    //Concantinating Heading for private chat page
    Heading.innerText= "Private chat. From: " + parentNickName + "  to: " + toNickName  
    socket.emit("message", "4" + parentNickName + " to: " + toNickName);
}

 //GET messages FROM server==========================================================
 socket.on("message", function(data) {
       //private chat                         //|| data.substring(0,1) == "4" 
       prefix = "3"+ parentNickName + " to: " + toNickName;
       opponent_prefix = "3"+ toNickName  + " to: " + parentNickName;
    if (data.substring(0, prefix.length) == prefix || data.substring(0, opponent_prefix.length) == opponent_prefix){
        line = document.createElement("p");
        line.innerText = data.substring(1) //Writes to the text box
        
        if (data.substring(0, opponent_prefix.length) === opponent_prefix) {
            line.style.color = "blue";}                          
        AllText.insertAdjacentElement("afterbegin", line); //Adds text to Head
    }
});
