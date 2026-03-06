import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { randomUUID } from "crypto";

const JAI_API_BASE = process.env.JAI_API_BASE || "http://127.0.0.1:8080";

export async function registerRoutes(app: Express): Promise<Server> {
  // put application routes here
  // prefix all routes with /api

  // use storage to perform CRUD operations on the storage interface
  // e.g. storage.insertUser(user) or storage.getUserByUsername(username)

  app.get("/api/health", async (_req, res, next) => {
    try {
      const r = await fetch(`${JAI_API_BASE}/api/health`);
      const j = await r.json();
      res.json(j);
    } catch (e: any) {
      next(e);
    }
  });

  app.post("/api/jai/text", async (req, res, next) => {
    try {
      const { text } = req.body || {};
      if (!text || typeof text !== "string") {
        res.status(400).json({ message: "text is required" });
        return;
      }
      const rid = randomUUID();
      const r = await fetch(`${JAI_API_BASE}/api/text`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-request-id": rid,
        },
        body: JSON.stringify({ text }),
      });
      const body = await r.json();
      res.status(r.status).json(body);
    } catch (e: any) {
      next(e);
    }
  });

  app.post("/api/jai/vision", async (req, res, next) => {
    try {
      const { image, prompt } = req.body || {};
      if (!image || typeof image !== "string") {
        res.status(400).json({ message: "image is required" });
        return;
      }

      const apiKey = process.env.OPENAI_API_KEY;
      if (!apiKey) {
        res
          .status(500)
          .json({ message: "OPENAI_API_KEY is not configured on the server" });
        return;
      }

      const model =
        process.env.OPENAI_VISION_MODEL ||
        process.env.OPENAI_MODEL ||
        "gpt-4o-mini";

      const r = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          messages: [
            {
              role: "user",
              content: [
                {
                  type: "text",
                  text:
                    typeof prompt === "string" && prompt.trim().length > 0
                      ? prompt
                      : "You are a state-of-the-art multimodal assistant. Carefully analyze this image. Describe what you see, read any visible text, and call out anything important or unusual.",
                },
                {
                  type: "image_url",
                  image_url: {
                    url: image,
                  },
                },
              ],
            },
          ],
        }),
      });

      const body = await r.json();
      if (!r.ok) {
        const message =
          (body && (body.error?.message || body.message)) ||
          `Vision request failed with status ${r.status}`;
        res.status(r.status).json({ message });
        return;
      }

      const content =
        body.choices?.[0]?.message?.content ??
        (typeof body.response === "string" ? body.response : "");

      res.status(200).json({ response: content });
    } catch (e: any) {
      next(e);
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
