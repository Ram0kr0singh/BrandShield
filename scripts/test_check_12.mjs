import { spawn, execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const userDataDir = path.join(os.tmpdir(), "brandshield_chrome_profile_qa");
const screenshotsDir = path.resolve("screenshots/qa_checks");

const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const chrome = spawn(chromePath, [
  "--headless=new",
  "--remote-debugging-port=9222",
  "--no-sandbox",
  "--disable-gpu",
  `--user-data-dir=${userDataDir}`,
  "http://127.0.0.1:5173/"
]);

await new Promise((r) => setTimeout(r, 2000));

try {
  const listRes = await fetch("http://127.0.0.1:9222/json/list");
  const pages = await listRes.json();
  const page = pages.find(p => p.url.includes("5173")) || pages[0];
  const ws = new WebSocket(page.webSocketDebuggerUrl);

  let id = 1;
  const pending = new Map();

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(msg.error);
      else resolve(msg.result);
    }
  };

  await new Promise((resolve) => ws.onopen = resolve);

  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const msgId = id++;
    pending.set(msgId, { resolve, reject });
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });

  await send("Runtime.enable");
  await send("Page.enable");
  await new Promise((r) => setTimeout(r, 1500));

  const evalExpr = async (expr) => {
    const res = await send("Runtime.evaluate", {
      expression: expr,
      returnByValue: true,
      awaitPromise: true
    });
    return res.result?.value;
  };

  const takeScreenshot = async (name) => {
    const res = await send("Page.captureScreenshot", { format: "png" });
    const filePath = path.join(screenshotsDir, name);
    fs.writeFileSync(filePath, Buffer.from(res.data, "base64"));
    return filePath;
  };

  console.log("1. Initial state (backend up):");
  console.log("Cards on page:", await evalExpr("document.querySelectorAll('.source-card').length"));

  console.log("\n2. Stopping backend via NetTCPConnection PID...");
  try {
    execSync('powershell -Command "$conns = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue; if ($conns) { $conns | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"');
  } catch (e) {
    console.log("Kill err:", e.message);
  }
  await new Promise(r => setTimeout(r, 1500));

  // Check backend is actually down
  try {
    await fetch("http://127.0.0.1:8001/api/health");
    console.log("ERROR: Backend is still responding!");
  } catch {
    console.log("Confirmed: Backend is DOWN (fetch failed as expected).");
  }

  // Reload page
  console.log("\n3. Reloading page with backend DOWN...");
  await send("Page.reload", { ignoreCache: true });
  await new Promise(r => setTimeout(r, 2000));

  const downState = await evalExpr(`(() => {
    return {
      bodyText: document.body.innerText,
      unavailable: document.querySelector('.source-status-unavailable')?.innerText,
      loader: document.querySelector('.loader')?.innerText,
      viewError: document.querySelector('.view-error')?.innerText,
      hasButtons: Array.from(document.querySelectorAll('button')).map(b => b.innerText)
    };
  })()`);
  console.log("State with backend down:\n", JSON.stringify(downState, null, 2));
  await takeScreenshot("check_12_down.png");

  // Restart backend
  console.log("\n4. Restarting backend...");
  const child = spawn(".venv\\Scripts\\python.exe", ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8001"], {
    detached: true,
    stdio: "ignore"
  });
  child.unref();

  let ok = false;
  for (let i = 0; i < 15; i++) {
    await new Promise(r => setTimeout(r, 500));
    try {
      const res = await fetch("http://127.0.0.1:8001/api/health");
      if (res.ok) { ok = true; break; }
    } catch {}
  }
  console.log("Backend restarted:", ok);

  // Click Retry button
  console.log("\n5. Clicking Retry button...");
  await evalExpr(`(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const retryBtn = buttons.find(b => b.innerText.includes('Retry'));
    if (retryBtn) retryBtn.click();
  })()`);
  await new Promise(r => setTimeout(r, 2000));

  const recoveredState = await evalExpr(`(() => {
    return {
      bodyText: document.body.innerText.slice(0, 200),
      cardsCount: document.querySelectorAll('.source-card').length,
      firstCard: document.querySelectorAll('.source-card')[0]?.querySelector('.source-card-name')?.innerText,
      buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText)
    };
  })()`);
  console.log("State after clicking Retry:\n", JSON.stringify(recoveredState, null, 2));
  await takeScreenshot("check_12_recovered.png");

  ws.close();
} catch (e) {
  console.error("Test error:", e);
} finally {
  chrome.kill();
}

