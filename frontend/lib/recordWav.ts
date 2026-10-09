// Records from the microphone and returns a 16 kHz mono WAV Blob.
//
// Why convert in the browser: MediaRecorder produces webm/opus (Chrome,
// Firefox) or mp4 (Safari), and decoding those on the server needs ffmpeg
// installed. A plain 16 kHz mono WAV is what speech models want anyway and
// the Python side can read it with no extra system tools.

const TARGET_RATE = 16000;

export type Recorder = { stop: () => Promise<Blob>; cancel: () => void };

export async function startRecording(): Promise<Recorder> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const media = new MediaRecorder(stream);
  const chunks: BlobPart[] = [];
  media.ondataavailable = (e) => e.data.size > 0 && chunks.push(e.data);
  media.start();

  const release = () => stream.getTracks().forEach((t) => t.stop());

  return {
    cancel() {
      if (media.state !== "inactive") media.stop();
      release();
    },
    stop() {
      return new Promise<Blob>((resolve, reject) => {
        media.onstop = async () => {
          release();
          try {
            const raw = new Blob(chunks, { type: media.mimeType });
            resolve(await toWav16k(raw));
          } catch (e) {
            reject(e);
          }
        };
        media.stop();
      });
    },
  };
}

async function toWav16k(blob: Blob): Promise<Blob> {
  const bytes = await blob.arrayBuffer();
  const ctx = new AudioContext();
  const decoded = await ctx.decodeAudioData(bytes);
  await ctx.close();

  // Resample + downmix to mono with an OfflineAudioContext.
  const length = Math.ceil(decoded.duration * TARGET_RATE);
  const offline = new OfflineAudioContext(1, length, TARGET_RATE);
  const src = offline.createBufferSource();
  src.buffer = decoded;
  src.connect(offline.destination);
  src.start();
  const rendered = await offline.startRendering();

  return encodeWav(rendered.getChannelData(0), TARGET_RATE);
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const write = (offset: number, s: string) =>
    [...s].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));

  write(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  write(8, "WAVE");
  write(12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  write(36, "data");
  view.setUint32(40, samples.length * 2, true);

  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}
