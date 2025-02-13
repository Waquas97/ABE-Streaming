import numpy as np


def zipf_dist(num_clients):
	#Files
	mpd_files = ["help360-HTTPS-4tiles.mpd","help360-HTTPS-4tiles-copy1.mpd","help360-HTTPS-4tiles-copy2.mpd","help360-HTTPS-4tiles-copy3.mpd","help360-HTTPS-4tiles-copy4.mpd"]


	# Parameters
	a = 1.5  # This value controls the skewness of the distribution. Adjust as needed.

	# Generate client selections
	selections = np.random.zipf(a, num_clients)

	# Normalize to match your mpd_files index range (0 to len(mpd_files)-1)
	selections = np.clip(selections - 1, 0, len(mpd_files) - 1)

	# Assign MPD files to clients based on ZIPF distribution
	selected_mpd_files = [mpd_files[i] for i in selections]
	#print(selected_mpd_files)

	print(len(selected_mpd_files))
	print(selected_mpd_files)

zipf_dist(30)