#!/usr/bin/env python3
#            _    __           
#           | |  / _|          
#  _ __ ___ | |_| |_ _ __  ___ 
# | '_ ` _ \| __|  _| '_ \/ __|
# | | | | | | |_| | | |_) \__ \
# |_| |_| |_|\__|_| | .__/|___/
#                   | |        
#                   |_|        
# mtfps.py - Max Tolles FfProbe Skript
# https://patorjk.com/software/taag/#p=display&f=Big&t=mtfps

import json
import subprocess
import sys
import os

def probe(filename):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams']
    cmd.append(filename)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode == 0:
        data = json.loads(out)
        video_info = {}
        audio_langs = []
        for stream in data['streams']:
            # Video Info
            # only first video stream should be used, other video streams can contain misleading info
            if stream['codec_type'] == 'video' and video_info == {}:
                # convert print statements to dictionary assignments
                video_info['codec_long_name'] = stream['codec_long_name']
                video_info['resolution'] = (stream['width'], stream['height'])
                
                #if [ "${COLORSPACE}" = "bt2020nc" ] && [ "${COLORTRANSFER}" = "smpte2084" ] && [ "${COLORPRIMARIES}" = "bt2020" ]; 
                # from https://www.reddit.com/r/ffmpeg/comments/kjwxm9/how_to_detect_if_video_is_hdr_or_sdr_batch_script/
                try:
                    if stream['color_space'] == 'bt2020nc' and stream['color_transfer'] == 'smpte2084' and stream['color_primaries'] == 'bt2020':
                        video_info['HDR'] = 'Yes'
                    else:
                        video_info['HDR'] = 'No'
                except KeyError:
                    video_info['HDR'] = 'Probably not (missing metadata)'

            # Audio Info
            if stream['codec_type'] == 'audio':
                audio_langs.append(stream['tags']['language'])
        #print(json.dumps(data, indent=4))
        return video_info, audio_langs
    else:
        return None, None

def info_printer(video_info, audio_langs):
    print('Video Info:')
    print('  Codec: {}'.format(video_info['codec_long_name']))
    print('  Resolution: {}x{}'.format(*video_info['resolution']))
    print('  HDR: {}'.format(video_info['HDR']))
    print('Audio Languages:')
    for lang in audio_langs:
        print('  {}'.format(lang))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage: mtfps.py <filename or directory>'.format(sys.argv[0]))
        sys.exit(1)

    elif len(sys.argv) == 2:
        # check if argument is file or directory
        isfile = os.path.isfile(sys.argv[1])
        if isfile:
            video_info, audio_langs = probe(sys.argv[1])
            if video_info is not None and audio_langs is not None:
                info_printer(video_info, audio_langs)
            else:
                print('Error: Unable to probe {} (are you sure this is a video file?)'.format(sys.argv[1]))
                sys.exit(1)
        else:
            for root, dirs, files in os.walk(sys.argv[1]):
                for file in files:
                    if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.webm'):
                        video_info, audio_langs = probe(os.path.join(root, file))
                        if video_info is not None and audio_langs is not None:
                            print('File: {}'.format(file))
                            info_printer(video_info, audio_langs)
                            print()
                        else:
                            print('Error: Unable to probe {} (are you sure this is a video file?)'.format(file))
                            sys.exit(1)
    elif len(sys.argv) == 3: # special flag added
        if sys.argv[1] == "--max-mode": # only the largest file in the first level of each folder gets probed
            for item in os.listdir(sys.argv[2]):
                if os.path.isdir(os.path.join(sys.argv[2], item)):
                    files = os.listdir(os.path.join(sys.argv[2], item))
                    largest_file = max(files, key=lambda x: os.path.getsize(os.path.join(sys.argv[2], item, x)))
                    video_info, audio_langs = probe(os.path.join(sys.argv[2], item, largest_file))
                    if video_info is not None and audio_langs is not None:
                        # print folder name instead of file name because folder name is prettier
                        print('Folder: {}'.format(item))
                        info_printer(video_info, audio_langs)
                        print()
                    else:
                        print('Error: Unable to probe {} (are you sure this is a video file?)'.format(largest_file))
                        sys.exit(1)
            
    else:
        print('Usage: mtfps.py <filename or directory>'.format(sys.argv[0]))
        sys.exit(1)

