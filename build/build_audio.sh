#!/bin/bash
# VO conform + minimal sound design.
#
# The bed is deliberately almost nothing: three soft low impacts on the
# three beats the film turns on. No music -- this house style doesn't have
# any, and a synthesised drone would sit under the VO doing no work on the
# phone speakers these actually get watched on.
set -e
cd "$(dirname "$0")"

VO=media/vo.mp3

# 1. clean + two-pass loudness to the -14 LUFS streaming target
MEAS=$(ffmpeg -hide_banner -nostats -i "$VO" \
  -af "highpass=f=75,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180,
       loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" \
  -f null - 2>&1 | sed -n '/^{/,/^}/p')
gv () { echo "$MEAS" | grep "\"$1\"" | sed 's/.*: *"\([^"]*\)".*/\1/'; }
I=$(gv input_i); TP=$(gv input_tp); LRA=$(gv input_lra); TH=$(gv input_thresh)
echo "VO measured: I=$I TP=$TP LRA=$LRA"

ffmpeg -v error -y -i "$VO" \
  -af "highpass=f=75,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180,
       loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:linear=true,
       aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo" \
  media/vo_clean.wav

# 2. one impact: a body tone under a filtered noise tick.
# NB ffmpeg's sine source peaks at -18dBFS, not 0, and the mono->stereo
# aformat costs a further 3dB -- hence the +12dB makeup on the tone.
# The decay is a real exp() envelope on the volume filter -- afade's exp
# curve starts collapsing at sample 0 and leaves nothing but a -32dB tick.
mkimpact () {  # $1=out  $2=freq  $3=dur  $4=decay  $5=gain
  ffmpeg -v error -y \
    -f lavfi -i "sine=frequency=$2:duration=$3:sample_rate=48000" \
    -f lavfi -i "anoisesrc=duration=$3:sample_rate=48000:amplitude=0.6:color=brown" \
    -filter_complex "[0:a]volume=4.0,volume='exp(-t*$4)':eval=frame[t];
                     [1:a]lowpass=f=500,highpass=f=85,
                          volume='exp(-t*18)':eval=frame,volume=1.8[n];
                     [t][n]amix=inputs=2:normalize=0,
                     afade=t=in:st=0:d=0.006,
                     volume=$5,
                     aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo" \
    "$1"
}
mkimpact media/imp_a.wav 96  0.55 6.0 0.95     # DEADBEAT
mkimpact media/imp_b.wav 76  0.60 5.5 1.05     # 24.9% APR
mkimpact media/imp_c.wav 128 0.75 4.5 0.70     # BALANCE £0.00

# 3. place them on the beats and mix under the VO
ffmpeg -v error -y \
  -i media/vo_clean.wav -i media/imp_a.wav -i media/imp_b.wav -i media/imp_c.wav \
  -filter_complex "
    [1:a]adelay=4120|4120[a];
    [2:a]adelay=25640|25640[b];
    [3:a]adelay=50320|50320[c];
    [a][b][c]amix=inputs=3:normalize=0,volume=0.5[sfx];
    [0:a][sfx]amix=inputs=2:normalize=0:duration=first[m];
    [m]alimiter=limit=0.94:level=false,
       apad,atrim=0:58.5,
       afade=t=out:st=58.1:d=0.4,
       aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[out]" \
  -map "[out]" media/mix.wav

# clean VO-only master of the same length, in case the impacts aren't wanted
ffmpeg -v error -y -i media/vo_clean.wav \
  -af "alimiter=limit=0.94:level=false,apad,atrim=0:58.5,afade=t=out:st=58.1:d=0.4,
       aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo" \
  media/mix_nosfx.wav

for f in media/mix.wav media/mix_nosfx.wav; do
  printf "%-22s %ss  " "$f" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f)"
  ffmpeg -hide_banner -nostats -i $f -af ebur128=framelog=quiet -f null - 2>&1 | tail -6 | tr -s ' \n' ' '
  echo
done
