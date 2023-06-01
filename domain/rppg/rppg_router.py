from fastapi import APIRouter
import cv2
from skimage.util import img_as_float
from scipy.sparse import spdiags
import numpy as np
import scipy.io
import csv
import time
from datetime import datetime
from .model import Attention_mask, MTTS_CAN
from scipy.signal import butter
import hashlib

height = 480
width = 640
dim = 36
hr_method = 'FFT'
img_rows = 36
img_cols = 36
frame_depth = 10
batch_size = 10
fs = 30
model_checkpoint = 'C:/projects/myapi (8)/domain/rppg/mtts_can.hdf5'
model = MTTS_CAN(frame_depth, 32, 64, (img_rows, img_cols, 3))
model.load_weights(model_checkpoint)

router = APIRouter(
    prefix="/api/rppg",
)

@router.post("/video")
def rppg_video(data: dict):
    print(time.strftime('%Y.%m.%d - %H:%M:%S'))
    username = data.get("username")
    frames = data.get("imageData")
    avg_hr = -1
    avg = []
    hash_object = hashlib.sha256()
    hash_object.update(username.encode())
    result = hash_object.hexdigest()
    f = open(result + '.csv', 'a', newline="")
    with open(result + '.csv', 'r', newline="") as csvfile:
        reader = csv.reader(csvfile)
        temp = list(reader)
        if len(temp) > 1:

            for row in reversed(temp):
                value = float(row[2])
                avg.append(value)

            avg_value = sum(avg) / len(avg)
            avg_hr = avg_value

    i = 0
    totalFrames = len(frames)
    Xsub = np.zeros((totalFrames, dim, dim, 3), dtype=np.float32)

    if totalFrames == 100:
        for frame in frames:
            img = cv2.imdecode(np.array(frame, np.uint8), cv2.IMREAD_COLOR)

            vidLxL = cv2.resize(img_as_float(img[:, int(width / 2) - int(height / 2 + 1): 
                        int(height / 2) + int(width / 2), :]), (dim, dim), interpolation=cv2.INTER_AREA)
            vidLxL = cv2.rotate(vidLxL, cv2.ROTATE_90_CLOCKWISE)  # rotate 90 degree
            vidLxL = cv2.cvtColor(vidLxL.astype('float32'), cv2.COLOR_BGR2RGB)
            vidLxL[vidLxL > 1] = 1
            vidLxL[vidLxL < (1 / 255)] = 1 / 255
            Xsub[i, :, :, :] = vidLxL
            i = i + 1

        print(time.strftime('%Y.%m.%d - %H:%M:%S'))

        normalized_len = totalFrames - 1
        dXsub = np.zeros((normalized_len, dim, dim, 3), dtype=np.float32)
        for j in range(normalized_len - 1):
            dXsub[j, :, :, :] = (Xsub[j + 1, :, :, :] - Xsub[j, :, :, :]) / (
                        Xsub[j + 1, :, :, :] + Xsub[j, :, :, :])
        dXsub = dXsub / np.std(dXsub)
        Xsub = Xsub - np.mean(Xsub)
        Xsub = Xsub / np.std(Xsub)
        dXsub = np.concatenate((dXsub, Xsub[:totalFrames - 1, :, :, :]), axis=3);
        heartrate, pulsegraph = predict_vitals(dXsub)
        
        print(time.strftime('%Y.%m.%d - %H:%M:%S'))

        date = str(datetime.now())
        date = date[:-7]
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        wr = csv.writer(f)
        wr.writerow([date, username, heartrate])
        f.flush()
        f.close()

        print(time.strftime('%Y.%m.%d - %H:%M:%S'))

        pulsegraph_list = pulsegraph.tolist()

        return {"status": "success", "heartrate": str(heartrate), "pulsegraph": pulsegraph_list, "avgpulse": str(avg_hr)}
    return {"status": "fail"}

def _next_power_of_2(x):
    """Calculate the nearest power of 2."""
    return 1 if x == 0 else 2 ** (x - 1).bit_length()


def _calculate_fft_hr(ppg_signal, fs=60, low_pass=0.75, high_pass=2.5):
    """Calculate heart rate based on PPG using Fast Fourier transform (FFT)."""
    ppg_signal = np.expand_dims(ppg_signal, 0)
    N = _next_power_of_2(ppg_signal.shape[1])
    f_ppg, pxx_ppg = scipy.signal.periodogram(ppg_signal, fs=fs, nfft=N, detrend=False)
    fmask_ppg = np.argwhere((f_ppg >= low_pass) & (f_ppg <= high_pass))
    mask_ppg = np.take(f_ppg, fmask_ppg)
    mask_pxx = np.take(pxx_ppg, fmask_ppg)
    fft_hr = np.take(mask_ppg, np.argmax(mask_pxx, 0))[0] * 60
    return fft_hr


def _calculate_peak_hr(ppg_signal, fs):
    """Calculate heart rate based on PPG using peak detection."""
    ppg_peaks, _ = scipy.signal.find_peaks(ppg_signal)
    hr_peak = 60 / (np.mean(np.diff(ppg_peaks)) / fs)
    return hr_peak


def predict_vitals(dXsub):
    dXsub_len = (dXsub.shape[0] // frame_depth) * frame_depth
    dXsub = dXsub[:dXsub_len, :, :, :]
    yptest = model.predict((dXsub[:, :, :, :3], dXsub[:, :, :, -3:]), batch_size=batch_size, verbose=1)

    pulse = yptest[0]
    pulse_pred = detrend(np.cumsum(pulse), 100)

    [b_pulse, a_pulse] = butter(1, [0.75 / fs * 2, 2.5 / fs * 2], btype='bandpass')
    pulse_pred = scipy.signal.filtfilt(b_pulse, a_pulse, np.double(pulse_pred))

    # resp = yptest[1]
    # resp_pred = detrend(np.cumsum(resp), 100)
    # [b_resp, a_resp] = butter(1, [0.08 / fs * 2, 0.5 / fs * 2], btype='bandpass')
    # resp_pred = scipy.signal.filtfilt(b_resp, a_resp, np.double(resp_pred))

    if hr_method == 'FFT':
        hr_pred = _calculate_fft_hr(pulse_pred, fs=fs)

    elif hr_method == 'Peak':
        hr_pred = _calculate_peak_hr(pulse_pred, fs=fs)

    return hr_pred, pulse


def detrend(signal, Lambda):
    """detrend(signal, Lambda) -> filtered_signal
    This function applies a detrending filter.
    This code is based on the following article "An advanced detrending method with application
    to HRV analysis". Tarvainen et al., IEEE Trans on Biomedical Engineering, 2002.
    *Parameters*
      ``signal`` (1d numpy array):
        The signal where you want to remove the trend.
      ``Lambda`` (int):
        The smoothing parameter.
    *Returns*
      ``filtered_signal`` (1d numpy array):
        The detrended signal.
    """
    signal_length = signal.shape[0]

    # observation matrix
    H = np.identity(signal_length)

    # second-order difference matrix

    ones = np.ones(signal_length)
    minus_twos = -2 * np.ones(signal_length)
    diags_data = np.array([ones, minus_twos, ones])
    diags_index = np.array([0, 1, 2])
    D = spdiags(diags_data, diags_index, (signal_length - 2), signal_length).toarray()
    filtered_signal = np.dot((H - np.linalg.inv(H + (Lambda ** 2) * np.dot(D.T, D))), signal)
    return filtered_signal

