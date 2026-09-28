const API_BASE = "/api";

// ---------- utilities ----------

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return null;
  return response.json();
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2400);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function titleCase(str) {
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

// ---------- tab navigation ----------

document.getElementById("tabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".tab-btn");
  if (!btn) return;
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  if (btn.dataset.tab === "recommendations") loadRecommendations();
  if (btn.dataset.tab === "inventory") loadInventory();
  if (btn.dataset.tab === "recipes") loadRecipes();
  if (btn.dataset.tab === "preferences") loadPreferences();
});

// ---------- modal ----------

const modalBackdrop = document.getElementById("modal-backdrop");
document.getElementById("modal-close").addEventListener("click", () => modalBackdrop.classList.remove("active"));
modalBackdrop.addEventListener("click", (e) => {
  if (e.target === modalBackdrop) modalBackdrop.classList.remove("active");
});

async function openRecipeModal(recipeId) {
  const recipe = await apiRequest(`/recipes/${recipeId}`);
  const body = document.getElementById("modal-body");
  body.innerHTML = `
    <h3>${escapeHtml(recipe.title)}</h3>
    <p class="recipe-meta">${escapeHtml(recipe.cuisine)} · ${recipe.prep_time_minutes} min · ${recipe.calories ?? "?"} kcal</p>
    <ul class="ingredient-list">
      ${recipe.ingredients
        .map(
          (ri) => `<li><span>${escapeHtml(titleCase(ri.ingredient.name))}${ri.optional ? " (optional)" : ""}</span><span>${ri.quantity} ${escapeHtml(ri.unit)}</span></li>`
        )
        .join("")}
    </ul>
    <div class="steps">${escapeHtml(recipe.steps)}</div>
  `;
  modalBackdrop.classList.add("active");
}

// ---------- recommendations ----------

function expiryLabel(days) {
  if (days === null || days === undefined) return null;
  if (days <= 0) return { text: "expires today", cls: "soon" };
  if (days === 1) return { text: "1 day left", cls: "soon" };
  if (days <= 3) return { text: `${days} days left`, cls: "soon" };
  return { text: `${days} days left`, cls: "ok" };
}

function recommendationCardHtml(rec) {
  const r = rec.recipe;
  const missing = rec.missing_ingredients.map((m) => `<span class="tag missing">missing: ${escapeHtml(titleCase(m))}</span>`);
  const subs = Object.entries(rec.substitutable).map(
    ([orig, sub]) => `<span class="tag sub">use ${escapeHtml(titleCase(sub.substitute))} for ${escapeHtml(titleCase(orig))}</span>`
  );
  const expiring = rec.expiring_ingredients_used.map((e) => `<span class="tag urgent">${escapeHtml(titleCase(e))} expiring</span>`);

  return `
    <div class="recipe-card" data-recipe-id="${r.id}">
      ${expiring.length ? `<div class="expiry-sticker ${rec.expiry_urgency > 0.6 ? "soon" : ""}">use it up</div>` : ""}
      <h3 class="recipe-title" data-recipe-id="${r.id}">${escapeHtml(r.title)}</h3>
      <p class="recipe-meta">${escapeHtml(r.cuisine)} · ${r.prep_time_minutes} min · ${r.calories ?? "?"} kcal · ranked by ${rec.model_used === "learned_reranker" ? "your history" : "heuristic"}</p>

      <div class="score-bar-row">
        <span>have</span>
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${Math.round(rec.coverage * 100)}%"></div></div>
        <span>${Math.round(rec.coverage * 100)}%</span>
      </div>
      <div class="score-bar-row">
        <span>urgency</span>
        <div class="score-bar-track"><div class="score-bar-fill expiry" style="width:${Math.round(rec.expiry_urgency * 100)}%"></div></div>
        <span>${Math.round(rec.expiry_urgency * 100)}%</span>
      </div>

      <div class="tag-row">${expiring.join("")}${missing.join("")}${subs.join("")}</div>

      <div class="card-actions">
        <button class="btn btn-small btn-cook" data-action="cooked" data-recipe-id="${r.id}">Cooked it</button>
        <button class="btn btn-small btn-skip" data-action="skipped" data-recipe-id="${r.id}">Skip</button>
      </div>
    </div>
  `;
}

async function loadRecommendations() {
  const list = document.getElementById("reco-list");
  list.innerHTML = `<div class="empty-state">Finding what to cook...</div>`;
  try {
    const recs = await apiRequest("/recommendations?top_n=12");
    if (!recs.length) {
      list.innerHTML = `<div class="empty-state">No recipes match right now. Add inventory items or loosen your preferences.</div>`;
      return;
    }
    list.innerHTML = recs.map(recommendationCardHtml).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Couldn't load recommendations: ${escapeHtml(err.message)}</div>`;
  }
}

document.getElementById("reco-list").addEventListener("click", async (e) => {
  const titleEl = e.target.closest(".recipe-title");
  if (titleEl) {
    openRecipeModal(titleEl.dataset.recipeId);
    return;
  }
  const actionBtn = e.target.closest("[data-action]");
  if (actionBtn) {
    const recipeId = Number(actionBtn.dataset.recipeId);
    const action = actionBtn.dataset.action;
    try {
      await apiRequest("/interactions", { method: "POST", body: JSON.stringify({ recipe_id: recipeId, action }) });
      showToast(action === "cooked" ? "Nice — inventory updated." : "Got it, noted.");
      loadRecommendations();
    } catch (err) {
      showToast(`Couldn't log that: ${err.message}`);
    }
  }
});

document.getElementById("retrain-btn").addEventListener("click", async () => {
  try {
    const result = await apiRequest("/recommendations/retrain", { method: "POST" });
    showToast(result.trained ? "Ranker retrained on your history." : result.reason);
    if (result.trained) loadRecommendations();
  } catch (err) {
    showToast(`Retrain failed: ${err.message}`);
  }
});

// ---------- inventory ----------

function inventoryRowHtml(item) {
  const label = expiryLabel(item.days_until_expiry);
  const pillClass = label ? (item.days_until_expiry <= 2 ? "urgent" : label.cls) : "ok";
  return `
    <div class="inventory-row" data-item-id="${item.id}">
      <div>
        <div class="name">${escapeHtml(titleCase(item.ingredient.name))}</div>
      </div>
      <div class="qty">${item.quantity} ${escapeHtml(item.unit)}</div>
      <div class="storage">${escapeHtml(item.storage_location)}</div>
      <div class="expiry-pill ${pillClass}">${label ? label.text : "no expiry set"}</div>
      <button class="btn btn-small btn-danger" data-delete-id="${item.id}">Remove</button>
    </div>
  `;
}

async function loadInventory() {
  const list = document.getElementById("inventory-list");
  list.innerHTML = `<div class="empty-state">Loading...</div>`;
  try {
    const items = await apiRequest("/inventory");
    if (!items.length) {
      list.innerHTML = `<div class="empty-state">Your kitchen is empty. Add what you have above, or scan a receipt.</div>`;
      return;
    }
    list.innerHTML = items.map(inventoryRowHtml).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Couldn't load inventory: ${escapeHtml(err.message)}</div>`;
  }
}

document.getElementById("inventory-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("inv-name").value.trim();
  if (!name) return;
  const payload = {
    ingredient_name: name,
    quantity: parseFloat(document.getElementById("inv-qty").value) || 1,
    unit: document.getElementById("inv-unit").value.trim() || "unit",
    storage_location: document.getElementById("inv-storage").value,
  };
  const expiry = document.getElementById("inv-expiry").value;
  if (expiry) payload.expiry_date = expiry;

  try {
    await apiRequest("/inventory", { method: "POST", body: JSON.stringify(payload) });
    e.target.reset();
    document.getElementById("inv-qty").value = 1;
    document.getElementById("inv-unit").value = "unit";
    showToast(`Added ${name}.`);
    loadInventory();
  } catch (err) {
    showToast(`Couldn't add item: ${err.message}`);
  }
});

document.getElementById("inventory-list").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-delete-id]");
  if (!btn) return;
  try {
    await apiRequest(`/inventory/${btn.dataset.deleteId}`, { method: "DELETE" });
    loadInventory();
  } catch (err) {
    showToast(`Couldn't remove item: ${err.message}`);
  }
});

// ---------- recipes ----------

function recipeBrowseCardHtml(recipe) {
  return `
    <div class="recipe-card">
      <h3 class="recipe-title" data-recipe-id="${recipe.id}">${escapeHtml(recipe.title)}</h3>
      <p class="recipe-meta">${escapeHtml(recipe.cuisine)} · ${recipe.prep_time_minutes} min · ${recipe.calories ?? "?"} kcal</p>
      <div class="tag-row">${recipe.tags.split(",").filter(Boolean).map((t) => `<span class="tag">${escapeHtml(t.trim())}</span>`).join("")}</div>
    </div>
  `;
}

let allRecipesCache = [];

async function loadRecipes() {
  const list = document.getElementById("recipe-list");
  list.innerHTML = `<div class="empty-state">Loading...</div>`;
  try {
    allRecipesCache = await apiRequest("/recipes");
    document.getElementById("recipe-count").textContent = `${allRecipesCache.length} recipes in your library`;
    list.innerHTML = allRecipesCache.map(recipeBrowseCardHtml).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Couldn't load recipes: ${escapeHtml(err.message)}</div>`;
  }
}

document.getElementById("recipe-list").addEventListener("click", (e) => {
  const titleEl = e.target.closest(".recipe-title");
  if (titleEl) openRecipeModal(titleEl.dataset.recipeId);
});

document.getElementById("recipe-search").addEventListener("input", (e) => {
  const query = e.target.value.trim().toLowerCase();
  const filtered = allRecipesCache.filter((r) => r.title.toLowerCase().includes(query));
  document.getElementById("recipe-list").innerHTML = filtered.map(recipeBrowseCardHtml).join("");
});

// ---------- receipt scanning ----------

let scanCandidates = [];

function scanRowHtml(item, index) {
  return `
    <div class="scan-row" data-index="${index}">
      <input type="checkbox" ${item.matched_ingredient_name ? "checked" : ""} data-field="include">
      <div>
        <input type="text" value="${escapeHtml(item.matched_ingredient_name || "")}" placeholder="ingredient name" data-field="name">
        <div class="raw">from: "${escapeHtml(item.raw_text)}" (confidence ${Math.round(item.match_confidence * 100)}%)</div>
      </div>
      <input type="number" value="${item.quantity}" min="0" step="0.1" data-field="quantity">
      <input type="text" value="${escapeHtml(item.unit)}" data-field="unit">
      <span></span>
    </div>
  `;
}

document.getElementById("scan-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("scan-file");
  if (!fileInput.files.length) return;
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const resultsEl = document.getElementById("scan-results");
  resultsEl.innerHTML = `<div class="empty-state">Reading receipt...</div>`;
  try {
    const result = await apiRequest("/receipts/scan", { method: "POST", body: formData });
    scanCandidates = result.items;
    if (!scanCandidates.length) {
      resultsEl.innerHTML = `<div class="empty-state">Couldn't find any item lines on that receipt.</div>`;
      return;
    }
    resultsEl.innerHTML =
      scanCandidates.map(scanRowHtml).join("") +
      `<button class="btn btn-primary" id="confirm-scan-btn">Add checked items to inventory</button>`;
  } catch (err) {
    resultsEl.innerHTML = `<div class="empty-state">Scan failed: ${escapeHtml(err.message)}</div>`;
  }
});

document.getElementById("scan-results").addEventListener("click", async (e) => {
  if (e.target.id !== "confirm-scan-btn") return;
  const rows = document.querySelectorAll(".scan-row");
  const items = [];
  rows.forEach((row) => {
    const include = row.querySelector('[data-field="include"]').checked;
    const name = row.querySelector('[data-field="name"]').value.trim();
    if (!include || !name) return;
    items.push({
      ingredient_name: name,
      quantity: parseFloat(row.querySelector('[data-field="quantity"]').value) || 1,
      unit: row.querySelector('[data-field="unit"]').value.trim() || "unit",
      storage_location: "pantry",
    });
  });
  if (!items.length) {
    showToast("Nothing checked to add.");
    return;
  }
  try {
    await apiRequest("/receipts/confirm", { method: "POST", body: JSON.stringify({ items }) });
    showToast(`Added ${items.length} item(s) to inventory.`);
    document.getElementById("scan-results").innerHTML = "";
    document.getElementById("scan-form").reset();
  } catch (err) {
    showToast(`Couldn't add items: ${err.message}`);
  }
});

// ---------- preferences ----------

async function loadPreferences() {
  try {
    const prefs = await apiRequest("/preferences");
    document.getElementById("pref-goal").value = prefs.nutrition_goal;
    document.getElementById("pref-horizon").value = prefs.expiry_horizon_days;
    document.getElementById("pref-restrictions").value = prefs.dietary_restrictions.join(", ");
    document.getElementById("pref-disliked").value = prefs.disliked_ingredients.join(", ");
    const topCuisine = Object.entries(prefs.cuisine_weights).sort((a, b) => b[1] - a[1])[0];
    document.getElementById("pref-cuisine").value = topCuisine ? topCuisine[0] : "";
  } catch (err) {
    showToast(`Couldn't load preferences: ${err.message}`);
  }
}

document.getElementById("preferences-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const cuisine = document.getElementById("pref-cuisine").value;
  const payload = {
    nutrition_goal: document.getElementById("pref-goal").value,
    expiry_horizon_days: parseInt(document.getElementById("pref-horizon").value, 10) || 5,
    dietary_restrictions: document.getElementById("pref-restrictions").value.split(",").map((s) => s.trim()).filter(Boolean),
    disliked_ingredients: document.getElementById("pref-disliked").value.split(",").map((s) => s.trim()).filter(Boolean),
    cuisine_weights: cuisine ? { [cuisine]: 0.3 } : {},
  };
  try {
    await apiRequest("/preferences", { method: "PUT", body: JSON.stringify(payload) });
    showToast("Preferences saved.");
  } catch (err) {
    showToast(`Couldn't save preferences: ${err.message}`);
  }
});

// ---------- init ----------

loadRecommendations();
