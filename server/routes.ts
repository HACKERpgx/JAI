import type { Express } from "express";
import { createServer, type Server } from "http";
import { memoryService } from "./services/memoryService";

export async function registerRoutes(app: Express): Promise<Server> {
  // Chat API routes
  app.post("/api/chat/send", async (req, res) => {
    try {
      const { sessionId, message } = req.body;
      if (!sessionId || !message) {
        return res.status(400).json({ error: "Missing sessionId or message" });
      }
      const result = await memoryService.sendMessage(parseInt(sessionId), message);
      res.json(result);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/chat/session", async (req, res) => {
    try {
      const { personaId, lorebookId } = req.body;
      const session = await memoryService.createSession(personaId, lorebookId);
      res.json(session);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/chat/session/:id", async (req, res) => {
    try {
      const session = await memoryService.getSession(parseInt(req.params.id));
      if (!session) return res.status(404).json({ error: "Session not found" });
      res.json(session);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/chat/sessions", async (_req, res) => {
    try {
      const sessions = await memoryService.getAllSessions();
      res.json(sessions);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/personas", async (_req, res) => {
    try {
      const personas = await memoryService.getAllPersonas();
      res.json(personas);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
