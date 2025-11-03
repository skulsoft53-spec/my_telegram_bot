const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const cors = require("cors");

const app = express();
app.use(cors());
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// ✅ Игроки и роли
let players = {};
const OWNER_NAME = "Apachi_Ventowsky"; // 🔥 Владелец проекта

wss.on("connection", (ws) => {
  console.log("🔗 Новый игрок подключился");

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg);

      // 🔹 Когда игрок заходит
      if (data.type === "join") {
        let role = "player";
        if (data.name === OWNER_NAME) {
          role = "owner"; // 👑 делает владельца
        }
        players[data.id] = { x: 0, y: 0, name: data.name, role };
        console.log(`✅ ${data.name} вошёл в игру как ${role}`);
      }

      // 🔹 Движение
      if (data.type === "move") {
        if (players[data.id]) {
          players[data.id].x = data.x;
          players[data.id].y = data.y;
        }
      }

      // 🔹 Стрельба
      if (data.type === "shoot") {
        console.log(`🔫 ${data.name} стреляет`);
      }

      // 🔹 Команды (например, /kick, /ban)
      if (data.type === "command" && players[data.id]) {
        const player = players[data.id];
        const cmd = data.command;

        if (player.role === "owner") {
          console.log(`👑 Владелец (${player.name}) выполнил команду: ${cmd}`);
          // Тут можешь добавить обработку всех команд
        } else {
          console.log(`⚠️ ${player.name} попытался выполнить ${cmd}, но нет прав`);
        }
      }

      // 🔹 Отправляем текущее состояние всем
      const payload = JSON.stringify({ type: "state", players });
      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(payload);
        }
      });
    } catch (err) {
      console.log("Ошибка:", err.message);
    }
  });

  ws.on("close", () => console.log("❌ Игрок отключился"));
});

const PORT = process.env.PORT || 10000;
server.listen(PORT, () => console.log(`✅ Сервер запущен на порту ${PORT}`));
