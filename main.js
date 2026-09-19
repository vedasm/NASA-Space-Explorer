const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

function enableParallax() {
  if (motionQuery.matches) return;

  let framePending = false;

  const updateParallax = () => {
    const scroll = window.scrollY;
    document.documentElement.style.setProperty("--star-drift", `${scroll * -0.08}px`);
    document.documentElement.style.setProperty(
      "--star-drift-slow",
      `${scroll * -0.035}px`
    );
    document.documentElement.style.setProperty(
      "--shooting-drift",
      `${scroll * -0.12}px`
    );
    document.documentElement.style.setProperty("--hero-drift", `${scroll * -0.025}px`);
    framePending = false;
  };

  window.addEventListener(
    "scroll",
    () => {
      if (framePending) return;
      framePending = true;
      window.requestAnimationFrame(updateParallax);
    },
    { passive: true }
  );
  updateParallax();
}

enableParallax();

function bindMagnetic(root = document) {
  if (motionQuery.matches) return;

  root.querySelectorAll(".jump a").forEach((element) => {
    if (element.dataset.magneticBound) return;
    element.dataset.magneticBound = "true";

    element.addEventListener("pointermove", (event) => {
      const bounds = element.getBoundingClientRect();
      const x = Math.max(-4, Math.min(4, ((event.clientX - bounds.left) / bounds.width - 0.5) * 8));
      const y = Math.max(-4, Math.min(4, ((event.clientY - bounds.top) / bounds.height - 0.5) * 8));
      element.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    });

    element.addEventListener("pointerleave", () => {
      element.style.transform = "";
    });
  });
}

bindMagnetic();

function escapeHtml(text) {
  const box = document.createElement("div");
  box.textContent = text ?? "";
  return box.innerHTML;
}

async function requestJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function showError(element, message) {
  element.innerHTML = `<p class="notice notice--error">${escapeHtml(message)}</p>`;
}

function buildMedia(data) {
  if (data.media_type === "image") {
    const imageUrl = data.hdurl || data.url;
    return `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(data.title)}" />
      <button class="media-expand" type="button" aria-label="View full image">View full image</button>`;
  }
  if (data.url.includes("youtube") || data.url.includes("vimeo")) {
    return `<iframe src="${escapeHtml(data.url)}" title="${escapeHtml(data.title)}"
              allow="accelerometer; encrypted-media; picture-in-picture"
              allowfullscreen></iframe>`;
  }
  return `<video src="${escapeHtml(data.url)}" controls></video>`;
}

const imageViewer = document.querySelector("#image-viewer");
const viewerImage = document.querySelector("#image-viewer-image");
const closeViewer = () => imageViewer.close();

document.querySelector("#apod-media").addEventListener("click", (event) => {
  if (!event.target.closest(".media-expand")) return;

  const image = document.querySelector("#apod-media img");
  viewerImage.src = image.src;
  viewerImage.alt = image.alt;
  imageViewer.showModal();
});

imageViewer.addEventListener("click", (event) => {
  if (event.target === imageViewer || event.target.closest(".image-viewer__close")) {
    closeViewer();
  }
});

async function loadApod() {
  const frame = document.querySelector("#apod-media");

  try {
    const data = await requestJson("/api/apod");

    frame.innerHTML = buildMedia(data);
    document.querySelector("#apod-title").textContent = data.title;
    document.querySelector("#apod-explanation").textContent = data.explanation;
    document.querySelector("#apod-date").textContent = data.date;
    document.title = `${data.title} — NASA Space Explorer`;

    if (data.copyright) {
      document.querySelector("#apod-credit").textContent =
        `Image: ${data.copyright.trim()}`;
    }
  } catch (error) {
    showError(frame, error.message);
  }
}

loadApod();
