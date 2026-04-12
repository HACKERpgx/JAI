import type { Express } from "express";
import { createServer, type Server } from "http";
import { memoryService } from "./services/memoryService";

export async function registerRoutes(app: Express): Promise<Server> {
  // Legacy API endpoints for backward compatibility with app.js
  app.post("/api/text", async (req, res) => {
    try {
      const { text } = req.body;
      if (!text) {
        return res.status(400).json({ error: "Missing text" });
      }
      
      // Get or create default session
      let sessionId = parseInt(req.headers['x-session-id'] as string) || 1;
      try {
        await memoryService.getSession(sessionId);
      } catch {
        const session = await memoryService.createSession();
        sessionId = session.id;
      }
      
      const result = await memoryService.sendMessage(sessionId, text);
      res.json({ 
        response: result.assistantMessage.content,
        sessionId: sessionId
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/messages/:sessionId", async (req, res) => {
    try {
      const sessionId = parseInt(req.params.sessionId);
      const session = await memoryService.getSession(sessionId);
      if (!session) return res.status(404).json({ error: "Session not found" });
      
      const messages = session.messages.reverse().map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.createdAt
      }));
      
      res.json({ messages, sessionId });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

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

  // Voice API endpoint (placeholder - would need speech-to-text integration)
  app.post("/api/voice", async (req, res) => {
    try {
      // For now, just return a placeholder response
      // In a real implementation, this would process the audio file
      const transcript = "Voice message received (placeholder transcript)";
      
      // Get or create default session
      let sessionId = parseInt(req.headers['x-session-id'] as string) || 1;
      try {
        await memoryService.getSession(sessionId);
      } catch {
        const session = await memoryService.createSession();
        sessionId = session.id;
      }
      
      const result = await memoryService.sendMessage(sessionId, transcript);
      res.json({ 
        transcript: transcript,
        response: result.assistantMessage.content,
        sessionId: sessionId
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Health check endpoint
  app.get("/api/health", async (_req, res) => {
    try {
      res.json({ 
        ok: true, 
        time: new Date().toISOString(),
        version: "1.0.0"
      });
    } catch (error: any) {
      res.status(500).json({ ok: false, error: error.message });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
