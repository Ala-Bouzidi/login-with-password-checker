// password_strength.js
const passwordInput = document.getElementById("password");
const rules = {
  length: document.getElementById("r-length"),
  upper: document.getElementById("r-upper"),
  digit: document.getElementById("r-digit"),
  special: document.getElementById("r-special"),
  common: document.getElementById("r-common")
};
const bar = document.querySelector(".bar");
const scoreText = document.getElementById("scoreText");

let lastRequest = 0;

function setRule(el, ok){
  el.classList.toggle("ok", ok);
  el.classList.toggle("fail", !ok);
}

function setBar(percent){
  bar.style.setProperty("--pct", percent + "%");
  bar.querySelector("::after"); // noop to avoid linter issues
  // change CSS width by changing pseudo-element via inline style hack:
  bar.style.background = "#eee";
  // create inner fill element if not exists
  let fill = bar.querySelector(".fill");
  if (!fill) {
    fill = document.createElement("div");
    fill.className = "fill";
    fill.style.height = "100%";
    fill.style.borderRadius = "6px";
    fill.style.transition = "width 140ms ease";
    bar.appendChild(fill);
  }
  let color = "#ff5959";
  if (percent >= 75) color = "#27ae60";
  else if (percent >= 50) color = "#f1c232";
  else color = "#ff5959";
  fill.style.width = percent + "%";
  fill.style.background = color;
}

async function checkPassword(password) {
  // client-side checks
  const length_ok = password.length >= 8;
  const has_upper = /[A-Z]/.test(password);
  const has_digit = /\d/.test(password);
  const has_special = /[^a-zA-Z0-9]/.test(password);

  setRule(rules.length, length_ok);
  setRule(rules.upper, has_upper);
  setRule(rules.digit, has_digit);
  setRule(rules.special, has_special);

  // talk to server for 'common passwords' check
  const reqId = ++lastRequest;
  let in_common = false;
  try {
    const res = await fetch("/api/check_password", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password})
    });
    if (reqId !== lastRequest) return; // outdated response
    const data = await res.json();
    in_common = !!data.in_common;
    setRule(rules.common, !in_common);
    const score = data.score; // 0-4
    const percent = Math.min(100, Math.round((score / 4) * 100));
    scoreText.textContent = in_common ? "Too common — choose another password." : ["Very weak","Weak","Okay","Good","Strong"][score];
    setBar(percent);
  } catch (e) {
    // network error: just evaluate locally
    setRule(rules.common, true);
    const score = [length_ok, has_upper, has_digit, has_special].filter(Boolean).length;
    const percent = Math.min(100, Math.round((score / 4) * 100));
    scoreText.textContent = ["Very weak","Weak","Okay","Good","Strong"][score];
    setBar(percent);
  }
}

passwordInput && passwordInput.addEventListener("input", (e) => {
  checkPassword(e.target.value);
});

// initial state
checkPassword("");
