'''
代码修改自https://github.com/CjangCjengh/MoeGoe
'''

import logging
import random
import re
import sys

import commons
import utils
from models import SynthesizerTrn
from private import *
from scipy.io.wavfile import write
from text import text_to_sequence
from torch import LongTensor, no_grad
from my_tools import get_salt
import time

logging.getLogger('numba').setLevel(logging.WARNING)


def ex_print(text, escape=False):
    if escape:
        print(text.encode('unicode_escape').decode())
    else:
        print(text)


def get_text(text, hps, cleaned=False):
    if cleaned:
        text_norm = text_to_sequence(text, hps.symbols, [])
    else:
        text_norm = text_to_sequence(text, hps.symbols, hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm


def ask_if_continue():
    while True:
        answer = input('Continue? (y/n): ')
        if answer == 'y':
            break
        elif answer == 'n':
            sys.exit(0)


def print_speakers(speakers, escape=False):
    if len(speakers) > 100:
        return
    print('ID\tSpeaker')
    for id, name in enumerate(speakers):
        ex_print(str(id) + '\t' + name, escape)


def get_speaker_id(message):
    speaker_id = input(message)
    try:
        speaker_id = int(speaker_id)
    except:
        print(str(speaker_id) + ' is not a valid ID!')
        sys.exit(1)
    return speaker_id


def get_label_value(text, label, default, warning_name='value'):
    value = re.search(rf'\[{label}=(.+?)\]', text)
    if value:
        try:
            text = re.sub(rf'\[{label}=(.+?)\]', '', text, 1)
            value = float(value.group(1))
        except:
            print(f'Invalid {warning_name}!')
            sys.exit(1)
    else:
        value = default
    return value, text


def get_label(text, label):
    if f'[{label}]' in text:
        return True, text.replace(f'[{label}]', '')
    else:
        return False, text


def vits_tts(text: str, speaker: str):
    try:
        model = PTH_DICT[speaker]['pth_path']
        config = PTH_DICT[speaker]['config_path']

        hps_ms = utils.get_hparams_from_file(config)
        n_speakers = hps_ms.data.n_speakers if 'n_speakers' in hps_ms.data.keys(
        ) else 0
        n_symbols = len(hps_ms.symbols) if 'symbols' in hps_ms.keys() else 0
        # speakers = hps_ms.speakers if 'speakers' in hps_ms.keys() else ['0']
        # use_f0 = hps_ms.data.use_f0 if 'use_f0' in hps_ms.data.keys() else False
        emotion_embedding = hps_ms.data.emotion_embedding if 'emotion_embedding' in hps_ms.data.keys(
        ) else False

        net_g_ms = SynthesizerTrn(n_symbols,
                                  hps_ms.data.filter_length // 2 + 1,
                                  hps_ms.train.segment_size //
                                  hps_ms.data.hop_length,
                                  n_speakers=n_speakers,
                                  emotion_embedding=emotion_embedding,
                                  **hps_ms.model)
        _ = net_g_ms.eval()
        utils.load_checkpoint(model, net_g_ms)

        if n_symbols != 0:
            if not emotion_embedding:
                length_scale, text = get_label_value(
                    text, 'LENGTH', PTH_DICT[speaker]['speed'], 'length scale')
                noise_scale, text = get_label_value(text, 'NOISE', 0.667,
                                                    'noise scale')
                noise_scale_w, text = get_label_value(text, 'NOISEW', 0.8,
                                                      'deviation of noise')
                cleaned, text = get_label(text, 'CLEANED')

                stn_tst = get_text(text, hps_ms, cleaned=cleaned)

                speaker_id = 0

                stamp = int(time.time()) % 1000000
                wav_name = str(stamp) + '.wav'
                out_path = WAV_OUT + wav_name

                with no_grad():
                    x_tst = stn_tst.unsqueeze(0)
                    x_tst_lengths = LongTensor([stn_tst.size(0)])
                    sid = LongTensor([speaker_id])
                    audio = net_g_ms.infer(x_tst,
                                           x_tst_lengths,
                                           sid=sid,
                                           noise_scale=noise_scale,
                                           noise_scale_w=noise_scale_w,
                                           length_scale=length_scale)[0][
                                               0,
                                               0].data.cpu().float().numpy()

                write(out_path, hps_ms.data.sampling_rate, audio)
        return wav_name, 0
    except Exception as e:
        return str(e), 1


if __name__ == '__main__':
    stamp1 = int(time.time())
    a, b = vits_tts('雷光斩断过往，你我走向歧路。我将坠入黑暗，换你回到光明。雷神语音，已就位。', 'nahida')
    stamp2 = int(time.time())
    print(a, b)
    print(stamp2 - stamp1)
