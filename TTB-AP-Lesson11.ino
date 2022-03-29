// Using an Arduino with Python LESSON 11: Passing Data from Python to Arduino.
// https://www.youtube.com/watch?v=VdSFwYrYqW0
// https://toptechboy.com/

// https://www.arduino.cc/en/Tutorial/BuiltInExamples/SerialEvent
// https://www.best-microcontroller-projects.com/arduino-strtok.html
// https://www.e-tinkers.com/2020/01/do-you-know-arduino-sprintf-and-floating-point/
// https://www.leonardomiliani.com/en/2013/un-semplice-crc8-per-arduino/

// https://crccalc.com/?method=crc8
//  CRC-8/MAXIM
//    rgbLEDs=0!243 | rgbLEDs=1!173 | rgbLEDs=2!79  | rgbLEDs=3!17
//    rgbLEDs=4!146 | rgbLEDs=5!204 | rgbLEDs=6!46  | rgbLEDs=7!112

#include <Watchdog.h>         // A simple watchdog library.
#include <DHT.h>              // DHT11/22 sensor library.

//Debugging & testing defines - uncomment this define to enable some debug code.
//#define TESTSRX               // Enable serial received command testing serial prints.

// DHT11/22 sensor defines.
#define DHTTYPE11 DHT11       // Blue module, DHT11 defined as 11 in <DHT.h>.
#define DHTTYPE22 DHT22       // White module, DHT22 defined as 22 in <DHT.h>.

// Arduino analog I/O pin defines.
#define POT1PIN A0            // Also known as IO pin 21.

// Arduino digital I/O pin defines.
#define DHT11PIN 3
#define DHT22PIN 4
#define BLLEDPIN 5
#define GNLEDPIN 6
#define RDLEDPIN 7
#define HBLEDPIN LED_BUILTIN  // Usually digital I/O pin 13.

// Some (re)defines to make LED control easier to follow.
#define ON HIGH
#define OFF LOW

// Function prototypes - this allows the definition of default values.
void rgbLEDBank(int action = 0);

//Code loop job defines.
#define JOB1CYCLE 100         // Job 1 execution cycle: 0.1s  - Get the data: Read the potentiometers.
#define JOB2CYCLE 1000        // Job 2 execution cycle: 1s    - Get the data: Read the DHT11 sensor.
#define JOB3CYCLE 2000        // Job 3 execution cycle: 2s    - Get the data: Read the DHT22 sensor.
#define JOB4CYCLE 100         // Job 4 execution cycle: 0.1s  - Share the results: Output data to the serial console.
#define JOB5CYCLE 10          // Job 5 execution cycle: 0.01s - Action commands: Parse and action any received serial commands.
#define JOB9CYCLE 500         // Job 9 execution cycle: 0.5s  - Toggle the heartbeat LED.

// Transmit data buffer.
#define TXBUFFERMAX 32              // The maximum size of the data buffer in which sensor data characters are stored before sending.
char txBuffer[TXBUFFERMAX + 1];     // A character array variable to hold outgoing sensor data characters.
// Receive data buffer.
#define RXBUFFERMAX 32              // The maximum size of the data buffer in which received command characters are stored.
char rxBuffer[RXBUFFERMAX + 1];     // A character array variable to hold incoming command character data.
const char crcDelimiter[] = ":~!";  // The delimiter between the command and CRC8 checksum can be any of these characters.
const char cmdDelimiter[] = " ,=";  // The delimiter between the command subject and command action can be any of these characters.
bool commandReady = false;          // A flag to indicate that the current command is ready to be actioned.

// Watchdog initialisation.
Watchdog cerberous;

// Sensor object initialisations.
DHT myDHT11(DHT11PIN, DHTTYPE11);   // Initialize the DHT11 sensor for normal 16mhz Arduino (default delay = 6).
DHT myDHT22(DHT22PIN, DHTTYPE22);   // Initialize the DHT22 sensor for normal 16mhz Arduino (default delay = 6).

void setup() {
  // Initialise the potentiometer pins.
  pinMode(POT1PIN, INPUT);
  // Start the DHT11 sensor.
  myDHT11.begin();
  // Start the DHT22 sensor.
  myDHT22.begin();
  // Initialise the LED pins.
  pinMode(BLLEDPIN, OUTPUT);
  pinMode(GNLEDPIN, OUTPUT);
  pinMode(RDLEDPIN, OUTPUT);
  pinMode(HBLEDPIN, OUTPUT);
  // Start the serial port.
  Serial.begin(115200);
  while(!Serial); // Wait for the serial I/O to start.
  // Start the watchdog.
  cerberous.enable();  // The default watchdog timeout period is 1000ms.
}

void loop() {
  // Initialise the heartbeat status variable - OFF = LOW = 0.
  static bool hbStatus = OFF;
  // Initialise the potentiometer variable to something that indicates an invalid reading.
  static int pot1Value = -1;
  // Initialise the DHT variables to something that indicates invalid readings.
  //static float temperatureDHT11 = NAN;
  //static float humidityDHT11    = NAN;
  //static float temperatureDHT22 = NAN;
  //static float humidityDHT22    = NAN;
  static char temperatureDHT11str[8] = "NAN";
  static char humidityDHT11str[8]    = "NAN";
  static char temperatureDHT22str[8] = "NAN";
  static char humidityDHT22str[8]    = "NAN";
  // Initialise the CRC8 checksum variable.
  byte chksumCRC8 = 0;
  // Record the current time. When a single timeNow is used for all jobs it ensures they are synchronised.
  unsigned long timeNow = millis();
  // Job variables. Set to timeNow so that jobs do not start immediately - this allows the sensors to settle.
  static unsigned long timeMark1 = timeNow; // Last time Job 1 was executed.
  static unsigned long timeMark2 = timeNow; // Last time Job 2 was executed.
  static unsigned long timeMark3 = timeNow; // Last time Job 3 was executed.
  static unsigned long timeMark4 = timeNow; // Last time Job 4 was executed.
  static unsigned long timeMark5 = timeNow; // Last time Job 5 was executed.
  static unsigned long timeMark9 = timeNow; // Last time Job 9 was executed.
  // Job 1 - Get the data: Read the potentiometers.
  if (timeNow - timeMark1 >= JOB1CYCLE) {
    timeMark1 = timeNow;
    // Do something...
    pot1Value = analogRead(POT1PIN);
  }
  // Job 2 - Get the data: Read the DHT11 sensor.
  if (timeNow - timeMark2 >= JOB2CYCLE) {
    timeMark2 = timeNow;
    // Do something...   
    //temperatureDHT11 = myDHT11.readTemperature();
    //humidityDHT11 = myDHT11.readHumidity();
    dtostrf(myDHT11.readTemperature(), 3, 2, temperatureDHT11str);  // The temperature is needed as a string.
    dtostrf(myDHT11.readHumidity(),    3, 2, humidityDHT11str);     // The humidity is needed as a string.
  }
  // Job 3 - Get the data: Read the DHT22 sensor.
  if (timeNow - timeMark3 >= JOB3CYCLE) {
    timeMark3 = timeNow;
    // Do something...
    //temperatureDHT22 = myDHT22.readTemperature();
    //humidityDHT22 = myDHT22.readHumidity();
    dtostrf(myDHT22.readTemperature(), 3, 2, temperatureDHT22str);  // The temperature is needed as a string.
    dtostrf(myDHT22.readHumidity(),    3, 2, humidityDHT22str);     // The humidity is needed as a string.
  }
  // Job 4 - Share the results: Output CSV data to the serial console.
  if (timeNow - timeMark4 >= JOB4CYCLE) {
    timeMark4 = timeNow;
    // Do something...
    // Construct the sensor data string using the strings for the temperatures and humidities - sprintf does not support %f.
    sprintf(txBuffer, "%d,%s,%s,%s,%s", pot1Value, temperatureDHT11str, humidityDHT11str, temperatureDHT22str, humidityDHT22str);
    // Calculate the CRC8 checksum of the txBuffer.
    chksumCRC8 = calcCRC8((byte*)txBuffer); // Cast the char array pointer to a byte array pointer.
    // Print the results.
    Serial.print(txBuffer);
    // Add the CRC8 checksum to the end.
    Serial.print("!");
    Serial.println(chksumCRC8);
  }
  // Job 5 - Action commands: Parse and action any received serial commands.
  if (timeNow - timeMark5 >= JOB5CYCLE) {
    timeMark5 = timeNow;
    // Do something...
    if (commandReady) {
      // Parse the received data - NULL is returned if nothing is found by strtok().
      char *command = strtok(rxBuffer, crcDelimiter); // A pointer to a NULL terminated part of the receive buffer.
      char *chksum  = strtok(NULL, crcDelimiter);     // A pointer to another NULL terminated part of the receive buffer.
      // Lets check the CRC8 checksum, if there is one.
      if (chksum != NULL) {
        if (calcCRC8((byte*)command) != (byte)atoi(chksum)) {
          command = NULL; // Cancel the command if the CRC8 checksum has failed.
        }
      }
      // Parse the command - NULL is returned if nothing is found by strtok().
      char *subject = strtok(command, cmdDelimiter);  // A pointer to a NULL terminated part of the receive buffer.
      char *action  = strtok(NULL, cmdDelimiter);     // A pointer to another NULL terminated part of the receive buffer.
      #ifdef TESTSRX
        Serial.print("Command : ");
        if (subject != NULL) {
          Serial.print(subject);
          Serial.print(" = ");
          if (action != NULL) {
            Serial.println(action);
          }
        }
        else {
          Serial.print("None");
        }
        Serial.print("Rx CRC8 : ");
        if (chksum != NULL) {
          Serial.println(chksum);
        }
        Serial.print("Exp CRC8: ");
        Serial.println(calcCRC8((byte*)command)); // Cast the char array pointer to a byte array pointer.
      #endif
      // Lets action the command.
      if (strcmp(subject, "rgbLEDs") == 0 and action != NULL) {
        rgbLEDBank((byte)atoi(action)); // We have a recognised subject and an action for it. 
      }
      // All done, so clear the ready flag for the next command to be received.
      commandReady = false;
    }
  }
  // Job 9 - Toggle the heartbeat LED.
  if (timeNow - timeMark9 >= JOB9CYCLE) {
    timeMark9 = timeNow;
    // Do something...
    // Toggle the heartbeat status.
    hbStatus = !hbStatus;
    digitalWrite(HBLEDPIN, hbStatus);
    // Reset the watchdog.
    cerberous.reset();
  }
}

// SerialEvent automatically executes after each run of main loop if new serial data has been received.
void serialEvent() {
  // We must preserve the command buffer index between calls as this function may not collect a whole command in a single call.
  static byte bufferIndex = 0;
  while (Serial.available() and not commandReady) {
    // Get the new byte of data from the serial rx buffer.
    char rxChar = (char)Serial.read();
    // If we have received the end of command delimiter or reached the end of the buffer, finish the string and set a flag for the main loop to action the command.
    if (rxChar == '\n' or bufferIndex == RXBUFFERMAX) {
      rxBuffer[bufferIndex] = '\0'; // Terminate the string.
      commandReady = true;          // Set the command redy flag for the main loop.
      bufferIndex = 0;              // Reset the buffer index in readyness for the next command.
    }
    // Otherwise, if we are builiding a new command, add the data to the command buffer and increment the buffer index.
    if (not commandReady) {
      rxBuffer[bufferIndex++] = rxChar;
    }
  }
}

// Turn ON/OFF the red/green/blue LEDs as per the command action.
void rgbLEDBank(byte action) {
  // Valid action values are 0 - 7 using bits 0 - 2, otherwise the requetsed action is ignored.
  if (action <= 7){
    // Action value bit 0 controls the blue LED.
    if (bitRead(action, 0) == 1) {
      digitalWrite(BLLEDPIN, ON);
    }
    else {
      digitalWrite(BLLEDPIN, OFF);
    }
    // Action value bit 1 controls the green LED.
    if (bitRead(action, 1) == 1) {
      digitalWrite(GNLEDPIN, ON);
    }
    else {
      digitalWrite(GNLEDPIN, OFF);
    }
    // Action value bit 2 controls the red LED.
    if (bitRead(action, 2) == 1) {
      digitalWrite(RDLEDPIN, ON);
    }
    else {
      digitalWrite(RDLEDPIN, OFF);
    }
  }
}

// Calculate the CRC8 checksum of a null terminated character array.
// Based on the CRC8 formulas by Dallas/Maxim (GNU GPL 3.0 license).
byte calcCRC8(byte* dataBuffer) {
  // Initialise the CRC8 checksum.
  byte chksumCRC8 = 0;
  // While the byte to be process is not the null terminator.
  while(*dataBuffer != '\0') {
    byte currentByte = *dataBuffer; // Get the byte to be processed.
    // Process each bit of the byte. 
    for (byte bitCounter = 0; bitCounter < 8; bitCounter++) {
        byte sum = (chksumCRC8 ^ currentByte) & 0x01;
        chksumCRC8 >>= 1;
        if (sum) {
           chksumCRC8 ^= 0x8C;
        }
        currentByte >>= 1;
     }
     dataBuffer++;
  }
  return chksumCRC8;
}

// EOF
