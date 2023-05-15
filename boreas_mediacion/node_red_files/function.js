const topic = msg.topic.split("/");
var shellyStored;
var shellyId = topic[1];
var shellyType = topic[1].split("-")[0];
var shellyCircuit = topic[3];
var flowKey = shellyId + '/' + shellyCircuit;



if (flow.get(flowKey) != undefined) {
       shellyStored = flow.get(flowKey);
     }else{
       shellyStored = global.get('newShelly')(shellyType, shellyId, shellyCircuit, null);
      };


//RELAY
if (topic[2] === 'relay') {
   shellyStored.device.relay = msg.payload;

 } else {
// MEASURES
    shellyStored.measures[topic[4]] = msg.payload;
 };



flow.set(flowKey, shellyStored);

if (Object.values(shellyStored.measures).every((measure) => measure !== null)) {
        msg.payload = shellyStored;
     shellyStored = global.get('newShelly')(shellyType, shellyId, shellyCircuit, (msg.payload.device.relay));
        flow.set(flowKey, shellyStored);

        return msg;
 }
