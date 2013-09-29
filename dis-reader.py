import pyaudio
import struct

def chunk(iterable, chunksize):
    """A generator that yields chunks of `chunksize` from iterable `iterable`."""
    for index in xrange(0, len(iterable), chunksize):
        yield iterable[index : index + chunksize]

def decode(message):
    """Takes a list of integers representing bits and returns a string with the ASCII equivalent."""
    output = ""

    # Read the message byte-by-byte, skipping the first and last ones
    # which appear to be fixed
    for byte in chunk(message[8:-8], 8):
        # Convert each 8-bit list of integers to an ASCII character.
        # (Ugly, sorry!)
        output += chr(int("".join(map(lambda bit: str(bit), byte)), 2))
        
    return output

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
                    yield decode(message)
                    message = None
    
            # Keep the current clock value for the next iteration, we use
            # it for rising edge detection.
            prev_clock = clock

if __name__ == "__main__":
    print "Waiting for DIS radio messages. (possible pyaudio error messages are expected)"
    for message in getDISMessages():
        print message

