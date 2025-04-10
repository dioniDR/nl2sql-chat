let modoChat = true;
let consultasGuardadas = [];

// 🔁 Cambiar entre modos (chat/simple)
function alternarModo() {
  modoChat = !modoChat;
  document.getElementById("modoChat").className = modoChat ? "visible" : "hidden";
  document.getElementById("modoSimple").className = modoChat ? "hidden" : "block";
  document.getElementById("toggleModo").innerText = modoChat ? "Cambiar a modo simple" : "Cambiar a modo chat";
}

// 🧠 Pregunta desde el modo chat
function enviarPregunta() {
  const input = document.getElementById("pregunta");
  const pregunta = input.value.trim();
  if (!pregunta) return;

  // Mostrar loading
  const historial = document.getElementById("historial");
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "flex items-center space-x-2 my-4 text-gray-500";
  loadingDiv.innerHTML = `
    <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
    </svg>
    <span>Procesando consulta...</span>
  `;
  historial.appendChild(loadingDiv);

  fetch("http://localhost:8000/preguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pregunta })
  })
  .then(res => res.json())
  .then(data => {
    historial.removeChild(loadingDiv); // Remover indicador de carga
    mostrarEnHistorial(pregunta, data);
    input.value = ""; // limpiar input

    if (data.sql && !data.error) {
      guardarConsulta(pregunta, data.sql);
    }
  })
  .catch(error => {
    historial.removeChild(loadingDiv); // Remover indicador de carga
    const errorDiv = document.createElement("div");
    errorDiv.className = "bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded my-4";
    errorDiv.textContent = `Error: ${error.message}`;
    historial.appendChild(errorDiv);
  });
}

// ⚡ Pregunta directa desde modo simple
function enviarPreguntaSimple() {
  const input = document.getElementById("preguntaSimple");
  const pregunta = input.value.trim();
  if (!pregunta) return;

  // Mostrar loading
  const respuestaDiv = document.getElementById("respuestaSimple");
  respuestaDiv.innerHTML = `
    <div class="flex items-center space-x-2 text-gray-500">
      <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <span>Procesando consulta...</span>
    </div>
  `;

  fetch("http://localhost:8000/preguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pregunta })
  })
  .then(res => res.json())
  .then(data => {
    respuestaDiv.innerHTML = renderizarRespuesta(data);
    input.value = "";

    if (data.sql && !data.error) {
      guardarConsulta(pregunta, data.sql);
    }
  })
  .catch(error => {
    respuestaDiv.innerHTML = `
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        Error: ${error.message}
      </div>
    `;
  });
}

// 📋 Mostrar consulta y resultados en historial
function mostrarEnHistorial(pregunta, data) {
  const historial = document.getElementById("historial");
  const contenedor = document.createElement("div");
  contenedor.className = "mb-4 last:mb-0";

  contenedor.innerHTML = `
    <div class="bg-gray-100 p-3 rounded-lg mb-2">
      <p class="font-semibold">Tú:</p>
      <p>${pregunta}</p>
    </div>
    <div class="ml-4">
      <p class="font-semibold">SQL:</p>
      <div class="bg-gray-800 text-gray-200 p-3 rounded-lg my-2 overflow-x-auto">
        <code>${data.sql}</code>
      </div>
      <div class="mt-2">${renderizarRespuesta(data)}</div>
    </div>
    <hr class="my-4 border-gray-200">
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
