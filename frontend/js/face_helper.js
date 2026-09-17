// SmartRail HQ — Face Recognition & Biometric Camera Helper
class BiometricScanner {
  constructor(videoElement, canvasElement, statusElement) {
    this.video = videoElement;
    this.canvas = canvasElement || document.createElement("canvas");
    this.statusElem = statusElement;
    this.stream = null;
    this.isScanning = false;
  }

  async startCamera() {
    try {
      if (this.statusElem) this.statusElem.innerText = "Камера іске қосылуда...";
      
      const constraints = {
        video: {
          facingMode: "user",
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;
      await this.video.play();
      this.isScanning = true;

      if (this.statusElem) this.statusElem.innerText = "Түріңізді овалға бағыттаңыз";
      return true;
    } catch (err) {
      console.warn("Camera access denied or unavailable, using simulation fallback:", err);
      if (this.statusElem) this.statusElem.innerText = "Демо-режим: камера имитациясы";
      return false;
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
      this.isScanning = false;
    }
  }

  captureFrame() {
    if (!this.video || !this.video.videoWidth) {
      // Return synthetic sample biometric image
      return this.generateSyntheticFace();
    }
    this.canvas.width = this.video.videoWidth;
    this.canvas.height = this.video.videoHeight;
    const ctx = this.canvas.getContext("2d");
    ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
    return this.canvas.toDataURL("image/jpeg", 0.85);
  }

  generateSyntheticFace() {
    const c = document.createElement("canvas");
    c.width = 300;
    c.height = 300;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, 300, 300);
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(150, 150, 80, 0, Math.PI * 2);
    ctx.stroke();
    return c.toDataURL("image/jpeg", 0.8);
  }
}
