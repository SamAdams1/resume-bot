#!/usr/bin/env node

const { spawn, exec } = require("child_process");
const path = require("path");
const os = require("os");

const isWindows = os.platform() === "win32";

// Colors for console output
const colors = {
  reset: "\x1b[0m",
  cyan: "\x1b[36m",
  green: "\x1b[32m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
};

function log(message, color = "reset") {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function runCommand(command, cwd, name) {
  return new Promise((resolve, reject) => {
    log(`\n📦 Starting ${name}...`, "cyan");

    const child = spawn(command, [], {
      cwd,
      shell: true,
      stdio: "inherit",
      env: { ...process.env, FORCE_COLOR: "1" },
    });

    child.on("error", (error) => {
      log(`❌ Error starting ${name}: ${error.message}`, "red");
      reject(error);
    });

    child.on("exit", (code) => {
      if (code !== 0 && code !== null) {
        log(`⚠️  ${name} exited with code ${code}`, "yellow");
      }
      resolve();
    });
  });
}

async function startAll() {
  const projectRoot = __dirname;
  const backendRoot = path.join(projectRoot, "backend");
  const frontendRoot = path.join(projectRoot, "frontend");

  log("\n🚀 Starting applyJobs application...", "green");
  log("═══════════════════════════════════════", "green");

  try {
    // Start Docker services
    log("\n1️⃣  Starting Docker services (database & search)...", "cyan");
    const dockerCommand = isWindows
      ? "docker-compose up -d"
      : "docker compose up -d";

    await new Promise((resolve, reject) => {
      exec(dockerCommand, { cwd: projectRoot }, (error, stdout, stderr) => {
        if (error) {
          log(`❌ Docker error: ${error.message}`, "red");
          reject(error);
        } else {
          log("✅ Docker services started", "green");
          resolve();
        }
      });
    });

    // Start Backend
    const backendCommand = isWindows
      ? "venv\\Scripts\\activate.bat && uvicorn backend.src.server:app --reload"
      : "source venv/Scripts/activate && uvicorn backend.src.server:app --reload";

    const backendPromise = runCommand(
      backendCommand,
      projectRoot,
      "Backend (FastAPI)",
    );

    // Start Frontend
    const frontendPromise = runCommand(
      "npm start",
      frontendRoot,
      "Frontend (Angular)",
    );

    log("\n✨ Application is starting...", "green");
    log("═══════════════════════════════════════", "green");
    log("📍 Backend: http://localhost:8000", "cyan");
    log("📍 Frontend: http://localhost:4200", "cyan");
    log("📍 Search Engine (Searxng): http://localhost:8080", "cyan");
    log("\nPress Ctrl+C to stop all services\n", "yellow");

    // Wait for both services to complete
    await Promise.all([backendPromise, frontendPromise]);
  } catch (error) {
    log(`\n❌ Failed to start application: ${error.message}`, "red");
    process.exit(1);
  }
}

async function stopAll() {
  const projectRoot = __dirname;

  log("\n🛑 Stopping applyJobs application...", "yellow");
  log("═══════════════════════════════════════", "yellow");

  try {
    const dockerCommand = isWindows
      ? "docker-compose down"
      : "docker compose down";

    await new Promise((resolve) => {
      exec(dockerCommand, { cwd: projectRoot }, (error) => {
        if (error) {
          log(`⚠️  Docker stop warning: ${error.message}`, "yellow");
        } else {
          log("✅ Docker services stopped", "green");
        }
        resolve();
      });
    });

    log("✨ All services stopped", "green");
  } catch (error) {
    log(`Error stopping services: ${error.message}`, "red");
  }
}

async function setup() {
  const projectRoot = __dirname;
  const backendRoot = path.join(projectRoot, "backend");
  const frontendRoot = path.join(projectRoot, "frontend");

  log("\n📋 Setting up applyJobs project...", "green");
  log("═══════════════════════════════════════", "green");

  try {
    // Install frontend dependencies
    log("\n1️⃣  Installing frontend dependencies...", "cyan");
    await new Promise((resolve, reject) => {
      exec("npm install", { cwd: frontendRoot, stdio: "inherit" }, (error) => {
        if (error) {
          reject(error);
        } else {
          log("✅ Frontend dependencies installed", "green");
          resolve();
        }
      });
    });

    log("\n✨ Setup complete!", "green");
    log("You can now run: npm start", "cyan");
  } catch (error) {
    log(`\n❌ Setup failed: ${error.message}`, "red");
    process.exit(1);
  }
}

// CLI Handler
const command = process.argv[2];

switch (command) {
  case "start":
    startAll().catch(() => process.exit(1));
    break;
  case "stop":
    stopAll().catch(() => process.exit(1));
    break;
  case "setup":
    setup().catch(() => process.exit(1));
    break;
  default:
    log("applyJobs CLI", "green");
    log("═════════════════════════════════", "green");
    log("\nUsage: app [command]", "cyan");
    log("\nCommands:", "yellow");
    log("  start    Start all services (backend, frontend, database)", "cyan");
    log("  stop     Stop all services", "cyan");
    log("  setup    Install dependencies", "cyan");
    log("\nExamples:", "yellow");
    log("  app start", "cyan");
    log("  npm start", "cyan");
    process.exit(0);
}
