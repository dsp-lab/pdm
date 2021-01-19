import wave
import struct
from _pdm import ffi,lib
import numpy

BLOCKSIZE = 8192*8
CHANNEL_LEFT,CHANNEL_RIGHT = range(2)
OSR = 64
SCALE = 5
DITHERMODE = 0

# filename = '../data/RockDrums-48-stereo-11secs.wav'
# filename = '../data/HotelCalifornia.wav'
filename = '../data/HowsItGoingToBe.wav'
f = wave.open(filename)
print('nchannels: %s' % f.getnchannels())
print('sampwidth: %s' % f.getsampwidth())
print('framerate: %s' % f.getframerate())
print('nframes  : %s' % f.getnframes())
channel_num = f.getnchannels()
block_num,last_block_size = divmod(f.getnframes(),BLOCKSIZE)
if last_block_size > 0:
    block_num = block_num + 1
print('blocknum: %s' % block_num)
print('lastblocksize: %s' % last_block_size)

buffer_out = ffi.new('int[]', BLOCKSIZE*128)
out_size = ffi.new('size_t *')
lib.pcm2pdm_help()
of_pdm = open(filename[:-4]+'.pdm_mono','wb') if channel_num == 1 else open(filename[:-4]+'.pdm_stereo','wb')

for block_ind in range(block_num):
    block_size = last_block_size if block_ind == block_num-1 else BLOCKSIZE
    frame = numpy.array(struct.unpack('%ih'%(block_size*channel_num), f.readframes(block_size)),dtype=numpy.int32)
    frame_out = frame.copy()
    frame_channel = [numpy.copy(frame[0::2]), numpy.copy(frame[1::2])]
    pdm_mem_vec = []
    for channel in range(channel_num):
        buffer_in = ffi.cast('int *',frame_channel[channel].ctypes.data)
        lib.pcm2pdm_conversion(channel,buffer_out,out_size,buffer_in,block_size,OSR,SCALE,DITHERMODE,block_ind == 0)
        pdm_out = numpy.frombuffer(ffi.buffer(buffer_out,out_size[0]*ffi.sizeof('int')),dtype=numpy.int32)
        pdm_mem = numpy.dot(numpy.power(2,[7,6,5,4,3,2,1,0]),pdm_out.reshape((-1,8)).T)
        pdm_mem_vec.append(pdm_mem)

    # writem pdm memory to file (always 2nd channel)
    # of_pdm.write(struct.pack('%iB'%(len(pdm_mem)),*pdm_mem.tolist()))

    if channel_num == 1:
        of_pdm.write(struct.pack('%iB'%(len(pdm_mem)),*pdm_mem.tolist()))
    else:
        pdm_mem = numpy.zeros(2*len(pdm_mem_vec[0]),dtype='uint8')
        pdm_mem[0::2] = pdm_mem_vec[0]
        pdm_mem[1::2] = pdm_mem_vec[1]
        of_pdm.write(struct.pack('%iB'%(len(pdm_mem)),*pdm_mem.tolist()))

    print('block %3d: %d' % (block_ind,out_size[0]))

f.close()
of_pdm.close()
