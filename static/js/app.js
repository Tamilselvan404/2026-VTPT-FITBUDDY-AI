const $ = (id) => document.getElementById(id);
let currentPlanId = null;
let currentUserId = null;

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 3000);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

async function loadHealth() {
  try {
    const health = await api("/health");
    $("statusCard").textContent = health.gemini_configured
      ? `Gemini connected · ${health.model}`
      : "Demo mode · add GOOGLE_API_KEY for Gemini";
  } catch {
    $("statusCard").textContent = "Backend status unavailable";
  }
}

function profileData() {
  return {
    name: $("name").value.trim(),
    age: Number($("age").value),
    gender: $("gender").value,
    weight_kg: Number($("weight_kg").value),
    goal: $("goal").value,
    intensity: $("intensity").value
  };
}

function renderPlan(data) {
  currentPlanId = data.plan_id;
  currentUserId = data.user_id;
  $("sourcePill").textContent = data.source === "gemini" ? "Gemini" : "Demo";
  $("emptyState").hidden = true;
  $("reviseCard").hidden = false;

  const plan = data.plan;
  const root = document.createElement("div");
  root.innerHTML = `
    <h3>${escapeHtml(plan.title)}</h3>
    <p>${escapeHtml(plan.summary)}</p>
    <div class="safety"><strong>Safety notes</strong><ul>${plan.safety_notes.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul></div>
    <div>${plan.days.map(day => `
      <article class="day">
        <div class="day-top"><strong>${escapeHtml(day.day)} · ${escapeHtml(day.focus)}</strong><span class="meta">${day.duration_minutes} min</span></div>
        ${day.exercises.map(ex => `
          <div class="exercise">
            <strong>${escapeHtml(ex.name)}</strong>
            <div class="meta">${ex.sets} sets · ${escapeHtml(ex.reps)} · ${ex.rest_seconds}s rest</div>
            ${ex.notes ? `<div class="meta">${escapeHtml(ex.notes)}</div>` : ""}
          </div>
        `).join("")}
      </article>
    `).join("")}</div>
  `;
  $("planView").replaceChildren(root);
  $("planView").hidden = false;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[c]));
}

$("profileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("generateBtn");
  button.disabled = true;
  button.textContent = "Building your plan…";

  try {
    const data = await api("/api/plans/generate", {
      method: "POST",
      body: JSON.stringify(profileData())
    });
    renderPlan(data);

    const tip = await api(`/api/nutrition-tip?goal=${encodeURIComponent($("goal").value)}`);
    $("tipText").textContent = tip.tip;
    toast("Plan generated successfully.");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Generate 7-day plan";
  }
});

$("reviseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;

  try {
    const data = await api(`/api/plans/${currentPlanId}/revise`, {
      method: "POST",
      body: JSON.stringify({ feedback: $("feedback").value.trim() })
    });
    renderPlan(data);
    $("feedback").value = "";
    toast("Plan revised.");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
});

$("tipBtn").addEventListener("click", async () => {
  $("tipBtn").disabled = true;
  try {
    const tip = await api(`/api/nutrition-tip?goal=${encodeURIComponent($("goal").value)}`);
    $("tipText").textContent = tip.tip;
  } catch (error) {
    toast(error.message);
  } finally {
    $("tipBtn").disabled = false;
  }
});

loadHealth();
