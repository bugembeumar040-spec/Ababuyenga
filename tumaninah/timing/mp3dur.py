import struct, sys, os

BR = {  # MPEG1 Layer3, MPEG2/2.5 Layer3
 (1,3): [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0],
 (2,3): [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0],
}
SR = {3:[44100,48000,32000], 2:[22050,24000,16000], 0:[11025,12000,8000]}

def skip_id3(b):
    if b[:3] == b'ID3':
        size = ((b[6]&0x7f)<<21)|((b[7]&0x7f)<<14)|((b[8]&0x7f)<<7)|(b[9]&0x7f)
        return 10 + size
    return 0

def duration(path):
    b = open(path,'rb').read()
    i = skip_id3(b)
    n = len(b)
    # trim ID3v1
    if b[-128:-125] == b'TAG': n -= 128
    total = 0.0
    frames = 0
    while i < n-4:
        if b[i] != 0xFF or (b[i+1] & 0xE0) != 0xE0:
            i += 1; continue
        h = b[i+1]
        ver_bits = (h >> 3) & 3           # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
        layer = (h >> 1) & 3              # 1 = Layer III
        if ver_bits == 1 or layer != 1:
            i += 1; continue
        h2 = b[i+2]
        bi = (h2 >> 4) & 0xF
        si = (h2 >> 2) & 3
        pad = (h2 >> 1) & 1
        if bi in (0,15) or si == 3:
            i += 1; continue
        mpeg1 = ver_bits == 3
        br = BR[(1 if mpeg1 else 2, 3)][bi]
        sr = SR[ver_bits][si]
        if br == 0: i += 1; continue
        spf = 1152 if mpeg1 else 576
        flen = int((spf//8) * br * 1000 / sr) + pad
        if flen <= 4: i += 1; continue
        total += spf / sr
        frames += 1
        i += flen
    return total, frames

if __name__ == '__main__':
    for p in sys.argv[1:]:
        d, f = duration(p)
        print("%8.2f  %6d  %s" % (d, f, os.path.basename(p)))
