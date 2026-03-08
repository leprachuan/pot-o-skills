#!/usr/bin/env node
/**
 * Proactive Watchers - Gemini runtime implementation (Node.js)
 *
 * Provides the same watcher functionality for Gemini-based agents.
 * Uses the shared Python core engine via subprocess calls for consistency.
 */

const { execSync, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");

const WATCHERS_DIR =
  process.env.WATCHERS_DIR ||
  path.join(require("os").homedir(), ".proactive-watchers");
const CORE_SCRIPT = path.join(__dirname, "..", "claude", "proactive_watchers.py");

class ProactiveWatchersCLI {
  constructor() {
    this.watchersDir = WATCHERS_DIR;
    this.watchersFile = path.join(this.watchersDir, "watchers.json");
    this.historyDir = path.join(this.watchersDir, "history");
    this._ensureDirs();
    this._activePollers = new Map();
  }

  _ensureDirs() {
    [this.watchersDir, this.historyDir].forEach((dir) => {
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    });
  }

  _loadWatchers() {
    if (!fs.existsSync(this.watchersFile)) return [];
    try {
      return JSON.parse(fs.readFileSync(this.watchersFile, "utf8")).watchers || [];
    } catch {
      return [];
    }
  }

  _saveWatchers(watchers) {
    fs.writeFileSync(
      this.watchersFile,
      JSON.stringify({ watchers, updated_at: Date.now() / 1000 }, null, 2)
    );
  }

  create(config) {
    if (!config.name || !config.url) {
      console.error("Error: name and url are required");
      process.exit(1);
    }
    const watchers = this._loadWatchers();
    if (watchers.some((w) => w.name === config.name)) {
      console.error(`Error: Watcher '${config.name}' already exists`);
      process.exit(1);
    }

    const watcher = {
      type: "url_change",
      condition: "value_changed",
      check_interval: 300,
      method: "GET",
      headers: {},
      enabled: true,
      created_at: Date.now() / 1000,
      on_trigger: {
        method: "log_only",
        prompt_template: "Watcher '{{watcher_name}}' triggered: {{reason}}",
      },
      ...config,
    };

    watchers.push(watcher);
    this._saveWatchers(watchers);
    console.log(`Created watcher: ${watcher.name}`);
    return watcher;
  }

  list() {
    const watchers = this._loadWatchers();
    if (!watchers.length) {
      console.log("No watchers defined.");
      return;
    }

    console.log(
      `${"NAME".padEnd(25)} ${"TYPE".padEnd(18)} ${"INTERVAL".padEnd(10)} ${"ENABLED".padEnd(8)}`
    );
    console.log("─".repeat(65));
    for (const w of watchers) {
      const interval = `${w.check_interval || 300}s`;
      const enabled = w.enabled !== false ? "yes" : "no";
      console.log(
        `${(w.name || "").padEnd(25)} ${(w.type || "url_change").padEnd(18)} ${interval.padEnd(10)} ${enabled.padEnd(8)}`
      );
    }
  }

  async test(name) {
    const watcher = this._loadWatchers().find((w) => w.name === name);
    if (!watcher) {
      console.error(`Watcher '${name}' not found`);
      process.exit(1);
    }

    console.log(`Testing watcher: ${name}`);
    console.log(`URL: ${watcher.url}`);

    try {
      const response = await this._fetchUrl(watcher);
      console.log(`Status: ${response.statusCode}`);
      console.log(`Response type: ${typeof response.data}`);

      if (watcher.trigger_field) {
        const value = this._extractField(response.data, watcher.trigger_field);
        console.log(`Field '${watcher.trigger_field}': ${JSON.stringify(value)}`);
      }

      const stateFile = path.join(this.historyDir, `${name}_state.json`);
      let prevState = {};
      if (fs.existsSync(stateFile)) {
        prevState = JSON.parse(fs.readFileSync(stateFile, "utf8"));
      }

      console.log(`Condition: ${watcher.condition}`);
      console.log(
        `Previous state: ${Object.keys(prevState).length ? "exists" : "none (first poll)"}`
      );
    } catch (err) {
      console.error(`Error: ${err.message}`);
      process.exit(1);
    }
  }

  async start(name) {
    if (name === "all") {
      const watchers = this._loadWatchers().filter((w) => w.enabled !== false);
      for (const w of watchers) {
        this._startPoller(w);
      }
      console.log(`Started ${watchers.length} watcher(s)`);
    } else {
      const watcher = this._loadWatchers().find((w) => w.name === name);
      if (!watcher) {
        console.error(`Watcher '${name}' not found`);
        process.exit(1);
      }
      this._startPoller(watcher);
      console.log(`Started watcher: ${name}`);
    }
  }

  stop(name) {
    if (name === "all") {
      for (const [n, timer] of this._activePollers) {
        clearInterval(timer);
      }
      const count = this._activePollers.size;
      this._activePollers.clear();
      console.log(`Stopped ${count} watcher(s)`);
    } else {
      const timer = this._activePollers.get(name);
      if (timer) {
        clearInterval(timer);
        this._activePollers.delete(name);
        console.log(`Stopped watcher: ${name}`);
      } else {
        console.error(`Watcher '${name}' is not running`);
      }
    }
  }

  delete(name) {
    this.stop(name);
    const watchers = this._loadWatchers().filter((w) => w.name !== name);
    this._saveWatchers(watchers);
    console.log(`Deleted watcher: ${name}`);
  }

  history(name, limit = 50) {
    const logFile = path.join(this.historyDir, `${name}.log`);
    if (!fs.existsSync(logFile)) {
      console.log(`No history for '${name}'`);
      return;
    }
    const lines = fs.readFileSync(logFile, "utf8").trim().split("\n");
    const events = lines
      .slice(-limit)
      .map((l) => {
        try { return JSON.parse(l); } catch { return null; }
      })
      .filter(Boolean);

    for (const e of events) {
      const ts = e.iso_time || "?";
      const triggered = e.triggered ? " TRIGGERED" : "";
      console.log(`[${ts}] ${e.type || "?"}${triggered}: ${e.reason || e.error || ""}`);
    }
  }

  _startPoller(watcher) {
    const name = watcher.name;
    if (this._activePollers.has(name)) return;

    const interval = (watcher.check_interval || 300) * 1000;

    const poll = async () => {
      try {
        const result = await this._fetchUrl(watcher);
        this._logEvent(name, {
          type: "poll",
          status_code: result.statusCode,
          triggered: false,
          reason: "Poll completed",
        });
      } catch (err) {
        this._logEvent(name, {
          type: "error",
          error: err.message,
        });
      }
    };

    poll();
    const timer = setInterval(poll, interval);
    this._activePollers.set(name, timer);
  }

  _fetchUrl(watcher) {
    return new Promise((resolve, reject) => {
      const url = new URL(watcher.url);
      const client = url.protocol === "https:" ? https : http;
      const options = {
        method: watcher.method || "GET",
        headers: watcher.headers || {},
        timeout: (watcher.timeout || 30) * 1000,
        rejectUnauthorized: watcher.verify_ssl !== false,
      };

      const req = client.request(url, options, (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          let data;
          try {
            data = JSON.parse(body);
          } catch {
            data = body;
          }
          resolve({ data, statusCode: res.statusCode, raw: body.slice(0, 5000) });
        });
      });

      req.on("error", reject);
      req.on("timeout", () => reject(new Error("Request timed out")));
      req.end();
    });
  }

  _extractField(data, fieldPath) {
    const parts = fieldPath.split(".");
    let current = data;
    for (const part of parts) {
      if (current == null) return null;
      if (typeof current === "object" && part in current) {
        current = current[part];
      } else if (Array.isArray(current)) {
        const idx = parseInt(part, 10);
        current = isNaN(idx) ? null : current[idx];
      } else {
        return null;
      }
    }
    return current;
  }

  _logEvent(name, event) {
    event.timestamp = Date.now() / 1000;
    event.iso_time = new Date().toISOString();
    const logFile = path.join(this.historyDir, `${name}.log`);
    fs.appendFileSync(logFile, JSON.stringify(event) + "\n");
  }
}

// CLI entry point
const args = process.argv.slice(2);
const cli = new ProactiveWatchersCLI();
const command = args[0];

function getArg(flag) {
  const idx = args.indexOf(flag);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : null;
}

(async () => {
  switch (command) {
    case "create": {
      const configPath = getArg("--config");
      if (configPath) {
        const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
        cli.create(config);
      } else {
        console.error("Usage: proactive_watchers.js create --config <file>");
      }
      break;
    }
    case "list":
      cli.list();
      break;
    case "test":
      await cli.test(getArg("--watcher") || args[1]);
      break;
    case "start":
      await cli.start(getArg("--watcher") || args[1] || "all");
      console.log("Watching... (Ctrl+C to stop)");
      break;
    case "stop":
      cli.stop(getArg("--watcher") || args[1] || "all");
      break;
    case "delete":
      cli.delete(getArg("--watcher") || args[1]);
      break;
    case "history":
      cli.history(getArg("--watcher") || args[1], parseInt(getArg("--limit") || "50", 10));
      break;
    default:
      console.log("Proactive Watchers (Gemini/Node.js)");
      console.log("Commands: create, list, test, start, stop, delete, history");
      console.log("Usage: node proactive_watchers.js <command> --watcher <name>");
  }
})();
