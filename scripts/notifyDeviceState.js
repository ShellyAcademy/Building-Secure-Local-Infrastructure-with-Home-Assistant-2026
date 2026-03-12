let url = "https://home-assistant-ui.duckdns.org:8123/api/services/notify/notify";
let body = {
}
let auth_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI5MTE2MWYyMWJiZTc0N2E1OTU4YTFhOTM2YTk1YTA0MCIsImlhdCI6MTc3MzMzNTMzNywiZXhwIjoyMDg4Njk1MzM3fQ.ncsGSw4WVCQ48kaLmgaj6n5RrgITNEclLgEBXS_uNI0";

headers = {
  "Authorization": "Bearer " + auth_key
}

function notify_ha(message) {
  body.message = message;
  Shelly.call("HTTP.Request", {
      "url": url,
      "method": "POST",
      "headers": headers,
      "body": body
    }, function(result, error_code, error_message) {
        console.log("error code:", error_code);
        console.log("error message:", error_message);
      }
  );
}

Shelly.addStatusHandler(function(event){
  if (event.component === "switch:0" && typeof event.delta.output != "undefined") {
    if (event.delta.output) {
      notify_ha("Light is on!");
    } else {
      notify_ha("Light is off!");
    }
  }
});