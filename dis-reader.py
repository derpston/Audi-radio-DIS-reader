import pyaudio
import struct

def chunk(iterable, chunksize):
    """A generator that yields chunks of `chunksize` from iterable `iterable`."""
    for index in xrange(0, len(iterable), chunksize):
        yield iterable[index : index + chunksize]

def decode(bitstream):
    """Takes a list of integers representing bits and returns (bool, str) representing the checksum validity and the string with the ASCII equivalent of the message."""
    message = ""

    checksum = 0

    # Read the message byte-by-byte, skipping the first which is a header.
    for index, bits in enumerate(chunk(bitstream[:-8], 8)):
        # Convert each 8-bit list of integers to an int.
        # (Ugly, sorry!)
        byte = int("".join(map(lambda bit: str(bit), bits)), 2)

        # Update the checksum with this byte.
        checksum += byte

        # Append all non-header bytes to the message.
        if index > 0:
            message += chr(byte)
    
    # Read the transmitted checksum.
    transmitted_checksum = int("".join(map(lambda bit: str(bit), bitstream[-8:])), 2)

    # Verifying the checksum involves taking the sum of all bytes
    # including the header and comparing the inverted least significant
    # byte against the transmitted checksum.
    checksum_validity= ((checksum & 0xff) ^ 0xff) == transmitted_checksum
        
    return (checksum_validity, message)

def getDISMessages(binary_one_threshold = 20000):
    """A generator that attempts to read Audi radio DIS messages from
    the default microphone and yields them as plain ASCII strings.
    
    binary_one_threshold (default 20000) is a tuning value for the level
    between (-32k, 32k) above which a sample will be considered to be a
    binary 1. Your hardware / audio quality / etc may vary, but expected
    tuning values are between 5k and 32k."""

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

    message = None
    prev_clock = 0

    while True:
        # Fetch a block of samples from the microphone.
        samples = stream.read(1024)
    
        # One sample is 4 bytes, 2 for each channel. Step through the
        # samples four bytes at a time.
        for sample in chunk(samples, 4):

            # Unpack the 16-bit signed sample.
            clock, data = struct.unpack("<hh", sample)

            # Look for a rising clock edge.
            if clock > binary_one_threshold and prev_clock < binary_one_threshold:
                
                # Is this rising edge the start of a new message?
                if message is None:
                    message = []

                # Convert the data sample into a bit and add it to the message.
                message.append(int(data > binary_one_threshold))
    
                if len(message) == (18 * 8): # 18 bytes.
                    # Found the end of the message.
                    yield decode(message)
                    message = None
    
            # Keep the current clock value for the next iteration, we use
            # it for rising edge detection.
            prev_clock = clock

if __name__ == "__main__":
    print "Waiting for DIS radio messages."
    print "(possible pyaudio/alsa/pulse/jack/etc warnings are expected)"
    for (checksum_valid, message) in getDISMessages():
        print repr(message),
        
        if checksum_valid:
            print "(checksum valid)"
        else:
            print "(checksum INVALID)"

