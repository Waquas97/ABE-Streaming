#!/usr/bin/env python3
"""
Author:            Parikshit Juluri
Contact:           pjuluri@umkc.edu
Testing:
    import dash_client
    mpd_file = <MPD_FILE>
    dash_client.playback_duration(mpd_file, 'http://198.248.242.16:8005/')

    From commandline:
    python dash_client.py -m "http://198.248.242.16:8006/media/mpd/x4ukwHdACDw.mpd" -p "all"
    python dash_client.py -m "http://127.0.0.1:8000/media/mpd/x4ukwHdACDw.mpd" -p "basic"
    https://github.com/jancc/AStream
    https://stackoverflow.com/questions/57366845/how-to-concatenate-videos-in-ffmpeg-with-different-attributes/57367243#57367243

    ffmpeg -y -copyts -start_at_zero -noaccurate_seek -i /home/kulkarnu/experiments/transmitted_videos/video4/jellyfish6-crf10-streaming.mp4 \
    -keyint_min 48 -g 48 -frag_type duration -frag_duration 0.4 -sc_threshold 0 -c:v libx264 \
    -profile:v main -crf 10 -c:a aac -ar 48000 -f dash -dash_segment_type mp4 \
    -map v:0 -movflags frag_keyframe -s:0 426x240 \
    -map v:0 -movflags frag_keyframe -s:1 640x360 \
    -map v:0 -movflags frag_keyframe -s:2 854x480 \
    -map v:0 -movflags frag_keyframe -s:3 1024x600 \
    -map v:0 -movflags frag_keyframe -s:4 1280x720 \
    -map v:0 -movflags frag_keyframe -s:5 1600x900 \
    -map v:0 -movflags frag_keyframe -s:6 1920x1080 \
    -map 0:a \
    -init_seg_name chunk\$RepresentationID\$-index.mp4 -media_seg_name chunk\$RepresentationID\$-\$Number%05d\$.mp4 \
    -use_template 0 -use_timeline 0 \
    -seg_duration 4 -adaptation_sets "id=0,streams=v id=1,streams=a" \
    dash.mpd
"""

import read_mpd
import urllib.parse
import urllib.request, urllib.error, urllib.parse
import random
import os
import sys
import errno
import ssl
import timeit
import http.client
import io
import json
import shutil
import subprocess
import pandas as pd
from datetime import datetime
from string import ascii_letters, digits
from argparse import ArgumentParser
from multiprocessing import Process, Queue
from collections import defaultdict
from adaptation import basic_dash, basic_dash2, weighted_dash, netflix_dash
from adaptation.adaptation import WeightedMean
import config_dash
from configure_log_file import configure_log_file, write_json
import dash_buffer
import time

# Constants
DEFAULT_PLAYBACK = 'NETFLIX'
DOWNLOAD_CHUNK = 1024
COMBINE_SEGMENTS = 0

# Globals for arg parser with the default values
# Not sure if this is the correct way ....
MPD = None
LIST = False
PLAYBACK = DEFAULT_PLAYBACK
DOWNLOAD = False
SEGMENT_LIMIT = None


class DashPlayback:
    """
    Audio[bandwidth] : {duration, url_list}
    Video[bandwidth] : {duration, url_list}
    """

    def __init__(self):

        self.min_buffer_time = None
        self.playback_duration = None
        self.audio = dict()
        self.video = dict()


def get_mpd(url):
    """ Module to download the MPD from the URL and save it to file"""
    #print(url)
    try:
        if url.find('https://') == 0:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            connection = urllib.request.urlopen(url, timeout=10, context=ctx)
        else:
            connection = urllib.request.urlopen(url, timeout=10)
    except urllib.error.HTTPError as error:
        config_dash.LOG.error("Unable to download MPD file HTTP Error: %s" %
                              error.code)
        return None
    except urllib.error.URLError:
        error_message = "URLError. Unable to reach Server.Check if Server active"
        config_dash.LOG.error(error_message)
        print(error_message)
        return None
    except IOError as xxx_todo_changeme:
        http.client.HTTPException = xxx_todo_changeme
        message = "Unable to , file_identifierdownload MPD file HTTP Error."
        config_dash.LOG.error(message)
        return None

    mpd_data = connection.read()
    connection.close()
    config_dash.LOG.info("Downloaded the MPD file")
    return io.BytesIO(mpd_data)


def get_bandwidth(data, duration):
    """ Module to determine the bandwidth for a segment
    download"""
    return data * 8 / duration


def get_domain_name(url):
    """ Module to obtain the domain name from the URL
        From : http://stackoverflow.com/questions/9626535/get-domain-name-from-url
    """
    parsed_uri = urllib.parse.urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain


def id_generator(id_size=6):
    """ Module to create a random string with uppercase 
        and digits.
    """
    return 'TEMP_' + ''.join(
        random.choice(ascii_letters + digits) for _ in range(id_size))


def download_segment(segment_url, dash_folder, index_file=None):
    """ Module to download the segment """
    parsed_uri = urllib.parse.urlparse(segment_url)
    segment_path = '{uri.path}'.format(uri=parsed_uri)
    while segment_path.startswith('/'):
        segment_path = segment_path[1:]
    segment_filename = os.path.join(dash_folder,
                                    os.path.basename(segment_path))
    segment_temp_filename = os.path.join(
        dash_folder, "temp" + os.path.basename(segment_path))
    make_sure_path_exists(os.path.dirname(segment_filename))

    #https://stackoverflow.com/a/42873372/12865444
    num_retries = 0
    while num_retries < 1:
        num_retries = num_retries + 1
        bashCommand = "curl -k --retry 5 -o {} -s -w 'total_time=%{{{}}}\\nsize_download=%{{{}}}\\nhttp_code=%{{{}}}\\n' {}".format(
            segment_filename, "time_total", "size_download", "http_code",
            segment_url)
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        segment_download_time = float(output.decode().split('\n')[0].replace(
            "\r", '').split("=")[-1])
        segment_size = int(output.decode().split('\n')[1].replace(
            "\r", '').split("=")[-1])
        http_code = int(output.decode().split('\n')[2].replace(
            "\r", '').split("=")[-1])
        if not os.path.isfile(segment_filename):
            config_dash.LOG.info(
                "Basic-DASH: FileNotFoundError during segment download - {}. # retry = {}"
                .format(segment_filename, num_retries))
            if num_retries == 5:
                raise FileNotFoundError(
                    "File {} was not found!".format(segment_filename))
            continue
        if http_code != 200:
            config_dash.LOG.info(
                "Basic-DASH: ValueError during segment download; received http code = {}. # retry = {}"
                .format(http_code, num_retries))
            if num_retries == 5:
                raise ValueError(
                    "HTTP Response code is not 200. It is {}".format(
                        http_code))
            continue
        break

    #print(segment_download_time, segment_size, http_code)

    if COMBINE_SEGMENTS:
        start_time = timeit.default_timer()
        segment_file_handle = open(segment_filename, 'wb')
        if index_file != None:
            fo = open(index_file, "rb")
            shutil.copyfileobj(fo, segment_file_handle)
            fo.close()
        segment_file_handle.close()
        with open(segment_filename,
                  "ab") as myfile, open(segment_temp_filename, "rb") as file2:
            myfile.write(file2.read())
        try:
            os.remove(segment_temp_filename)
        except:
            pass
        #fio = timeit.default_timer() - start_time
        #print("fio",fio)
        #print "segment size = {}".format(segment_size)
        #print "segment filename = {}".format(segment_filename)

    return segment_size, segment_filename, segment_download_time


def get_media_all(domain, media_info, file_identifier, done_queue):
    """ Download the media from the list of URL's in media
    """
    bandwidth, media_dict = media_info
    media = media_dict[bandwidth]
    media_start_time = timeit.default_timer()
    for segment in [media.initialization] + media.url_list:
        start_time = timeit.default_timer()
        segment_url = urllib.parse.urljoin(domain, segment)
        _, segment_file = download_segment(segment_url, file_identifier)
        elapsed = timeit.default_timer() - start_time
        if segment_file:
            done_queue.put((bandwidth, segment_url, elapsed))
    media_download_time = timeit.default_timer() - media_start_time
    done_queue.put((bandwidth, 'STOP', media_download_time))
    return None


def make_sure_path_exists(path):
    """ Module to make sure the path exists if not create it
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def print_representations(dp_object):
    """ Module to print the representations"""
    print("The DASH media has the following video representations/bitrates")
    for bandwidth in dp_object.video:
        print(bandwidth)


def compute_qoe(lamda=1,
                mu=3,
                bitrates=[],
                my_quality=0,
                prev_quality=0,
                rebuffer_time=0):
    # Pensieve - https://github.com/hongzimao/pensieve/blob/master/dash_client/player_code_noMPC/app/js/streaming/BufferController.js
    # https://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p325.pdf
    # Users’ QoE preferences: We compared the performance of the algorithms under 3 sets of QoE weights:
    # “Balanced” (λ = 1, μ = μs = 3000)
    # “Avoid Instability” (λ = 3, μ = μs = 3000)
    # “Avoid Rebuffering” (λ = 1, μ = μs = 6000)
    # Similar to equation 5 of https://doi.org/10.1186/s13174-021-00133-y
    # bitrate is in Kbps and rebuffer time is in ms
    my_bitrate = (bitrates[my_quality]) / 1000
    prev_bitrate = (bitrates[prev_quality]) / 1000
    instability = abs(my_bitrate - prev_bitrate)
    qoe = my_bitrate - (lamda * instability) - (mu * rebuffer_time * 1000)
    return qoe


def start_playback_smart(dp_object,
                         domain,
                         playback_type=None,
                         download=False,
                         video_segment_duration=None,
                         file_identifier=""):
    """ Module that downloads the MPD-FIle and download
        all the representations of the Module to download
        the MPEG-DASH media.
        Example: start_playback_smart(dp_object, domain, "SMART", DOWNLOAD, video_segment_duration)

        :param dp_object:       The DASH-playback object
        :param domain:          The domain name of the server (The segment URLS are domain + relative_address)
        :param playback_type:   The type of playback
                                1. 'BASIC' - The basic adapataion scheme
                                2. 'SARA' - Segment Aware Rate Adaptation
                                3. 'NETFLIX' - Buffer based adaptation used by Netflix
        :param download: Set to True if the segments are to be stored locally (Boolean). Default False
        :param video_segment_duration: Playback duratoin of each segment
        :return:
    """
    # Initialize the DASH buffer
    dash_player = dash_buffer.DashPlayer(dp_object.playback_duration,
                                         video_segment_duration)
    dash_player.start()
    # A folder to save the segments in
    if file_identifier == "":
        file_identifier = id_generator()
    config_dash.LOG.info("The segments are stored in %s" % file_identifier)
    dp_list = defaultdict(defaultdict)
    index_dict = {}
    #with open("dp_obj.txt", "w") as f:
    #    for i, d in dp_object.video.items():
    #        f.write("{}: {}\n".format(i, d))
    # Creating a Dictionary of all that has the URLs for each segment and different bitrates
    for brcount, bitrate in enumerate(dp_object.video):
        index_dict[str(bitrate)] = {}
        index_dict[str(bitrate)]["index_downloaded"] = 0
        # Getting the URL list for each bitrate
        dp_object.video[bitrate] = read_mpd.get_url_list(
            dp_object, video_segment_duration, bitrate, brcount)

        if "$Bandwidth$" in dp_object.video[bitrate].initialization:
            dp_object.video[bitrate].initialization = dp_object.video[
                bitrate].initialization.replace("$Bandwidth$", str(bitrate))

        #media_urls = [dp_object.video[bitrate].initialization] + dp_object.video[bitrate].url_list
        media_urls = dp_object.video[bitrate].url_list
        #print("media urls",media_urls)
        for segment_count, segment_url in enumerate(
                media_urls, dp_object.video[bitrate].start):
            # segment_duration = dp_object.video[bitrate].segment_duration
            #print "segment url"
            #print segment_url
            dp_list[segment_count][bitrate] = segment_url
    #print("dp_list - ",dp_list)
    #print("index_dict - ",index_dict)
    bitrates = list(dp_object.video.keys())
    bitrates.sort()
    average_dwn_time = 0
    segment_files = []
    # For basic adaptation
    previous_segment_times = []
    recent_download_sizes = []
    weighted_mean_object = None
    current_bitrate = bitrates[0]
    previous_bitrate = None
    total_downloaded = 0
    # Delay in terms of the number of segments
    delay = 0
    segment_duration = 0
    segment_size = segment_download_time = None
    # Netflix Variables
    netflix_rate_map = None
    average_segment_sizes = get_average_segment_sizes(dp_object)
    netflix_state = "INITIAL"
    qoe_index = 1
    rebuffer_times = []
    qualities = []
    qoes = []
    # Start playback of all the segments
    for segment_number, segment in enumerate(
            dp_list, dp_object.video[current_bitrate].start):
        config_dash.LOG.info(" {}: Processing the segment {}".format(
            playback_type.upper(), segment_number))
        dash_player.current_segment = segment_number
        config_dash.JSON_HANDLE['playback_info']['interruptions'][
            'events'].append([0, 0])
        if not previous_bitrate:
            previous_bitrate = current_bitrate
        if SEGMENT_LIMIT:
            if not dash_player.segment_limit:
                dash_player.segment_limit = int(SEGMENT_LIMIT)
            if segment_number > int(SEGMENT_LIMIT):
                config_dash.LOG.info("Segment limit reached")
                break
        #print("segment_number ={}".format(segment_number))
        #print("dp_object.video[bitrate].start={}".format(dp_object.video[bitrate].start))
        if segment_number == dp_object.video[bitrate].start:
            current_bitrate = bitrates[0]
        else:
            if playback_type.upper() == "BASIC":
                current_bitrate, average_dwn_time = basic_dash2.basic_dash2(
                    segment_number, bitrates, average_dwn_time,
                    recent_download_sizes, previous_segment_times,
                    current_bitrate)

                if dash_player.buffer.qsize() > config_dash.BASIC_THRESHOLD:
                    delay = dash_player.buffer.qsize(
                    ) - config_dash.BASIC_THRESHOLD
                config_dash.LOG.info(
                    "Basic-DASH: Selected {} for the segment {}".format(
                        current_bitrate, segment_number + 1))
            elif playback_type.upper() == "SMART":
                if not weighted_mean_object:
                    weighted_mean_object = WeightedMean(
                        config_dash.SARA_SAMPLE_COUNT)
                    config_dash.LOG.debug(
                        "Initializing the weighted Mean object")
                # Checking the segment number is in acceptable range
                if segment_number < len(
                        dp_list) - 1 + dp_object.video[bitrate].start:
                    try:
                        current_bitrate, delay = weighted_dash.weighted_dash(
                            bitrates, dash_player,
                            weighted_mean_object.weighted_mean_rate,
                            current_bitrate,
                            get_segment_sizes(dp_object, segment_number + 1))
                    except IndexError as e:
                        config_dash.LOG.error(e)

            elif playback_type.upper() == "NETFLIX":
                config_dash.LOG.info("Playback is NETFLIX")
                # Calculate the average segment sizes for each bitrate
                if segment_number <= len(dp_list):
                    try:
                        if segment_size and segment_download_time:
                            segment_download_rate = segment_size / segment_download_time
                        else:
                            segment_download_rate = 0
                        current_bitrate, netflix_rate_map, netflix_state = netflix_dash.netflix_dash(
                            bitrates, dash_player, segment_download_rate,
                            current_bitrate, average_segment_sizes,
                            netflix_rate_map, netflix_state)
                        config_dash.LOG.info(
                            "NETFLIX: Next bitrate = {}".format(
                                current_bitrate))
                    except IndexError as e:
                        config_dash.LOG.error(e)
                else:
                    config_dash.LOG.critical(
                        "Completed segment playback for Netflix")
                    break

                # If the buffer is full wait till it gets empty by 1 segment so that we can download the next one
                # Reference - https://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p325.pdf:
                # In this paper we assume that the player immediately starts to download chunk k + 1 as soon as chunk k is downloaded.
                # The one exception is when the buffer is full, the player waits for the buffer to reduce to a level which allows chunk k to be appended
                # Also as per Figure 6 from http://tiny-tera.stanford.edu/~nickm/papers/sigcomm2014-video.pdf
                # f(B) should be designed to en- sure a chunk can always be downloaded before the buffer shrinks into the reservoir area.
                if dash_player.buffer.qsize(
                ) >= config_dash.NETFLIX_BUFFER_SIZE:
                    delay = (dash_player.buffer.qsize() -
                             config_dash.NETFLIX_BUFFER_SIZE + 1)
                    config_dash.LOG.info("NETFLIX: delay = {} seconds".format(
                        delay * segment_duration))
            else:
                config_dash.LOG.error(
                    "Unknown playback type:{}. Continuing with basic playback".
                    format(playback_type))
                current_bitrate, average_dwn_time = basic_dash.basic_dash(
                    segment_number, bitrates, average_dwn_time,
                    segment_download_time, current_bitrate)
        segment_path = dp_list[segment][current_bitrate]
        #print   "domain"
        #print domain
        #print "segment"
        #print segment
        #print "current bitrate"
        #print current_bitrate
        #print segment_path
        segment_url = urllib.parse.urljoin(domain, segment_path)
        #print "segment url"
        #print segment_url
        config_dash.LOG.info("{}: Segment URL = {}".format(
            playback_type.upper(), segment_url))
        if delay:
            delay_start = time.time()
            config_dash.LOG.info("SLEEPING for {}seconds ".format(
                delay * segment_duration))
            while time.time() - delay_start < (delay * segment_duration):
                time.sleep(1)
            delay = 0
            config_dash.LOG.debug("SLEPT for {}seconds ".format(time.time() -
                                                                delay_start))
        segment_download_time = 0
        try:
            #print 'url'
            #print segment_url
            #print 'file'
            #print file_identifier
            if not index_dict[str(int(current_bitrate))]["index_downloaded"]:
                index_segment_url = urllib.parse.urljoin(
                    domain, dp_object.video[current_bitrate].initialization)
                _, index_segment_filename, _ = download_segment(
                    index_segment_url, file_identifier)
                index_dict[str(int(
                    current_bitrate))]["index_file"] = index_segment_filename
                config_dash.LOG.info("{}: Downloaded index segment {}".format(
                    playback_type.upper(), index_segment_url))
                index_dict[str(int(current_bitrate))]["index_downloaded"] = 1
            segment_size, segment_filename, segment_download_time = download_segment(
                segment_url,
                file_identifier,
                index_file=index_dict[str(int(current_bitrate))]["index_file"])
            config_dash.LOG.info("{}: Downloaded segment {}".format(
                playback_type.upper(), segment_url))
        except IOError as e:
            config_dash.LOG.error("Unable to save segment %s" % e)
            return None
        previous_segment_times.append(segment_download_time)
        recent_download_sizes.append(segment_size)
        # Updating the JSON information
        segment_name = os.path.split(segment_url)[1]
        if "segment_info" not in config_dash.JSON_HANDLE:
            config_dash.JSON_HANDLE["segment_info"] = list()
        config_dash.JSON_HANDLE["segment_info"].append(
            (segment_name, current_bitrate, segment_size,
             segment_download_time))
        total_downloaded += segment_size
        config_dash.LOG.info(
            "{} : The total downloaded = {}, segment_size = {}, segment_number = {}"
            .format(playback_type.upper(), total_downloaded, segment_size,
                    segment_number))
        if playback_type.upper() == "SMART" and weighted_mean_object:
            weighted_mean_object.update_weighted_mean(segment_size,
                                                      segment_download_time)

        segment_info = {
            'playback_length': video_segment_duration,
            'size': segment_size,
            'bitrate': current_bitrate,
            'data': segment_filename,
            'URI': segment_url,
            'segment_number': segment_number
        }

        # Real-time QoE Computing
        my_quality = bitrates.index(current_bitrate)
        qualities.append(my_quality)
        if segment_number > config_dash.MAX_BUFFER_SIZE:
            if qoe_index == 1:
                rebuffer_time = dash_player.initial_wait
                prev_quality = qualities[qoe_index - 1]
            else:
                rebuffer_time = (
                    config_dash.JSON_HANDLE['playback_info']['interruptions']
                    ['events'][qoe_index - 1][1] -
                    config_dash.JSON_HANDLE['playback_info']['interruptions']
                    ['events'][qoe_index - 1][0])
                prev_quality = qualities[qoe_index - 2]
            rebuffer_times.append(rebuffer_time)
            config_dash.LOG.info("Rebuffer time for Segment # {} is {}".format(
                qoe_index, rebuffer_time))
            qoe = compute_qoe(bitrates=bitrates,
                              my_quality=qualities[qoe_index - 1],
                              prev_quality=prev_quality,
                              rebuffer_time=rebuffer_time)
            qoes.append(qoe)
            config_dash.LOG.info("QoE for Segment # {} is {}".format(
                qoe_index, qoe))
            qoe_index = qoe_index + 1

        segment_duration = segment_info['playback_length']
        dash_player.write(segment_info)
        segment_files.append(segment_filename)
        config_dash.LOG.info(
            "Downloaded %s. Size = %s in %s seconds" %
            (segment_url, segment_size, str(segment_download_time)))
        if previous_bitrate:
            if previous_bitrate < current_bitrate:
                config_dash.JSON_HANDLE['playback_info']['up_shifts'] += 1
            elif previous_bitrate > current_bitrate:
                config_dash.JSON_HANDLE['playback_info']['down_shifts'] += 1
            previous_bitrate = current_bitrate

    # QoEs of last few segments
    while qoe_index <= len(dp_list):
        rebuffer_time = (config_dash.JSON_HANDLE['playback_info']
                         ['interruptions']['events'][qoe_index - 1][1] -
                         config_dash.JSON_HANDLE['playback_info']
                         ['interruptions']['events'][qoe_index - 1][0])
        rebuffer_times.append(rebuffer_time)
        qoe = compute_qoe(bitrates=bitrates,
                          my_quality=qualities[qoe_index - 1],
                          prev_quality=qualities[qoe_index - 2],
                          rebuffer_time=rebuffer_time)
        qoes.append(qoe)
        config_dash.LOG.info("QoE for Segment # {} is {}".format(
            qoe_index, qoe))
        qoe_index = qoe_index + 1

    # waiting for the player to finish playing
    while dash_player.playback_state not in dash_buffer.EXIT_STATES:
        time.sleep(1)
    if not download:
        clean_files(file_identifier)

    #save qoe data to csv file
    df_cols = [
        "segment_num", "unix_timestamp", "epoch_time", "current_playback_time",
        "current_buffer_size", "quality", "bitrate", "interruption", "qoe"
    ]
    unix_timestamps = []
    with open(dash_player.log_file, "r") as fp:
        read_lines = [
            line for line in fp if "Reading the segment number" in line
        ]
    for line in read_lines:
        datets = line.split(" - ")[0]
        pdate = datetime.strptime(datets, '%Y-%m-%d %H:%M:%S,%f')
        unix_timestamps.append(pdate.timestamp())
    dash_buffer_csv = pd.read_csv(dash_player.buffer_log_file)
    dash_buffer_csv.dropna(inplace=True)
    df_play = dash_buffer_csv[dash_buffer_csv['Action'].str.contains(
        "Playing")]
    df_play = df_play.reset_index(drop=True)
    epoch_times = df_play["EpochTime"].tolist()
    current_playback_time = df_play["CurrentPlaybackTime"].tolist()
    current_buffer_sizes = df_play["CurrentBufferSize"].tolist()
    bit_rates = df_play["Bitrate"].tolist()
    segment_nums = [x for x in range(1, len(dp_list) + 1)]
    df = pd.DataFrame({
        df_cols[0]: segment_nums,
        df_cols[1]: unix_timestamps,
        df_cols[2]: epoch_times,
        df_cols[3]: current_playback_time,
        df_cols[4]: current_buffer_sizes,
        df_cols[5]: qualities,
        df_cols[6]: bit_rates,
        df_cols[7]: rebuffer_times,
        df_cols[8]: qoes,
    })
    max_qoe = bitrates[-1] / 1000
    df["nqoe"] = df[df_cols[8]] / max_qoe
    config_dash.LOG.info("Average QoE = {}".format(df[df_cols[7]].mean()))
    config_dash.LOG.info("Average n-QoE = {}".format(df["nqoe"].mean()))
    df.to_csv(config_dash.QOE_CSV_FILE, index=False)


def get_segment_sizes(dp_object, segment_number):
    """ Module to get the segment sizes for the segment_number
    :param dp_object:
    :param segment_number:
    :return:
    """
    segment_sizes = dict([
        (bitrate, dp_object.video[bitrate].segment_sizes[segment_number])
        for bitrate in dp_object.video
    ])
    config_dash.LOG.debug("The segment sizes of {} are {}".format(
        segment_number, segment_sizes))
    return segment_sizes


def get_average_segment_sizes(dp_object):
    """
    Module to get the avearge segment sizes for each bitrate
    :param dp_object:
    :return: A dictionary of aveage segment sizes for each bitrate
    """
    average_segment_sizes = dict()
    for bitrate in dp_object.video:
        num_segments = len(dp_object.video[bitrate].url_list)
        total_video_duration = dp_object.playback_duration
        total_size = bitrate * total_video_duration
        segment_size = total_size / num_segments
        average_segment_sizes[bitrate] = segment_size * 8 / 1000
        if 0:
            segment_sizes = dp_object.video[bitrate].segment_sizes
            segment_sizes = [float(i) for i in segment_sizes]
            try:
                average_segment_sizes[bitrate] = sum(segment_sizes) / len(
                    segment_sizes)
            except ZeroDivisionError:
                average_segment_sizes[bitrate] = 0
    config_dash.LOG.info("The avearge segment size for is {}".format(
        list(average_segment_sizes.items())))
    return average_segment_sizes


def clean_files(folder_path):
    """
    :param folder_path: Local Folder to be deleted
    """
    if os.path.exists(folder_path):
        try:
            for video_file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, video_file)
                if file_path.endswith(".mp4") and os.path.isfile(file_path):
                    os.unlink(file_path)
            #os.rmdir(folder_path)
        except OSError as e:
            config_dash.LOG.info(
                "Unable to delete the mp4 files in folder {}. {}".format(
                    folder_path, e))
        config_dash.LOG.info(
            "Deleted the mp4 files from folder '{}'".format(folder_path))


def start_playback_all(dp_object, domain):
    """ Module that downloads the MPD-FIle and download all the representations of 
        the Module to download the MPEG-DASH media.
    """
    # audio_done_queue = Queue()
    video_done_queue = Queue()
    processes = []
    file_identifier = id_generator(6)
    config_dash.LOG.info("File Segments are in %s" % file_identifier)
    # for bitrate in dp_object.audio:
    #     # Get the list of URL's (relative location) for the audio
    #     dp_object.audio[bitrate] = read_mpd.get_url_list(bitrate, dp_object.audio[bitrate],
    #                                                      dp_object.playback_duration)
    #     # Create a new process to download the audio stream.
    #     # The domain + URL from the above list gives the
    #     # complete path
    #     # The fil-identifier is a random string used to
    #     # create  a temporary folder for current session
    #     # Audio-done queue is used to exchange information
    #     # between the process and the calling function.
    #     # 'STOP' is added to the queue to indicate the end
    #     # of the download of the sesson
    #     process = Process(target=get_media_all, args=(domain, (bitrate, dp_object.audio),
    #                                                   file_identifier, audio_done_queue))
    #     process.start()
    #     processes.append(process)

    for bitrate in dp_object.video:
        dp_object.video[bitrate] = read_mpd.get_url_list(
            bitrate, dp_object.video[bitrate], dp_object.playback_duration,
            dp_object.video[bitrate].segment_duration)
        # Same as download audio
        process = Process(target=get_media_all,
                          args=(domain, (bitrate, dp_object.video),
                                file_identifier, video_done_queue))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()
    count = 0
    for queue_values in iter(video_done_queue.get, None):
        bitrate, status, elapsed = queue_values
        if status == 'STOP':
            config_dash.LOG.critical("Completed download of %s in %f " %
                                     (bitrate, elapsed))
            count += 1
            if count == len(dp_object.video):
                # If the download of all the videos is done the stop the
                config_dash.LOG.critical(
                    "Finished download of all video segments")
                break


def create_arguments(parser):
    """ Adding arguments to the parser """
    parser.add_argument('-m', '--MPD', help="Url to the MPD File")
    parser.add_argument('-l',
                        '--LIST',
                        action='store_true',
                        help="List all the representations")
    parser.add_argument('-p',
                        '--PLAYBACK',
                        default=DEFAULT_PLAYBACK,
                        help="Playback type (basic, sara, netflix, or all)")
    parser.add_argument('-n',
                        '--SEGMENT_LIMIT',
                        default=SEGMENT_LIMIT,
                        help="The Segment number limit")
    parser.add_argument('-d',
                        '--DOWNLOAD',
                        action='store_true',
                        default=False,
                        help="Keep the video files after playback")
    parser.add_argument('-o',
                        '--LOG_FOLDER',
                        default="log",
                        help="Logs and download directory")
    parser.add_argument('-q',
                        '--QUIC',
                        action='store_true',
                        default=False,
                        help="Use QUIC as protocol")
    parser.add_argument('-mp',
                        '--MP',
                        action='store_true',
                        default=False,
                        help="Activate multipath in QUIC")
    parser.add_argument('-nka',
                        '--NO_KEEP_ALIVE',
                        action='store_true',
                        default=False,
                        help="Keep alive connection to Server")
    parser.add_argument(
        '-s',
        '--SCHEDULER',
        default='lowRTT',
        help="Scheduler in multipath usage (lowRTT, RR, redundant)")
    parser.add_argument('--fec',
                        action='store_true',
                        default=False,
                        help='Enable FEC')
    parser.add_argument('--fecn',
                        default=4,
                        help='Number of data symbols in a FEC block')


def main():
    """ Main Program wrapper """
    # configure the log file
    # Create arguments
    parser = ArgumentParser(description='Process Client parameters')
    create_arguments(parser)
    args = parser.parse_args()
    globals().update(vars(args))
    LOG_FOLDER = args.LOG_FOLDER
    config_dash.init(LOG_FOLDER=LOG_FOLDER)
    configure_log_file(playback_type=PLAYBACK.lower())
    config_dash.JSON_HANDLE['playback_type'] = PLAYBACK.lower()
    config_dash.JSON_HANDLE['transport'] = 'tcp'
    config_dash.JSON_HANDLE['scheduler'] = 'singlePath'
    if not MPD:
        print("ERROR: Please provide the URL to the MPD file. Try Again..")
        return None

    config_dash.LOG.info('Downloading MPD file %s' % MPD)
    # Retrieve the MPD files for the video
    mpd_file = get_mpd(MPD)
    domain = get_domain_name(MPD)
    dp_object = DashPlayback()

    # Reading the MPD file created
    dp_object, video_segment_duration = read_mpd.read_mpd(mpd_file, dp_object)

    config_dash.LOG.info("The DASH media has %d video representations" %
                         len(dp_object.video))
    if LIST:
        # Print the representations and EXIT
        print_representations(dp_object)
        return None
    if "all" in PLAYBACK.lower():
        if mpd_file:
            config_dash.LOG.critical("Start ALL Parallel PLayback")
            start_playback_all(dp_object, domain)
    elif "basic" in PLAYBACK.lower():
        config_dash.LOG.critical("Started Basic-DASH Playback")
        start_playback_smart(dp_object, domain, "BASIC", DOWNLOAD,
                             video_segment_duration, LOG_FOLDER)
    elif "sara" in PLAYBACK.lower():
        config_dash.LOG.critical("Started SARA-DASH Playback")
        start_playback_smart(dp_object, domain, "SMART", DOWNLOAD,
                             video_segment_duration, LOG_FOLDER)
    elif "netflix" in PLAYBACK.lower():
        config_dash.LOG.critical("Started Netflix-DASH Playback")
        start_playback_smart(dp_object, domain, "NETFLIX", DOWNLOAD,
                             video_segment_duration, LOG_FOLDER)
    else:
        config_dash.LOG.error("Unknown Playback parameter {}".format(PLAYBACK))
        return None

    write_json()


if __name__ == "__main__":
    sys.exit(main())
