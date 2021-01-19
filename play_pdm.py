import pyaudio
import wave
import time
import struct
import numpy
from scipy.signal import butter, lfilter, lfilter_zi

CHUNK = 2048
PDM_OSR = 64
PDM_SCALE = 5
PDM_CHUNK_SIZE = CHUNK*PDM_OSR//8    # in bytes
ANALPF_b, ANALPF_a = butter(4, 21.5e3/(64*44.1e3/2), 'low')
ANALPF_state = [numpy.zeros(len(ANALPF_b)-1), numpy.zeros(len(ANALPF_b)-1)]

# filename = '../data/RockDrums-48-stereo-11secs.pdm_stereo'
# filename = '../data/HotelCalifornia.pdm_stereo'
filename = '../data/HowsItGoingToBe.pdm_stereo'

wf = open(filename, 'rb')
if filename.endswith('pdm_stereo'):
    nchannels = 2
else:
    nchannels = 1

# pdm2pcm conversion
def pdm2pcm(mem):
    zi = globals()['ANALPF_state']
    data_pdm = struct.unpack('<%iB'%len(mem),mem)
    data_step = 1 if nchannels == 1 else 2
    frame_out = numpy.zeros((len(data_pdm)*8)//PDM_OSR,dtype='int16')
    for k in range(nchannels):
        bitstream = numpy.unpackbits(numpy.array(data_pdm[::data_step],dtype='uint8')).astype('float')
        pcm_out,zi_out = lfilter(ANALPF_b,ANALPF_a,2*bitstream-1,zi=zi[k])
        subframe = numpy.round(pcm_out[::PDM_OSR]*8/PDM_SCALE*2**15).astype(dtype=numpy.int32)
        subframe[subframe>32767] = 32767
        subframe[subframe<-32767] = -32767
        frame_out[k::data_step] = subframe
        zi[k] = zi_out
    globals()['ANALPF_state'] = zi
    return frame_out.astype('int16')

def callback(in_data, frame_count, time_info, status):
    chunk_size = frame_count
    pdm_chunk_size = nchannels*chunk_size*PDM_OSR//8
    data = wf.read(pdm_chunk_size)
    data_pcm = pdm2pcm(data)
    return (data_pcm, pyaudio.paContinue)

# create & start play
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=nchannels,
                rate=44100,
                output=True,
                stream_callback=callback)

stream.start_stream()
while stream.is_active():
    time.sleep(0.1)
stream.stop_stream()
stream.close()
p.terminate()
wf.close()
