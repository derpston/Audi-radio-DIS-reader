Audi-radio-DIS-Reader
=====================

A tool for reading the text that an Audi radio sends to the Driver Information System LCD.


Background
==========

The Driver Information System is the LCD in the middle of the dashboard clocks, seen here:

![Audi DIS](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/audi-dis.jpg "Audi DIS")

The stock radios are able to send arbitrary text to the top third of this display. In the above picture, it is reporting that track 6 on CD 5 is playing.

The specific radio this worked with was an Audi Concert, model 4B0 035 186.

The radio uses three pins and a simple format to send this data to the DIS. The pins we're interested in are in the top 20-pin connector on the rear of the radio, pins 8, 9 and 10 and you can find a [full pinout here](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/concertpinout.gif).

![Audi Concert radio connectors](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/audi-concert-connectors.jpg "Audi Concert radio connectors")

* 8: DIS clock signal
* 9: DIS data signal
* 10: DIS enable signal

These pins produce digital signals at 5V.

For the purpose of reading the DIS data sent by the radio, we can ignore pin 10, the DIS enable signal.

The radio was removed from the car and powered from a 12V supply in a lab environment. On the lower 8-pin connector ("III") use pin 8 for GND and 7 for +12V.

An oscilloscope was used to verify the clock/data pin understanding was correct and establish the signal levels:

![Oscillopscope](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/audi-radio-dis-scope.jpg "Measuring pins 8 and 9 with an oscilliscope")

In order to read the signals on pins 8 and 9, I used a PC soundcard with a stereo microphone feature. Pin 8 was connected to the left channel and pin 9 to the right. No discrete components were used between the two, the soundcard seemed to handle the 5V signals without complaint.

![Lab overview](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/lab-overview.jpg "Lab overview")

![Connection closeup](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/connections-closeup.jpg "Connection closeup")

In a sound editor, this is what I saw:

![DIS clock/data signals](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/dis-clock-data.jpg "DIS clock/data signals")

This is where the code in this repo comes in.

Reading the DIS data with Python
================================

With the clock/data lines connected to the left/right audio channels, one can use PyAudio to read samples from the microphone and detect high/low bit states.

The protocol is relatively simple. Each time the clock signal shows a rising edge, read one bit from the data signal.

![Decoding DIS data](https://raw.github.com/derpston/Audi-radio-DIS-reader/master/img/dis-data-decoded.jpg "Decoding DIS data")

Working with PyAudio to read this data is relatively simple.

Configure reading from the microphone port:

```python
# Read from the microphone.
# Ask for 16-bit signed samples, stereo at 96kHz and 1024 samples
# each time we read from the buffer.
# Note that this requires stereo because the data has clock and data
# signals - we need both, and hardware capable of stereo input.
stream = pyaudio.PyAudio().open(
    format = pyaudio.paInt16,
    channels = 2,
    rate = 96000,
    input = True,
    frames_per_buffer = 1024)
```

Read one sample and convert the left and right channel values to integers.

```python
sample = stream.read(1)

# One sample is 4 bytes, 2 for each channel.
# Unpack the 16-bit signed samples.
clock, data = struct.unpack("<hh", sample)
```

At this point, ```clock``` and ```data``` contain integers between -32k and 32k, corresponding to the voltage level on the signal lines at that time. If you compare that with, say, 20k, you can be reasonably sure you are seeing a '1' or a '0'.

After this, all that is needed is some simple logic to handle the format.

DIS data format
===============
The messages appear to be a fixed 18 bytes, where the first and last bytes are a header/footer and can be discarded. There appear to be two checksum bytes at the end that I haven't figured out yet.

An example capture produces something like this:

```
1111 0000 '\xf0'
0010 0000 ' '
0010 0000 ' '
0011 0001 '1'
0011 0000 '0'
0011 0010 '2'
0010 1110 '.'
0011 0000 '0'
0010 0000 ' '
0100 0110 'F'
0100 1101 'M'
0011 0001 '1'
0010 1101 '-'
0011 0011 '3'
0010 0000 ' '
0010 0000 ' '
0001 1100 '\x1c'
0101 1110 '^'
```

Which corresponds to a DIS display of: "  102.0 FM1-3  "

Dependencies
============

* An Audi radio that generates this data.
* A power supply to get it running in a lab environment. (12V, 5A)
* An antenna. (A piece of wire will do.)
* A sound device capable of stereo input.
* PyAudio. (Available under Ubuntu from the python-pyaudio package)

Running it
==========

Once you have the dependencies installed, try running it and pressing some preset buttons on the radio to make it generate DIS data.

```
~$ python dis-reader.py
Waiting for DIS radio messages. (possible pyaudio error messages are expected)
[...audio system warnings snipped...]
   89.6 FM1-4  
   89.6 FM1    
```

Troubleshooting
===============

The first troubleshooting step should be to open a sound recording application like Audacity and record a sample. You should see spikes when the radio sends DIS data. Try zooming in on them to look at the quality of the waveforms. You should get something similar to the DIS clock/data signal screenshot above.

Contributing
========
Contributions welcome!

