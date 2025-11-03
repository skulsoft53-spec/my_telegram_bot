const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const cors = require("cors");

const app = express();
app.use(cors());
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// =========================
// 🧩 Конфигурация ролей
// =========================
const ROLE_TABLE = {
  "Apachi_Ventowsky": "owner",  // 👑 Владелец
  "Admin_Junior": "admin_1",    // Младший админ
  "Admin_Moder": "admin_2",     // Модератор
  "Admin_Senior": "admin_3",    // Старший админ
  "Admin_Curator": "admin_4",   // Куратор
  "Admin_Deputy": "admin_5",    // Зам. главного
  "Admin_Chief": "admin_6",     // Главный админ
  "Tech_Support": "tech_1",     // Тех-специалист
  "Tech_Engineer": "tech_3",    // Старший тех
};

// =========================
// ⚙️ Правила команд по уровням
// =========================
const COMMAND_ACCESS = {
  kick: 1,      // /kick доступен с admin_1
  mute: 1,      // /mute доступен с admin_1
  warn: 2,      // /warn доступен с admin_2
  tp: 2,        // /tp доступен с admin_2
  ban: 3,       // /ban доступен с admin_3
  announce: 3,  // /announce доступен с admin_3
  setrole: 5,   // /setrole доступен с admin_5
  fixcap: "tech",
  restartzone: "tech"
};

let players = {};

// =========================
// 🔍 Проверка доступа
// =========================
function canUseCommand(role, command) {
  if (role === "owner") return true; // 👑 Владелец может всё
  if (!COMMAND_ACCESS[command]) return false;

  const required = COMMAND_ACCESS[command];

  // если команда техническая
  if (required === "tech" && role.startsWith("tech_")) return true;

  // если команда админская
  if (role.startsWith("admin_")) {
    const level = parseInt(role.split("_")[1]);
    return level >= required;
  }

  return false;
}

// =========================
// 🔊 Сервер WebSocket
// =========================
wss.on("connection", (ws) => {
  console.log("🔗 Новый игрок подключился");

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg);

      // 🟢 Вход в игру
      if (data.type === "join") {
        let role = "player";
        if (ROLE_TABLE[data.name]) role = ROLE_TABLE[data.name];
        players[data.id] = { x: 0, y: 0, name: data.name, role };
        console.log(`✅ ${data.name} вошёл как ${role}`);
      }

      // 🚶 Движение
      if (data.type === "move" && players[data.id]) {
        players[data.id].x = data.x;
        players[data.id].y = data.y;
      }

      // 🔫 Стрельба
      if (data.type === "shoot" && players[data.id]) {
        console.log(`🔫 ${players[data.id].name} стреляет`);
      }

      // 💬 Команды
      if (data.type === "command" && players[data.id]) {
        const player = players[data.id];
        const [cmd, ...args] = data.command.replace("/", "").split(" ");
        if (canUseCommand(player.role, cmd)) {
          console.log(`⚙️ ${player.name} (${player.role}) выполняет: /${cmd} ${args.join(" ")}`);

          // Пример базовых команд:
          if (cmd === "announce") {
            const text = args.join(" ");
            broadcast(`📢 Объявление от ${player.name}: ${text}`);
          }

          if (cmd === "kick") {
            const target = args[0];
            if (target && players[target]) {
              delete players[target];
              broadcast(`🚫 ${target} был кикнут администратором ${player.name}`);
            }
          }

          // Остальные команды реализуются по аналогии
        } else {
          console.log(`🚫 ${player.name} не имеет прав на /${cmd}`);
        }
      }

      // 📡 Рассылка состояния всем
      broadcastState();
    } catch (err) {
      console.log("Ошибка:", err.message);
    }
  });

  ws.on("close", () => console.log("❌ Игрок отключился"));
});

function broadcast(message) {
  const payload = JSON.stringify({ type: "chat", message });
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) client.send(payload);
  });
}

function broadcastState() {
  const payload = JSON.stringify({ type: "state", players });
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) client.send(payload);
  });
}

const PORT = process.env.PORT || 10000;
server.listen(PORT, () => console.log(`✅ Сервер запущен на порту ${PORT}`));
