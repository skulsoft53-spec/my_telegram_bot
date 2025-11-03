const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const cors = require("cors");

const app = express();
app.use(cors());
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let players = {};

wss.on("connection", (ws) => {
  console.log("🔗 Новый игрок подключился");

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg);

      if (data.type === "join") {
        players[data.id] = { x: 0, y: 0, name: data.name };
        console.log(`✅ ${data.name} вошёл в игру`);
      }

      if (data.type === "move") {
        if (players[data.id]) {
          players[data.id].x = data.x;
          players[data.id].y = data.y;
        }
      }

      if (data.type === "shoot") {
        console.log(`🔫 ${data.name} стреляет`);
      }

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