// backend base URL (خلي البورت نفس اللي مشغّل عليه uvicorn)
const backendBase = "http://127.0.0.1:8001";

var UploadAudio = document.getElementById("upload-audio");
var UploadForm = document.getElementById("upload-form");
var UploadAudioErr = document.getElementById("upload_audio_err");
var SubmitButton = document.getElementById("submit-button");
var ExampleButton = document.getElementById("example-button");
var ClearButton = document.getElementById("clear-button");
var Spinner = document.getElementById("spinner");

async function processTest(e) {
  e.preventDefault();

  if (!UploadAudio.files || UploadAudio.files.length === 0) {
    UploadAudioErr.classList.remove("d-none");
    return false;
  }

  const allowedExt = ["wav", "ogg", "mp3", "flac", "m4a", "aac", "opus"];
  const ext = UploadAudio.files[0].name.split(".").pop().toLowerCase();
  if (!allowedExt.includes(ext)) {
    UploadAudioErr.innerHTML = "please upload an audio file (wav/ogg/mp3/...)";
    UploadAudioErr.classList.remove("d-none");
    return false;
  }

  try {
    // UI: disable buttons and show spinner
    UploadAudioErr.classList.add("d-none");
    setDisabled(true);
    Spinner.style.display = "inline-block";
    document.getElementById("status").innerText =
      "Status: uploading & processing...";

    const formData = new FormData();
    formData.append("file", UploadAudio.files[0]); // اسم الحقل في الـ backend = file

    const res = await fetch(backendBase + "/process-audio/", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let txt = await res.text().catch(() => "");
      console.error("Server error", res.status, txt);
      document.getElementById(
        "status"
      ).innerText = `Status: Server error ${res.status}`;
      return;
    }

    const result = await res.json();
    console.log(result);

    setStatus("File processed.", "ok");

    // show returned images (data-URLs or full URLs)
    if (result.original_plot)
      drawImage(
        result.original_plot,
        "wave-before",
        "ph-before",
        "dl-before",
        "original.png"
      );
    if (result.noisy_plot)
      drawImage(
        result.noisy_plot,
        "wave-middle",
        "ph-middle",
        "dl-middle",
        "noisy.png"
      );
    if (result.filtered_plot)
      drawImage(
        result.filtered_plot,
        "wave-after",
        "ph-after",
        "dl-after",
        "filtered.png"
      );

    // show kind if provided
    if (result.kind) {
      const k = result.kind;
      document.getElementById("cap-before").innerText = `Type: ${k}`;
      document.getElementById("cap-middle").innerText = `Type: ${k}`;
      document.getElementById("cap-after").innerText = `Type: ${k}`;
    }
  } catch (error) {
    console.error("Error uploading file:", error);
    document.getElementById("status").innerText =
      "Status: Error uploading file.";
  } finally {
    setDisabled(false);
    Spinner.style.display = "none";
  }
}

// زرار الـ Example يستدعي /process-default
ExampleButton.addEventListener("click", async function () {
  try {
    setDisabled(true);
    Spinner.style.display = "inline-block";
    document.getElementById("status").innerText =
      "Status: processing default example...";
    const res = await fetch(backendBase + "/process-default");
    if (!res.ok) {
      document.getElementById(
        "status"
      ).innerText = `Status: Example failed ${res.status}`;
      return;
    }
    const result = await res.json();

    if (result.original_plot)
      drawImage(
        result.original_plot,
        "wave-before",
        "ph-before",
        "dl-before",
        "original.png"
      );
    if (result.noisy_plot)
      drawImage(
        result.noisy_plot,
        "wave-middle",
        "ph-middle",
        "dl-middle",
        "noisy.png"
      );
    if (result.filtered_plot)
      drawImage(
        result.filtered_plot,
        "wave-after",
        "ph-after",
        "dl-after",
        "filtered.png"
      );

    if (result.kind) {
      document.getElementById("cap-before").innerText = `Type: ${result.kind}`;
      document.getElementById("cap-middle").innerText = `Type: ${result.kind}`;
      document.getElementById("cap-after").innerText = `Type: ${result.kind}`;
    }

    document.getElementById("status").innerText = "Status: Example processed.";
  } catch (e) {
    console.error(e);
    document.getElementById("status").innerText = "Status: error in example.";
  } finally {
    setDisabled(false);
    Spinner.style.display = "none";
  }
});

// helper: set image src from full URL
function drawImage(url, imgId, placeholderId, downloadId, downloadFilename) {
  if (!url) return;
  const el = document.getElementById(imgId);
  const ph = placeholderId ? document.getElementById(placeholderId) : null;
  const dl = downloadId ? document.getElementById(downloadId) : null;
  if (!el) return;
  el.src = url;
  el.style.display = "block";
  if (ph) ph.style.display = "none";
  if (dl) {
    dl.style.display = "inline-block";
    dl.href = url;
    if (downloadFilename) dl.setAttribute("download", downloadFilename);
  }
}

function setDisabled(state) {
  if (SubmitButton) SubmitButton.disabled = state;
  if (ExampleButton) ExampleButton.disabled = state;
  if (ClearButton) ClearButton.disabled = state;
  if (UploadAudio) UploadAudio.disabled = state;
}

ClearButton.addEventListener("click", function () {
  // reset images/placeholders
  document.getElementById("wave-before").style.display = "none";
  document.getElementById("wave-middle").style.display = "none";
  document.getElementById("wave-after").style.display = "none";
  document.getElementById("ph-before").style.display = "block";
  document.getElementById("ph-middle").style.display = "block";
  document.getElementById("ph-after").style.display = "block";
  document.getElementById("status").innerText = "Status: idle";
  UploadForm.reset();
});
