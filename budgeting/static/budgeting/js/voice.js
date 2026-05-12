/**
 * Speech-to-fill / auto-save for transaction fields (Web Speech API).
 * Transaction form: fill only. Dashboard: hidden form + optional auto-submit.
 */
(function () {
  function parseTranscript(raw, cats) {
    var t = (raw || "").toLowerCase().trim();
    var out = {
      kind: "expense",
      amount: null,
      categoryId: null,
      description: raw || "",
    };

    if (/\breceived\b|\bearned\b|\bsalary\b|\bincome\b/.test(t)) {
      out.kind = "income";
    }

    var numMatch = t.match(/\d+[.,]?\d*/);
    if (numMatch) {
      var n = parseFloat(numMatch[0].replace(",", "."));
      if (Number.isFinite(n) && n > 0) {
        out.amount = n.toFixed(2);
      }
    }

    function pickCategory(lower, list) {
      for (var i = 0; i < list.length; i++) {
        var name = (list[i].name || "").toLowerCase();
        if (!name.length) continue;
        if (lower.indexOf(name) !== -1) return String(list[i].id);
      }
      var synonyms = [
        [["food", "groceries", "grocery", "restaurant", "pizza"], "Food"],
        [["uber", "taxi", "train", "bus", "transport", "gas", "petrol"], "Transport"],
        [
          ["netflix", "spotify", "cinema", "movie", "entertain", "tv", "television", "cable", "hulu", "disney"],
          "Entertainment",
        ],
        [["rent", "electric", "water", "internet", "bill"], "Bills"],
        [["doctor", "pharmacy", "clinic", "health"], "Healthcare"],
        [
          [
            "clothes",
            "clothing",
            "shirt",
            "shirts",
            "pants",
            "jeans",
            "dress",
            "shoes",
            "sneakers",
            "jacket",
            "coat",
            "mall",
            "shopping",
            "apparel",
            "wardrobe",
            "accessories",
          ],
          "Shopping",
        ],
        [["salary", "paycheck", "wage"], "Salary"],
      ];
      for (var s = 0; s < synonyms.length; s++) {
        var words = synonyms[s][0];
        var tgt = synonyms[s][1];
        for (var w = 0; w < words.length; w++) {
          var cue = (words[w] || "").toLowerCase();
          if (!cue.length) continue;
          if (lower.indexOf(cue) !== -1) {
            for (var j = 0; j < list.length; j++) {
              if ((list[j].name || "").toLowerCase().indexOf(tgt.toLowerCase()) !== -1) {
                return String(list[j].id);
              }
            }
          }
        }
      }
      return null;
    }

    out.categoryId = pickCategory(t, cats);

    var now = new Date();
    var when = now;
    if (/\byesterday\b/.test(t)) {
      when.setDate(now.getDate() - 1);
    } else if (/\btoday\b/.test(t)) {
      /* keep */
    } else if (/\blast week\b/.test(t)) {
      when.setDate(now.getDate() - 7);
    }

    function pad(v) {
      return v < 10 ? "0" + v : String(v);
    }
    var y = when.getFullYear();
    var m = pad(when.getMonth() + 1);
    var d = pad(when.getDate());
    out.datetimeLocal = y + "-" + m + "-" + d + "T12:00";

    return out;
  }

  function fillTransactionForm(parsed, root) {
    root = root || document;
    var kindEl = root.querySelector('[name="kind"]');
    if (kindEl) kindEl.value = parsed.kind;

    var amtEl = root.querySelector('input[name="amount"]');
    if (amtEl && parsed.amount !== null) amtEl.value = parsed.amount;

    var catEl = root.querySelector('select[name="category"], input[name="category"]');
    if (catEl && parsed.categoryId) catEl.value = parsed.categoryId;

    var descEl = root.querySelector('input[name="description"], textarea[name="description"]');
    if (descEl) descEl.value = (parsed.description || "").trim();

    var whenEl = root.querySelector('input[name="occurred_at"]');
    if (whenEl && parsed.datetimeLocal) whenEl.value = parsed.datetimeLocal;
  }

  function canAutoSubmit(parsed) {
    if (!parsed.amount) return false;
    if (parsed.kind === "expense" && !parsed.categoryId) return false;
    return true;
  }

  function micBlockedHelp() {
    return (
      "Microphone blocked. In the address bar, click the lock or tune icon → Site settings → " +
      "Microphone → Allow, then reload and try again. On Windows, also check Settings → Privacy & security → " +
      "Microphone for the browser. Use https:// or http://127.0.0.1 — plain http:// on a LAN IP is blocked."
    );
  }

  function speechServiceBlockedHelp() {
    return (
      "Speech recognition was blocked by the browser or network (often extensions, VPN, or school/work policy). " +
      "Try another network, disable strict blockers, or review Microphone in the browser’s site permissions."
    );
  }

  function requestMicAccess(statusEl, onGranted) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      onGranted();
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(function (stream) {
        try {
          stream.getTracks().forEach(function (t) {
            t.stop();
          });
        } catch (_) {}
        onGranted();
      })
      .catch(function (err) {
        var name = err && err.name;
        if (!statusEl) return;
        if (name === "NotAllowedError" || name === "PermissionDeniedError") {
          statusEl.textContent = micBlockedHelp();
        } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
          statusEl.textContent = "No microphone found. Plug one in or choose the right input in system settings.";
        } else {
          statusEl.textContent =
            "Could not access the microphone" + (name ? " (" + name + ")." : ".");
        }
      });
  }

  function attachMic(cfg) {
    var micBtnId = cfg.micBtnId;
    var statusId = cfg.statusId;
    var categoriesId = cfg.categoriesId;
    var formId = cfg.formId || "";
    var autoSubmit = !!cfg.autoSubmit;

    var btn = document.getElementById(micBtnId);
    var statusEl = document.getElementById(statusId);
    var catEl = document.getElementById(categoriesId);
    if (!btn || !catEl) return;

    var formEl = formId ? document.getElementById(formId) : null;
    var root = formEl || document;

    var categories;
    try {
      categories = JSON.parse(catEl.textContent || "[]");
    } catch (_) {
      categories = [];
    }

    var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      if (statusEl) {
        statusEl.textContent =
          "Speech needs Chrome, Edge, or Safari with the Web Speech API enabled.";
      }
      btn.disabled = true;
      return;
    }

    if (typeof window.isSecureContext !== "undefined" && !window.isSecureContext) {
      if (statusEl) {
        statusEl.textContent =
          "Voice needs a secure page: use https:// or open the app at http://127.0.0.1 (not http://192.168… on plain HTTP).";
      }
      btn.disabled = true;
      return;
    }

    var recognition = new SpeechRec();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    btn.addEventListener("click", function () {
      if (statusEl) statusEl.textContent = "Allow the mic if prompted…";
      requestMicAccess(statusEl, function () {
        if (statusEl) statusEl.textContent = "Listening…";
        try {
          recognition.stop();
        } catch (_) {}
        try {
          recognition.start();
        } catch (e) {
          if (statusEl) {
            statusEl.textContent = "Could not start listening — wait a second and click again.";
          }
        }
      });
    });

    recognition.onerror = function (ev) {
      var err = (ev && ev.error) || "unknown";
      if (err === "aborted" || err === "no-speech") {
        if (statusEl) {
          statusEl.textContent = "No speech heard — click again and speak after the beep.";
        }
        return;
      }
      if (err === "not-allowed") {
        if (statusEl) statusEl.textContent = micBlockedHelp();
        return;
      }
      if (err === "service-not-allowed") {
        if (statusEl) statusEl.textContent = speechServiceBlockedHelp();
        return;
      }
      if (err === "audio-capture") {
        if (statusEl) {
          statusEl.textContent =
            "No microphone input. Check that the mic isn’t muted in Windows sound settings and try again.";
        }
        return;
      }
      if (statusEl) {
        statusEl.textContent =
          "Speech error (" + err + "). Try Chrome/Edge; if it persists, check the mic and site permissions.";
      }
    };

    recognition.onend = function () {
      if (statusEl && statusEl.textContent === "Listening…") {
        statusEl.textContent =
          "Session ended. Click the button again if you did not speak in time.";
      }
    };

    recognition.onresult = function (ev) {
      var text = "";
      try {
        text = ev.results[0][0].transcript;
      } catch (_) {}
      var parsed = parseTranscript(text, categories);
      fillTransactionForm(parsed, root);

      if (autoSubmit && formEl) {
        if (canAutoSubmit(parsed)) {
          if (statusEl) {
            statusEl.textContent = "Saving: “" + text + "”…";
          }
          formEl.submit();
          return;
        }
        var why = [];
        if (!parsed.amount) why.push("say an amount");
        if (parsed.kind === "expense" && !parsed.categoryId) {
          why.push("name a category that matches your list (e.g. food, clothes, bills)");
        }
        if (statusEl) {
          statusEl.textContent =
            "Heard “" +
            text +
            "” — need " +
            why.join(" and ") +
            ". Or use Add transaction to finish by hand.";
        }
        return;
      }

      if (statusEl) {
        statusEl.textContent = "Filled from: “" + text + "”. Review fields, then save.";
      }
    };
  }

  function init() {
    attachMic({
      micBtnId: "voice-mic-btn",
      statusId: "voice-mic-status",
      categoriesId: "voice-categories-data",
      autoSubmit: false,
    });
    attachMic({
      micBtnId: "dash-voice-mic-btn",
      statusId: "dash-voice-status",
      categoriesId: "dash-voice-categories-data",
      formId: "dash-voice-form",
      autoSubmit: true,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
