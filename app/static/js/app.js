// This is the new JavaScript file.

function openEditBoxDialog(id, name) {
  document.getElementById('edit_box_id').value = id;
  document.getElementById('edit_box_name').value = name;
  document.getElementById('editBoxDialog').style.display = "flex";
}
function closeEditBoxDialog() {
  document.getElementById('editBoxDialog').style.display = "none";
}

if (document.getElementById('editBoxForm')) {
    document.getElementById('editBoxForm').onsubmit = async function(e) {
      e.preventDefault();
      const id = document.getElementById('edit_box_id').value;
      const name = document.getElementById('edit_box_name').value.trim();
      if (!name) return;
      const form = new URLSearchParams();
      form.append("name", name);
      try {
        const res = await fetch(`/box/${id}/edit`, {
          method: "POST",
          body: form
        });
        if (!res.ok) throw new Error();
        // Update im DOM:
        const boxDiv = document.getElementById(`box-${id}`);
        if (boxDiv) {
          const nameEl = boxDiv.querySelector(".box-name a");
          if (nameEl) nameEl.textContent = name;
        }
        closeEditBoxDialog();
      } catch {
        alert("Fehler beim Umbenennen.");
      }
    };
}

// --- Sortieren ---
function sortItems() {
  let select = document.getElementById('sort-items');
  if (!select) return;
  let mode = select.value;
  let list = document.getElementById('item-list');
  let items = Array.from(list.querySelectorAll('.item-entry'));

  items.sort(function(a, b) {
    if (mode === "name") {
      return a.dataset.name.localeCompare(b.dataset.name, 'de');
    } else if (mode === "quantity") {
      return parseInt(b.dataset.quantity) - parseInt(a.dataset.quantity);
    } else { // last_updated
      return parseFloat(b.dataset.updated) - parseFloat(a.dataset.updated);
    }
  });

  // Neu sortieren
  items.forEach(item => list.appendChild(item));
}
if (document.getElementById('sort-items')) {
    document.addEventListener("DOMContentLoaded", sortItems);
}


// --- Menge ändern ---
async function changeQty(id, delta) {
  const form = new URLSearchParams();
  form.append("delta", delta);
  try {
    const res = await fetch(`/item/${id}/change`, {
      method: "POST",
      body: form
    });
    if (!res.ok) throw new Error();
    const { new_quantity } = await res.json();
    document.getElementById(`qty-${id}`).value = new_quantity;

    // Update Daten-Attribute für Sortierung (z.B. letzte Änderung!)
    const entry = document.getElementById(`item-${id}`);
    if (entry) {
      // Reload last_updated per AJAX? (Optional, für Perfektionisten)
      // Für jetzt bleibt timestamp wie gehabt
      entry.dataset.quantity = new_quantity;
    }
    sortItems();
  } catch {
    alert("Fehler beim Ändern der Menge.");
  }
}

// --- Stückzahl exakt setzen ---
async function setQty(id) {
  const input = document.getElementById(`qty-${id}`);
  const qty = parseInt(input.value);
  if (isNaN(qty)) return;
  const form = new URLSearchParams();
  form.append("quantity", qty);
  try {
    const res = await fetch(`/item/${id}/set`, {
      method: "POST",
      body: form
    });
    if (!res.ok) throw new Error();
    const { new_quantity } = await res.json();
    input.value = new_quantity;

    // Update Daten-Attribute für Sortierung
    const entry = document.getElementById(`item-${id}`);
    if (entry) {
      entry.dataset.quantity = new_quantity;
    }
    sortItems();
  } catch {
    alert("Fehler beim Setzen der Menge.");
  }
}

// --- Bearbeiten --- //
function openEditDialog(id, name, category) {
  document.getElementById('edit_id').value = id;
  document.getElementById('edit_name').value = name;
  document.getElementById('edit_category').value = category || "";
  document.getElementById('editDialog').style.display = "flex";
}
function closeEditDialog() {
  document.getElementById('editDialog').style.display = "none";
}

// AJAX-submit Edit-Formular
if (document.getElementById('editForm')) {
    document.getElementById('editForm').onsubmit = async function(e) {
      e.preventDefault();
      const id = document.getElementById('edit_id').value;
      const name = document.getElementById('edit_name').value.trim();
      const category = document.getElementById('edit_category').value.trim();
      if (!name) return;
      const form = new URLSearchParams();
      form.append("name", name);
      form.append("category", category);
      try {
        const res = await fetch(`/item/${id}/edit`, {
          method: "POST",
          body: form
        });
        if (!res.ok) throw new Error();
        // Update im DOM:
        const entry = document.getElementById(`item-${id}`);
        if (entry) {
          entry.querySelector("strong").textContent = name;
          let catEl = entry.querySelector("small");
          if (catEl) {
            if (category)
              catEl.textContent = `(${category})`;
            else
              catEl.remove();
          } else if (category) {
            // Neues small anhängen, falls vorher keins
            let strong = entry.querySelector("strong");
            if (strong) {
              let sm = document.createElement("small");
              sm.style.color = "#aaa";
              sm.textContent = `(${category})`;
              strong.after(document.createTextNode(" "), sm);
            }
          }
        }
        closeEditDialog();
      } catch {
        alert("Fehler beim Bearbeiten.");
      }
    };
}


// --- Löschen ---
async function deleteItem(id) {
  if (!confirm("Diesen Eintrag wirklich löschen?")) return;
  try {
    const res = await fetch(`/item/${id}/delete`, { method: "POST" });
    if (!res.ok) throw new Error();
    document.getElementById(`item-${id}`).remove();
  } catch {
    alert("Fehler beim Löschen.");
  }
}
