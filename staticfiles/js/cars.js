/* cars.js
   - Image uploader: click + drag & drop + live preview + remove (supports Django clear checkbox)
   - Quantity controls: [data-qty] with [data-minus]/[data-plus], honors min/max/step
*/

document.addEventListener("DOMContentLoaded", function () {
  // ---------- helpers ----------
  function toNumber(v, fallback) {
    var n = Number(v);
    return Number.isFinite(n) ? n : (fallback ?? 0);
  }
  function clamp(val, min, max) {
    var out = Math.max(min, val);
    if (Number.isFinite(max)) out = Math.min(out, max);
    return out;
  }
  function getAttrNum(el, name, fallback) {
    var raw = el.getAttribute(name);
    return raw === null ? fallback : toNumber(raw, fallback);
  }

  // ---------- image uploader ----------
  (function () {
    var form     = document.querySelector(".cars-form");
    var uploader = document.getElementById("carUploader");
    if (!form || !uploader) return;

    // Select elements locally within the uploader block to avoid name brittleness
    var input    = uploader.querySelector('input[type="file"]');
    var dropZone = uploader.querySelector(".cars-upload-zone");
    var prevLive = uploader.querySelector("#cars-preview");           // hidden img for new uploads
    var prevExist= uploader.querySelector("#cars-preview-existing");  // existing img (edit mode)

    if (!input || !dropZone) return;

    // Build preview wrapper with remove button
    var wrap = document.createElement("div");
    wrap.className = "cars-preview-wrap is-hidden";

    if (prevExist) wrap.appendChild(prevExist);
    if (prevLive)  wrap.appendChild(prevLive);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "cars-remove-btn";
    removeBtn.setAttribute("aria-label", "Remove image");
    removeBtn.textContent = "×";
    wrap.appendChild(removeBtn);

    uploader.insertBefore(wrap, dropZone);

    // Ensure the Django clear checkbox (for ClearableFileInput) exists
    function ensureClearCheckbox() {
      // Works with default ClearableFileInput: <input type="checkbox" name="image-clear">
      var baseName = input.name || "image";
      var name = baseName + "-clear";
      var clear = form.querySelector('input[type="checkbox"][name="' + name + '"]');
      if (!clear) {
        clear = document.createElement("input");
        clear.type = "checkbox";
        clear.name = name;
        clear.className = "is-hidden";
        form.appendChild(clear);
      }
      return clear;
    }
    var clearInput = ensureClearCheckbox();

    function showEmpty() {
      dropZone.classList.remove("is-hidden");
      wrap.classList.add("is-hidden");
    }

    function showPreview(useLive) {
      dropZone.classList.add("is-hidden");
      wrap.classList.remove("is-hidden");
      if (prevExist) prevExist.classList.add("is-hidden");
      if (prevLive)  prevLive.classList.add("is-hidden");
      (useLive ? prevLive : prevExist)?.classList.remove("is-hidden");
    }

    // Initial state
    if (prevExist && prevExist.getAttribute("src")) {
      showPreview(false);
    } else {
      showEmpty();
    }

    // Open file dialog
    dropZone.addEventListener("click", function (e) {
      e.preventDefault();
      input.click();
    });
    wrap.addEventListener("click", function (e) {
      if (e.target === removeBtn) return;
      input.click();
    });

    // File -> live preview
    function handleFile(file) {
      if (!file || !file.type || !file.type.startsWith("image/")) return;
      var url = URL.createObjectURL(file);
      if (prevLive) {
        prevLive.src = url;
        showPreview(true);
        if (clearInput) clearInput.checked = false;
      }
    }

    input.addEventListener("change", function () {
      var file = (input.files && input.files[0]) || null;
      handleFile(file);
    });

    // Drag & drop behavior
    ["dragenter", "dragover"].forEach(function (ev) {
      uploader.addEventListener(ev, function (e) {
        e.preventDefault(); e.stopPropagation();
        uploader.classList.add("drag-over");
        dropZone.classList.add("is-drag");
      });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      uploader.addEventListener(ev, function (e) {
        e.preventDefault(); e.stopPropagation();
        uploader.classList.remove("drag-over");
        dropZone.classList.remove("is-drag");
      });
    });
    uploader.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        var file = files[0];
        // Assign to the input via DataTransfer for compatibility
        var dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });

    // Remove image (clear field)
    removeBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      try {
        input.value = "";
        // Clear FileList
        var dt = new DataTransfer();
        input.files = dt.files;
      } catch (_) {}
      if (clearInput) clearInput.checked = true;
      if (prevLive)  { prevLive.removeAttribute("src"); prevLive.classList.add("is-hidden"); }
      if (prevExist) { prevExist.classList.add("is-hidden"); }
      showEmpty();
    });
  })();

  // ---------- quantity controls ----------
  (function () {
    document.querySelectorAll("[data-qty]").forEach(function (wrap) {
      var minus = wrap.querySelector("[data-minus]");
      var plus  = wrap.querySelector("[data-plus]");
      var input = wrap.querySelector("input, input[type='number']");

      if (!input) return;

      var step = getAttrNum(input, "step", 1);
      var min  = input.hasAttribute("min") ? getAttrNum(input, "min", -Infinity) : -Infinity;
      var max  = input.hasAttribute("max") ? getAttrNum(input, "max", Infinity)   :  Infinity;

      function setVal(v) {
        v = clamp(v, min, max);
        input.value = String(v);
        // Trigger reactive form libraries if any
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }

      minus && minus.addEventListener("click", function (e) {
        e.preventDefault();
        var v = toNumber(input.value, 0);
        setVal(v - step);
      });

      plus && plus.addEventListener("click", function (e) {
        e.preventDefault();
        var v = toNumber(input.value, 0);
        setVal(v + step);
      });

      // Keyboard support on +/- buttons
      [minus, plus].forEach(function (btn) {
        if (!btn) return;
        btn.setAttribute("type", "button");
        btn.setAttribute("tabindex", "0");
        btn.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            btn.click();
          }
        });
      });
    });
  })();
});
