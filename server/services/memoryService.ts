import { db } from "../../server/db";
import { 
  personas, lorebooks, lorebookEntries, chatSessions, chatMessages,
  type Persona, type Lorebook, type LorebookEntry, type ChatSession, type ChatMessage 
} from "../../shared/memorySchema";
import { eq, and, desc, sql } from "drizzle-orm";
import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";

export class MemoryService {
  private contextAssembler: any;
  private retrievalPipeline: any;

  constructor() {
    // Placeholder implementations
    this.contextAssembler = {
      assembleContext: (data: any) => ({
        systemPrompt: "You are a helpful AI assistant.",
        totalTokens: 1000,
        activeLoreEntries: []
      }),
      countTokens: (text: string) => Math.ceil(text.length / 4)
    };
    this.retrievalPipeline = {
      retrieve: async (query: string, lorebookId: number, pinned: any[]) => ({
        dynamic: []
      }),
      storeEmbedding: async (id: number, content: string) => {}
    };
  }

  // Persona CRUD
  async createPersona(data: Partial<Persona>): Promise<Persona> {
    const [persona] = await db.insert(personas).values({
      name: data.name!,
      description: data.description,
      backstory: data.backstory || "",
      personalityTraits: data.personalityTraits || [],
      speechStyle: data.speechStyle,
      knowledgeScope: data.knowledgeScope || [],
      forbiddenTopics: data.forbiddenTopics || [],
      systemPromptTemplate: data.systemPromptTemplate,
      isDefault: data.isDefault || false,
    }).returning();
    return persona;
  }

  async getPersona(id: number): Promise<Persona | undefined> {
    return await db.query.personas.findFirst({ where: eq(personas.id, id) });
  }

  async getAllPersonas(): Promise<Persona[]> {
    return await db.query.personas.findMany({ orderBy: desc(personas.updatedAt) });
  }

  async updatePersona(id: number, data: Partial<Persona>): Promise<Persona> {
    const [updated] = await db.update(personas)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(personas.id, id))
      .returning();
    return updated;
  }

  async deletePersona(id: number): Promise<void> {
    await db.delete(personas).where(eq(personas.id, id));
  }

  // Lorebook CRUD
  async createLorebook(data: Partial<Lorebook>): Promise<Lorebook> {
    const [lorebook] = await db.insert(lorebooks).values({
      name: data.name!,
      description: data.description,
    }).returning();
    return lorebook;
  }

  async getLorebook(id: number): Promise<(Lorebook & { entries: LorebookEntry[] }) | undefined> {
    const result = await db.query.lorebooks.findFirst({
      where: eq(lorebooks.id, id),
      with: { entries: true },
    });
    return result as any;
  }

  async getAllLorebooks(): Promise<Lorebook[]> {
    return await db.query.lorebooks.findMany({ orderBy: desc(lorebooks.updatedAt) });
  }

  async updateLorebook(id: number, data: Partial<Lorebook>): Promise<Lorebook> {
    const [updated] = await db.update(lorebooks)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(lorebooks.id, id))
      .returning();
    return updated;
  }

  async deleteLorebook(id: number): Promise<void> {
    await db.delete(lorebooks).where(eq(lorebooks.id, id));
  }

  // Lorebook Entry CRUD
  async createEntry(lorebookId: number, data: Partial<LorebookEntry>): Promise<LorebookEntry> {
    const [entry] = await db.insert(lorebookEntries).values({
      lorebookId,
      title: data.title!,
      content: data.content!,
      tags: data.tags || [],
      triggerKeywords: data.triggerKeywords || [],
      priorityWeight: data.priorityWeight || 1.0,
      isPinned: data.isPinned || false,
    }).returning();

    // Generate embedding for the entry
    const content = `${entry.title}\n${entry.content}`;
    await this.retrievalPipeline.storeEmbedding(entry.id, content);

    return entry;
  }

  async updateEntry(id: number, data: Partial<LorebookEntry>): Promise<LorebookEntry> {
    const [updated] = await db.update(lorebookEntries)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(lorebookEntries.id, id))
      .returning();

    // Update embedding if content changed
    if (data.title || data.content) {
      const content = `${updated.title}\n${updated.content}`;
      await this.retrievalPipeline.storeEmbedding(updated.id, content);
    }

    return updated;
  }

  async deleteEntry(id: number): Promise<void> {
    await db.delete(lorebookEntries).where(eq(lorebookEntries.id, id));
  }

  // Chat Session
  async createSession(personaId?: number, lorebookId?: number): Promise<ChatSession> {
    const [session] = await db.insert(chatSessions).values({
      title: "New Chat",
      personaId,
      lorebookId,
    }).returning();
    return session;
  }

  async getSession(id: number): Promise<(ChatSession & { messages: ChatMessage[] }) | undefined> {
    return await db.query.chatSessions.findFirst({
      where: eq(chatSessions.id, id),
      with: { messages: { orderBy: desc(chatMessages.createdAt), limit: 50 } },
    }) as any;
  }

  async getAllSessions(): Promise<ChatSession[]> {
    return await db.query.chatSessions.findMany({
      where: eq(chatSessions.isActive, true),
      orderBy: desc(chatSessions.updatedAt),
    });
  }

  // Message handling with context assembly
  async sendMessage(sessionId: number, userMessage: string): Promise<{ 
    assistantMessage: ChatMessage; 
    contextTokens: number; 
    activeLoreCount: number;
  }> {
    const session = await this.getSession(sessionId);
    if (!session) throw new Error("Session not found");

    // Get persona
    const persona = session.personaId ? await this.getPersona(session.personaId) : undefined;

    // Get lorebook entries
    let pinnedEntries: LorebookEntry[] = [];
    let dynamicEntries: any[] = [];

    if (session.lorebookId) {
      const allEntries = await db.query.lorebookEntries.findMany({
        where: and(
          eq(lorebookEntries.lorebookId, session.lorebookId),
          eq(lorebookEntries.isActive, true)
        ),
      });

      pinnedEntries = allEntries.filter((e: LorebookEntry) => e.isPinned);
      const result = await this.retrievalPipeline.retrieve(userMessage, session.lorebookId, pinnedEntries);
      dynamicEntries = result.dynamic;
    }

    // Build context
    const chatHistory = session.messages?.slice(-20).reverse().map((m: ChatMessage) => ({ role: m.role, content: m.content })) || [];
    
    const assembly = this.contextAssembler.assembleContext({
      persona,
      pinnedLore: pinnedEntries,
      dynamicLore: dynamicEntries as any,
      chatHistory,
      userMessage,
    });

    // Generate AI response
    const { text } = await generateText({
      model: openai("gpt-4o"),
      system: assembly.systemPrompt,
      messages: [...chatHistory, { role: "user", content: userMessage }],
    });

    // Store messages
    await db.insert(chatMessages).values({
      sessionId,
      role: "user",
      content: userMessage,
      tokensUsed: this.contextAssembler.countTokens(userMessage),
    });

    const [assistantMessage] = await db.insert(chatMessages).values({
      sessionId,
      role: "assistant",
      content: text,
      tokensUsed: this.contextAssembler.countTokens(text),
      loreEntriesUsed: assembly.activeLoreEntries,
    }).returning();

    // Update session stats
    await db.update(chatSessions)
      .set({
        messageCount: sql`${chatSessions.messageCount} + 2`,
        contextTokenCount: assembly.totalTokens,
        updatedAt: new Date(),
      })
      .where(eq(chatSessions.id, sessionId));

    return {
      assistantMessage,
      contextTokens: assembly.totalTokens,
      activeLoreCount: assembly.activeLoreEntries.length,
    };
  }

  // Export/Import
  async exportLorebook(lorebookId: number): Promise<any> {
    const lorebook = await this.getLorebook(lorebookId);
    if (!lorebook) throw new Error("Lorebook not found");

    return {
      name: lorebook.name,
      description: lorebook.description,
      version: "1.0",
      exportedAt: new Date().toISOString(),
      entries: lorebook.entries.map((e: LorebookEntry) => ({
        title: e.title,
        content: e.content,
        tags: e.tags,
        triggerKeywords: e.triggerKeywords,
        priorityWeight: e.priorityWeight,
        isPinned: e.isPinned,
      })),
    };
  }

  async importLorebook(data: any): Promise<Lorebook> {
    const lorebook = await this.createLorebook({
      name: data.name,
      description: data.description,
    });

    for (const entry of data.entries || []) {
      await this.createEntry(lorebook.id, entry);
    }

    return lorebook;
  }

  // Conflict detection
  async detectConflicts(lorebookId: number): Promise<Array<{ entry1: LorebookEntry; entry2: LorebookEntry; reason: string }>> {
    const entries = await db.query.lorebookEntries.findMany({
      where: and(eq(lorebookEntries.lorebookId, lorebookId), eq(lorebookEntries.isActive, true)),
    });

    const conflicts: Array<{ entry1: LorebookEntry; entry2: LorebookEntry; reason: string }> = [];

    for (let i = 0; i < entries.length; i++) {
      for (let j = i + 1; j < entries.length; j++) {
        const e1 = entries[i];
        const e2 = entries[j];

        // Check for duplicate titles
        if (e1.title.toLowerCase() === e2.title.toLowerCase()) {
          conflicts.push({ entry1: e1, entry2: e2, reason: "Duplicate titles" });
        }

        // Check for overlapping trigger keywords
        const sharedTriggers = e1.triggerKeywords.filter((k: any) => 
          e2.triggerKeywords.some((k2: any) => k.toLowerCase() === k2.toLowerCase())
        );
        if (sharedTriggers.length > 0) {
          conflicts.push({ entry1: e1, entry2: e2, reason: `Shared triggers: ${sharedTriggers.join(", ")}` });
        }

        // Check for contradictory content (simple heuristic)
        if (e1.content.includes("not") && e2.content.includes(e1.content.replace("not ", ""))) {
          conflicts.push({ entry1: e1, entry2: e2, reason: "Potentially contradictory content" });
        }
      }
    }

    return conflicts;
  }
}

export const memoryService = new MemoryService();
