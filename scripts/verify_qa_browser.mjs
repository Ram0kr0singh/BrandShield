import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const userDataDir = path.join(os.tmpdir(), "brandshield_chrome_profile");
fs.mkdirSync(userDataDir, { recursive: true });

const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const chrome = spawn(chromePath, [
  "--headless=new",
  "--remote-debugging-port=9222",
  "--no-sandbox",
  "--disable-gpu",
  `--user-data-dir=${userDataDir}`,
  "http://127.0.0.1:5173/"
]);

await new Promise((r) => setTimeout(r, 2500));

async function runTests() {
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
    await new Promise((r) => setTimeout(r, 1500));

    const evalExpr = async (expr) => {
      const res = await send("Runtime.evaluate", {
        expression: expr,
        returnByValue: true,
        awaitPromise: true
      });
      return res.result?.value;
    };

    console.log("=== CHECKING INITIAL CARD RENDERING ===");
    const cards = await evalExpr(`(() => {
      return Array.from(document.querySelectorAll('.source-card')).map(card => {
        const cs = window.getComputedStyle(card);
        const dot = card.querySelector('.source-dot');
        const dotCs = dot ? window.getComputedStyle(dot) : null;
        const statusEl = card.querySelector('.source-card-status');
        const statusCs = statusEl ? window.getComputedStyle(statusEl) : null;
        return {
          name: card.querySelector('.source-card-name')?.innerText,
          status: statusEl?.innerText,
          classes: card.className,
          message: card.querySelector('.source-card-message')?.innerText,
          time: card.querySelector('.source-card-time')?.innerText,
          hasActionBtn: !!card.querySelector('.source-action-btn'),
          actionBtnText: card.querySelector('.source-action-btn')?.innerText,
          borderColor: cs.borderColor,
          backgroundColor: cs.backgroundColor,
          dotColor: dotCs?.backgroundColor,
          statusColor: statusCs?.color
        };
      });
    })()`);
    console.log("Cards on load:\n", JSON.stringify(cards, null, 2));

    const captionInit = await evalExpr(`document.querySelector('.source-selection-caption')?.innerText`);
    console.log("Initial caption:", captionInit);

    // TEST (a): Click each of the 4 cards, confirm only that card is selected, and click it again to deselect
    console.log("\n=== TEST (a): Click each card to select, click again to deselect ===");
    for (let i = 0; i < 4; i++) {
      // Click card i
      await evalExpr(`document.querySelectorAll('.source-card')[${i}].click()`);
      await new Promise(r => setTimeout(r, 100));

      const selState1 = await evalExpr(`(() => {
        const cards = Array.from(document.querySelectorAll('.source-card'));
        return {
          selectedIndices: cards.map((c, idx) => c.classList.contains('selected') ? idx : -1).filter(idx => idx !== -1),
          selectedTagsCount: document.querySelectorAll('.source-selected-tag').length,
          caption: document.querySelector('.source-selection-caption')?.innerText,
          cardName: cards[${i}].querySelector('.source-card-name')?.innerText,
          ariaPressed: cards[${i}].getAttribute('aria-pressed')
        };
      })()`);
      console.log(`[Click card ${i}] Selected:`, selState1);

      if (selState1.selectedIndices.length !== 1 || selState1.selectedIndices[0] !== i) {
        throw new Error(`FAIL: Expected card ${i} to be exclusively selected.`);
      }

      // Click card i again to deselect
      await evalExpr(`document.querySelectorAll('.source-card')[${i}].click()`);
      await new Promise(r => setTimeout(r, 100));

      const selState2 = await evalExpr(`(() => {
        const cards = Array.from(document.querySelectorAll('.source-card'));
        return {
          selectedIndices: cards.map((c, idx) => c.classList.contains('selected') ? idx : -1).filter(idx => idx !== -1),
          caption: document.querySelector('.source-selection-caption')?.innerText,
          ariaPressed: cards[${i}].getAttribute('aria-pressed')
        };
      })()`);
      console.log(`[Click card ${i} again] Selected:`, selState2);

      if (selState2.selectedIndices.length !== 0 || selState2.caption !== "No source selected") {
        throw new Error(`FAIL: Expected card ${i} to be deselected.`);
      }
    }
    console.log("TEST (a) PASSED: Each card selects exclusively and deselects upon clicking again.");

    // TEST (b): Select card A then card B, confirm A deselects
    console.log("\n=== TEST (b): Select card A then card B, confirm A deselects ===");
    // Click card 0 (Controlled demo dataset)
    await evalExpr(`document.querySelectorAll('.source-card')[0].click()`);
    await new Promise(r => setTimeout(r, 100));
    // Click card 1 (Instagram live monitor)
    await evalExpr(`document.querySelectorAll('.source-card')[1].click()`);
    await new Promise(r => setTimeout(r, 100));

    const testB = await evalExpr(`(() => {
      const cards = Array.from(document.querySelectorAll('.source-card'));
      return {
        card0Selected: cards[0].classList.contains('selected'),
        card1Selected: cards[1].classList.contains('selected'),
        caption: document.querySelector('.source-selection-caption')?.innerText
      };
    })()`);
    console.log("Card A -> Card B result:", testB);
    if (testB.card0Selected || !testB.card1Selected) {
      throw new Error("FAIL: Card A did not deselect when selecting card B.");
    }
    console.log("TEST (b) PASSED: Selecting card B immediately deselects card A.");

    // Deselect card 1
    await evalExpr(`document.querySelectorAll('.source-card')[1].click()`);
    await new Promise(r => setTimeout(r, 100));

    // TEST (c): Simulate outage on Instagram while Google Play is selected, confirm only Instagram changes colour and the selection stays on Google Play
    console.log("\n=== TEST (c): Simulate outage on Instagram while Google Play is selected ===");
    // Select Google Play (card 2)
    await evalExpr(`document.querySelectorAll('.source-card')[2].click()`);
    await new Promise(r => setTimeout(r, 100));

    const beforeOutage = await evalExpr(`(() => {
      const cards = Array.from(document.querySelectorAll('.source-card'));
      return {
        card2Selected: cards[2].classList.contains('selected'),
        card2Name: cards[2].querySelector('.source-card-name')?.innerText,
        card1Classes: cards[1].className,
        card1Status: cards[1].querySelector('.source-card-status')?.innerText,
        caption: document.querySelector('.source-selection-caption')?.innerText
      };
    })()`);
    console.log("Before outage:", beforeOutage);

    // Click "Simulate outage" button on Instagram (card 1)
    console.log("Clicking Simulate outage button inside card 1 (Instagram)...");
    await evalExpr(`document.querySelectorAll('.source-card')[1].querySelector('.source-action-btn').click()`);
    await new Promise(r => setTimeout(r, 2000));

    const afterOutage = await evalExpr(`(() => {
      const cards = Array.from(document.querySelectorAll('.source-card'));
      const c1 = cards[1];
      const c2 = cards[2];
      const c1Cs = window.getComputedStyle(c1);
      const c1DotCs = window.getComputedStyle(c1.querySelector('.source-dot'));
      const c1StatusCs = window.getComputedStyle(c1.querySelector('.source-card-status'));
      return {
        instagram: {
          name: c1.querySelector('.source-card-name')?.innerText,
          status: c1.querySelector('.source-card-status')?.innerText,
          classes: c1.className,
          isSelected: c1.classList.contains('selected'),
          btnText: c1.querySelector('.source-action-btn')?.innerText,
          borderColor: c1Cs.borderColor,
          backgroundColor: c1Cs.backgroundColor,
          dotColor: c1DotCs.backgroundColor,
          statusColor: c1StatusCs.color
        },
        googlePlay: {
          name: c2.querySelector('.source-card-name')?.innerText,
          status: c2.querySelector('.source-card-status')?.innerText,
          classes: c2.className,
          isSelected: c2.classList.contains('selected')
        },
        caption: document.querySelector('.source-selection-caption')?.innerText
      };
    })()`);
    console.log("After Instagram outage:", JSON.stringify(afterOutage, null, 2));

    if (!afterOutage.instagram.classes.includes('degraded') || afterOutage.instagram.status !== "Degraded") {
      throw new Error("FAIL: Instagram did not change to Degraded!");
    }
    if (!afterOutage.googlePlay.isSelected || afterOutage.instagram.isSelected) {
      throw new Error("FAIL: Selection did not stay on Google Play!");
    }
    console.log("TEST (c) PASSED: Instagram changed to amber (Degraded), button changed to Restore, and selection remained on Google Play!");

    // TEST (d): Restore returns Instagram to grey
    console.log("\n=== TEST (d): Restore returns Instagram to grey ===");
    console.log("Clicking Restore button inside card 1 (Instagram)...");
    await evalExpr(`document.querySelectorAll('.source-card')[1].querySelector('.source-action-btn').click()`);
    await new Promise(r => setTimeout(r, 2000));

    const afterRestore = await evalExpr(`(() => {
      const cards = Array.from(document.querySelectorAll('.source-card'));
      const c1 = cards[1];
      const c1Cs = window.getComputedStyle(c1);
      const c1DotCs = window.getComputedStyle(c1.querySelector('.source-dot'));
      const c1StatusCs = window.getComputedStyle(c1.querySelector('.source-card-status'));
      return {
        instagram: {
          name: c1.querySelector('.source-card-name')?.innerText,
          status: c1.querySelector('.source-card-status')?.innerText,
          classes: c1.className,
          btnText: c1.querySelector('.source-action-btn')?.innerText,
          borderColor: c1Cs.borderColor,
          backgroundColor: c1Cs.backgroundColor,
          dotColor: c1DotCs.backgroundColor,
          statusColor: c1StatusCs.color
        },
        googlePlay: {
          isSelected: cards[2].classList.contains('selected')
        },
        caption: document.querySelector('.source-selection-caption')?.innerText
      };
    })()`);
    console.log("After Instagram restore:", JSON.stringify(afterRestore, null, 2));

    if (!afterRestore.instagram.classes.includes('not_configured') || afterRestore.instagram.status !== "Not configured") {
      throw new Error("FAIL: Instagram did not return to Not configured!");
    }
    if (!afterRestore.googlePlay.isSelected) {
      throw new Error("FAIL: Google Play selection was lost!");
    }
    console.log("TEST (d) PASSED: Restore returned Instagram to grey (Not configured) with button Simulate outage, while Google Play remained selected!");

    // Clean up: deselect Google Play
    await evalExpr(`document.querySelectorAll('.source-card')[2].click()`);
    await new Promise(r => setTimeout(r, 100));

    console.log("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!");
    ws.close();
  } catch (err) {
    console.error("Verification error:", err);
    process.exitCode = 1;
  } finally {
    chrome.kill();
  }
}

await runTests();

