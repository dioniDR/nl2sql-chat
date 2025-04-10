let modoChat = true;
let consultasGuardadas = [];

// 🔁 Cambiar entre modos (chat/simple)
function alternarModo() {
  modoChat = !modoChat;
  document.getElementById("modoChat").className = modoChat ? "visible" : "oculto";
  document.getElementById("modoSimple").className = modoChat ? "oculto" : "visible";
  document.getElementById("toggleModo").innerText = modoChat ? "Cambiar a modo simple" : "Cambiar a modo chat";
}

// 🧠 Pregunta desde el modo chat
function enviarPregunta() {
  const input = document.getElementById("pregunta");
  const pregunta = input.value.trim();
  if (!pregunta) return;

  fetch("http://localhost:8000/preguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pregunta })
  })
  .then(res => res.json())
  .then(data => {
    mostrarEnHistorial(pregunta, data);
    input.value = ""; // limpiar input

    if (data.sql && !data.error) {
      guardarConsulta(pregunta, data.sql);
    }
  });
}

// ⚡ Pregunta directa desde modo simple
function enviarPreguntaSimple() {
  const input = document.getElementById("preguntaSimple");
  const pregunta = input.value.trim();
  if (!pregunta) return;

  fetch("http://localhost:8000/preguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pregunta })
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("respuestaSimple").innerHTML = renderizarRespuesta(data);
    input.value = "";

    if (data.sql && !data.error) {
      guardarConsulta(pregunta, data.sql);
    }
  });
}

// 📋 Mostrar consulta y resultados en historial
function mostrarEnHistorial(pregunta, data) {
  const historial = document.getElementById("historial");
  const contenedor = document.createElement("div");

  contenedor.innerHTML = `
    <p><strong>Tú:</strong> ${pregunta}</p>
    <p><strong>SQL:</strong> <code>${data.sql}</code></p>
    <div>${renderizarRespuesta(data)}</div>
    <hr>
  `;

  historial.appendChild(contenedor);
  historial.scrollTop = historial.scrollHeight;
}

// 🧾 Formatea resultados como tabla
function renderizarRespuesta(data) {
  if (data.error) {
    return `<p style="color: red;">❌ Error: ${data.error}</p>`;
  }

  if (!data.resultados || data.resultados.length === 0) {
    return `<p>✅ Consulta ejecutada. Sin resultados.</p>`;
  }

  const columnas = Object.keys(data.resultados[0]);
  const filasHTML = data.resultados.map(row =>
    `<tr>${columnas.map(col => `<td>${row[col]}</td>`).join("")}</tr>`
  ).join("");

  const encabezado = columnas.map(col => `<th>${col}</th>`).join("");

  return `
    <table class="tabla-resultado">
      <thead><tr>${encabezado}</tr></thead>
      <tbody>${filasHTML}</tbody>
    </table>
  `;
}

// 💾 Guardar una consulta en el to-do list
function guardarConsulta(desc, sql) {
  const nueva = { desc, sql };
  consultasGuardadas.push(nueva);
  console.log("Guardando consulta:", nueva);
  renderizarConsultas();
  guardarEnLocal();
}

// 📤 Guardar en localStorage
function guardarEnLocal() {
  localStorage.setItem("consultasGuardadas", JSON.stringify(consultasGuardadas));
}

// 📥 Cargar desde localStorage al iniciar
function cargarConsultasGuardadas() {
  const guardadas = localStorage.getItem("consultasGuardadas");
  if (guardadas) {
    consultasGuardadas = JSON.parse(guardadas);
    renderizarConsultas();
  }
}

// 🧾 Mostrar lista de consultas guardadas
function renderizarConsultas() {
  const ul = document.getElementById("listaConsultas");
  ul.innerHTML = "";

  consultasGuardadas.forEach((c, i) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span title="${c.sql}">${c.desc}</span>
      <button onclick="ejecutarGuardada(${i})">▶️</button>
      <button onclick="eliminarConsulta(${i})">🗑️</button>
    `;
    ul.appendChild(li);
  });
}

// ▶️ Ejecutar una consulta guardada directamente (sin OpenAI)
function ejecutarGuardada(i) {
  const { sql, desc } = consultasGuardadas[i];
  fetch("http://localhost:8000/preguntar-sql", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql })
  })
  .then(res => res.json())
  .then(data => {
    if (modoChat) {
      mostrarEnHistorial(desc + " (guardada)", { sql, ...data });
    } else {
      document.getElementById("respuestaSimple").innerHTML = renderizarRespuesta({ sql, ...data });
    }
  });
}

// 🧽 Eliminar una consulta del historial guardado
function eliminarConsulta(i) {
  consultasGuardadas.splice(i, 1);
  renderizarConsultas();
  guardarEnLocal();
}

// 🧭 Mostrar/ocultar el panel de guardadas
function alternarPanel() {
  const panel = document.getElementById("consultasGuardadas");
  panel.style.display = (panel.style.display === "none") ? "block" : "none";
}

// 🔁 Cargar historial al iniciar
window.onload = () => {
  cargarConsultasGuardadas();
};
