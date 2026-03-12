let CONFIG = {
  // number of failures before triggering a Restart
  numberOfFails: 1, // 5 try
  // time in seconds between retries
  retryIntervalSeconds: 10
};

let failCounter = 0;
let check_for_wifi = true;

function checkForWifi() {
  if (!check_for_wifi) return;

  const response = Shelly.getComponentStatus('wifi')
  const isConnected = response.status==='got ip';

  // Connection is now established OR was never broken
  // Reset counter and start over
  if(isConnected){
    console.log(Date.now(), 'WiFi works correctly. Resetting counter to 0')
    failCounter = 0;
    return;
  }

  // If not connected, increment counter of failures
  failCounter++;

  if(failCounter < CONFIG.numberOfFails){
    const remainingAttemptsBeforeRestart = CONFIG.numberOfFails-failCounter;
    console.log(Date.now(), 'WiFi healthcheck failed ', failCounter, ' out of ', CONFIG.numberOfFails, ' times')
    return;
  }

  console.log(Date.now(), 'WiFi healthcheck failed all attempts. Restarting router...')

  check_for_wifi = false;
  Shelly.call("Switch.Set", {id:0, on:false});
  Timer.set(5 * 1000, false, function(){
    Shelly.call("Switch.Set", {id:0, on:true});
    // run for some time to wait for the router boot
    Timer.set(10 * 1000, false, function(){
      check_for_wifi = true;
    });
  })
}

print(Date.now(), "Start WiFi monitor");

Timer.set(CONFIG.retryIntervalSeconds * 1000, true, checkForWifi);