/**
 * Content Engine ↔ Nautilus Bridge
 *
 * Runs on manus server. Periodically:
 * 1. Calls CE /api/scout to get topic suggestions
 * 2. Posts them as bounties to Nautilus /api/agent-market/bounties
 * 3. Polls Nautilus for completed bounties
 * 4. Sends completed articles back to CE /api/write for RAID-2 refinement
 *
 * Usage: npx tsx ce_nautilus_bridge.ts
 * PM2:   pm2 start ce_nautilus_bridge.ts --interpreter "npx tsx" --name ce-bridge
 */

const CE_URL = "http://localhost:3200";
const CE_KEY = "ce_chunxiao_1503f97eb6bc8874f8b0c2c4f7f112a3";
const NAUTILUS_URL = "https://www.nautilus.social";
const NAUTILUS_KEY = "naut-kairos-3a0877b8df38104542c062d84ab2bdb3"; // Kairos as coordinator

const POLL_INTERVAL = 10 * 60 * 1000; // 10 minutes

interface ScoutResult {
  topics: Array<{
    title: string;
    angle: string;
    framework: string;
    urgency: string;
  }>;
}

async function fetchJSON(url: string, options: RequestInit = {}) {
  const resp = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  return resp.json();
}

// Step 1: Get topics from Content Engine scout
async function getScoutTopics(): Promise<ScoutResult> {
  try {
    const result = await fetchJSON(`${CE_URL}/api/scout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${CE_KEY}` },
      body: JSON.stringify({ count: 3 }),
    });
    console.log(`[Scout] Got ${result.topics?.length || 0} topics`);
    return result;
  } catch (e) {
    console.error(`[Scout] Failed:`, e);
    return { topics: [] };
  }
}

// Step 2: Post topic as Nautilus bounty
async function createBounty(topic: { title: string; angle: string; framework: string }) {
  try {
    const result = await fetchJSON(`${NAUTILUS_URL}/api/agent-market/bounties`, {
      method: "POST",
      headers: { "X-Agent-Key": NAUTILUS_KEY },
      body: JSON.stringify({
        title: `研报: ${topic.title}`,
        description: `[BOUNTY by content-engine] 写一篇深度研报。\n角度: ${topic.angle}\n框架: ${topic.framework}\n要求: 2000字以上，有数据支撑，有原创观点。`,
        reward_nau: 30,
        task_type: "research_synthesis",
      }),
    });
    if (result.bounty_id) {
      console.log(`[Bounty] Created: ${result.bounty_id} — ${topic.title}`);
      return result.bounty_id;
    } else {
      console.log(`[Bounty] Failed:`, JSON.stringify(result).slice(0, 200));
      return null;
    }
  } catch (e) {
    console.error(`[Bounty] Failed:`, e);
    return null;
  }
}

// Step 3: Check for completed bounties
async function checkCompletedBounties() {
  try {
    const result = await fetchJSON(`${NAUTILUS_URL}/api/agent-market/bounties`);
    const bounties = result.bounties || [];
    // Find completed bounties that came from content-engine
    const completed = bounties.filter(
      (b: any) => b.status === "completed" && b.description?.includes("[BOUNTY by content-engine]")
    );
    return completed;
  } catch (e) {
    console.error(`[Check] Failed:`, e);
    return [];
  }
}

// Step 4: Send completed article to CE for RAID-2 refinement
async function submitToRAID2(title: string, draft: string) {
  try {
    const result = await fetchJSON(`${CE_URL}/api/write`, {
      method: "POST",
      headers: { Authorization: `Bearer ${CE_KEY}` },
      body: JSON.stringify({
        topic: title,
        draft,
        max_rounds: 3,
      }),
    });
    console.log(`[RAID-2] Submitted: ${title} → rounds: ${result.rounds || "?"}`);
    return result;
  } catch (e) {
    console.error(`[RAID-2] Failed:`, e);
    return null;
  }
}

// Main loop
async function bridge() {
  console.log(`[Bridge] Content Engine (${CE_URL}) ↔ Nautilus (${NAUTILUS_URL})`);
  console.log(`[Bridge] Poll interval: ${POLL_INTERVAL / 1000}s`);

  while (true) {
    try {
      // Scout new topics and create bounties
      const scout = await getScoutTopics();
      for (const topic of (scout.topics || []).slice(0, 2)) {
        await createBounty(topic);
      }

      // Check for completed bounties and send to RAID-2
      const completed = await checkCompletedBounties();
      for (const bounty of completed) {
        if (bounty.result_output) {
          await submitToRAID2(bounty.title, bounty.result_output);
        }
      }

      console.log(`[Bridge] Cycle done. Waiting ${POLL_INTERVAL / 1000}s...`);
    } catch (e) {
      console.error(`[Bridge] Error:`, e);
    }

    await new Promise((r) => setTimeout(r, POLL_INTERVAL));
  }
}

bridge();
