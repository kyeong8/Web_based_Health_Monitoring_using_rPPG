<script>
  import { onMount, onDestroy } from 'svelte';
  import fastapi from '../lib/api';
  import { username, is_login } from "../lib/store";

  let videoRef;
  let error = '';
  let isStreaming = false;
  let print_hr = 0;
  let streamInterval;
  let frames = [];
  let avg_hr = 0;
  let pulse;

  let isRecording = false;
  let showPrintHr = false;
  let showAvgHr = false;
  let showCanvas = false; // 캔버스를 표시할지 여부를 저장하는 변수

  let pulseGraphRef;
  let graphContext;

  const startStreaming = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false
      });
      videoRef.srcObject = stream;
      videoRef.play();
      isStreaming = true;
    } catch (err) {
      error = err.message;
    }
  };

  const stopStreaming = () => {
    const stream = videoRef.srcObject;
    if (stream) {
      const tracks = stream.getTracks();
      tracks.forEach((track) => {
        track.stop();
      });
      videoRef.srcObject = null;
      isStreaming = false;
    }
  };

  const drawVideo = () => {
    window.requestAnimationFrame(drawVideo);
  };

  const rppg = async () => {
    isRecording = true;
    const date = new Date(Date.now());
    console.log(date);

    let url = '/api/rppg/video';

    while (isStreaming) {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      canvas.width = videoRef.videoWidth;
      canvas.height = videoRef.videoHeight;
      context.drawImage(videoRef, 0, 0, canvas.width, canvas.height);
      const frame = canvas.toDataURL('image/jpeg', 1.0);

      frames.push(frame);

      await new Promise(resolve => setTimeout(resolve, 33)); // 33ms ≈ 30fps
      if (frames.length === 100) { // 10 seconds * 30fps
        const date = new Date(Date.now());
        console.log(date);
        break;
      }
    }

    // Convert frames to imageData
    const imageData = frames.map(frame => {
      const binaryFrame = atob(frame.split(',')[1]);
      const byteArray = new Uint8Array(binaryFrame.length);
      for (let i = 0; i < binaryFrame.length; i++) {
        byteArray[i] = binaryFrame.charCodeAt(i);
      }
      return Array.from(byteArray);
    });
    frames = [];
    fastapi(
      'post',
      url,
      {imageData : imageData, username: String($username) },
      (json) => {
        if (json.status === 'success') {
          print_hr = json.heartrate;
          showPrintHr = true;

          if (Array.isArray(json.pulsegraph)) {
            pulse = new Float32Array(json.pulsegraph.flat());
          } else {
            // 예외 처리: pulse가 배열 형태가 아닌 경우
            console.error("Invalid pulse data");
          }
          avg_hr = json.avgpulse;
          showAvgHr = true;
          const date = new Date(Date.now());
          console.log(date);
          showCanvas = true; // 응답을 받았으므로 캔버스를 표시
        }
        else {
          console.log("response pulse error")
        }
      },
      (json_error) => {
        error = json_error;
      }
    );
    isRecording = false;
  };

  const drawPulseGraph = () => {
    graphContext.clearRect(0, 0, pulseGraphRef.width, pulseGraphRef.height);
    if (pulse) {
      const graphWidth = pulseGraphRef.width;
      const graphHeight = pulseGraphRef.height;
      const numSamples = pulse.length;

      // Calculate the horizontal and vertical scaling factors
      const xScale = graphWidth / numSamples;
      const yScale = graphHeight / (Math.max(...pulse) - Math.min(...pulse));

      // Draw the graph
      graphContext.beginPath();
      graphContext.moveTo(0, graphHeight - (pulse[0] - Math.min(...pulse)) * yScale);
      for (let i = 1; i < numSamples; i++) {
        graphContext.lineTo(i * xScale, graphHeight - (pulse[i] - Math.min(...pulse)) * yScale);
      }
      graphContext.strokeStyle = 'green';
      graphContext.lineWidth = 2;
      graphContext.stroke();
    }
    window.requestAnimationFrame(drawPulseGraph);
  };

  onMount(() => {
    if ($is_login) {
      startStreaming();
      drawVideo();

      pulseGraphRef = document.getElementById('pulseGraph');
      graphContext = pulseGraphRef.getContext('2d');
      drawPulseGraph();
    }
  });

  onDestroy(() => {
    if ($is_login) {
      clearInterval(streamInterval);
      stopStreaming();
    }
  });
</script>

<style>
  .container {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    height: 50vh;
  }

  .video-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }

  .pulse-graph {
    position: absolute;
    top: calc(100% + 10px);
    left: 50%;
    transform: translateX(-50%);
    border: 1px solid black;
  }

  .button-container {
    position: absolute;
    bottom: 0;
    right: 0;
    scale: 1.5;
    transform: translate(-150%, -20%);
  }

  .show {
    display: block;
  }

  .hide {
    display: none;
  }
</style>

<div class="container">
  <div class="video-container">
    <!-- svelte-ignore a11y-media-has-caption -->
    <video id="video" bind:this={videoRef} />
  </div>

  <div style="position: absolute; top: 0px; left: 350px; color: red; font-size: 30px;">
    {#if showPrintHr}
      {"hr: " + print_hr}
    {/if}
  </div>
  <div style="position: absolute; top: 30px; left: 350px; color: blue; font-size: 30px;">
    {#if showAvgHr}
      {"avg: " + avg_hr}
    {/if}
  </div>
  
  <div class="pulse-graph {showCanvas ? 'show' : 'hide'}">
    <canvas id="pulseGraph" width="800" height="200"></canvas>
  </div>

  <div class="button-container">
    <button on:click="{rppg}" disabled={isRecording}>
      Start rPPG
    </button>
  </div>
</div>
