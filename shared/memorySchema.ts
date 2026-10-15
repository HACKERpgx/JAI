import { pgTable, serial, text, timestamp, boolean, real, integer, jsonb, index, vector } from "drizzle-orm/pg-core";

// Personas table - Character definitions for AI roleplay
export const personas = pgTable("personas", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  backstory: text("backstory").notNull(),
  personalityTraits: text("personality_traits").array().notNull().default([]),
  speechStyle: text("speech_style"),
  knowledgeScope: text("knowledge_scope").array().notNull().default([]),
  forbiddenTopics: text("forbidden_topics").array().notNull().default([]),
  systemPromptTemplate: text("system_prompt_template"),
  isDefault: boolean("is_default").notNull().default(false),
  isActive: boolean("is_active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// Lorebooks table - Collections of lore entries
export const lorebooks = pgTable("lorebooks", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  isActive: boolean("is_active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// Lorebook entries - Individual pieces of knowledge
export const lorebookEntries = pgTable("lorebook_entries", {
  id: serial("id").primaryKey(),
  lorebookId: integer("lorebook_id").notNull().references(() => lorebooks.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  content: text("content").notNull(),
  tags: text("tags").array().notNull().default([]),
  triggerKeywords: text("trigger_keywords").array().notNull().default([]),
  priorityWeight: real("priority_weight").notNull().default(1.0),
  isPinned: boolean("is_pinned").notNull().default(false),
  isActive: boolean("is_active").notNull().default(true),
  useCount: integer("use_count").notNull().default(0),
  lastUsedAt: timestamp("last_used_at"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
}, (table) => ({
  lorebookIdx: index("lorebook_id_idx").on(table.lorebookId),
  activeIdx: index("entry_active_idx").on(table.isActive),
}));

// Vector embeddings for semantic search
export const lorebookEmbeddings = pgTable("lorebook_embeddings", {
  id: serial("id").primaryKey(),
  entryId: integer("entry_id").notNull().references(() => lorebookEntries.id, { onDelete: "cascade" }),
  embedding: vector("embedding", { dimensions: 1536 }).notNull(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
}, (table) => ({
  entryIdx: index("embedding_entry_idx").on(table.entryId),
}));

// Chat sessions
export const chatSessions = pgTable("chat_sessions", {
  id: serial("id").primaryKey(),
  title: text("title").notNull().default("New Chat"),
  personaId: integer("persona_id").references(() => personas.id),
  lorebookId: integer("lorebook_id").references(() => lorebooks.id),
  isActive: boolean("is_active").notNull().default(true),
  messageCount: integer("message_count").notNull().default(0),
  contextTokenCount: integer("context_token_count").notNull().default(0),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
}, (table) => ({
  personaIdx: index("session_persona_idx").on(table.personaId),
  lorebookIdx: index("session_lorebook_idx").on(table.lorebookId),
  activeIdx: index("session_active_idx").on(table.isActive),
}));

// Chat messages
export const chatMessages = pgTable("chat_messages", {
  id: serial("id").primaryKey(),
  sessionId: integer("session_id").notNull().references(() => chatSessions.id, { onDelete: "cascade" }),
  role: text("role").notNull(), // "user" or "assistant"
  content: text("content").notNull(),
  tokensUsed: integer("tokens_used").notNull().default(0),
  loreEntriesUsed: jsonb("lore_entries_used").default([]),
  createdAt: timestamp("created_at").notNull().defaultNow(),
}, (table) => ({
  sessionIdx: index("message_session_idx").on(table.sessionId),
  roleIdx: index("message_role_idx").on(table.role),
  createdIdx: index("message_created_idx").on(table.createdAt),
}));

// Type exports
export type Persona = typeof personas.$inferSelect;
export type NewPersona = typeof personas.$inferInsert;
export type Lorebook = typeof lorebooks.$inferSelect;
export type NewLorebook = typeof lorebooks.$inferInsert;
export type LorebookEntry = typeof lorebookEntries.$inferSelect;
export type NewLorebookEntry = typeof lorebookEntries.$inferInsert;
export type ChatSession = typeof chatSessions.$inferSelect;
export type NewChatSession = typeof chatSessions.$inferInsert;
export type ChatMessage = typeof chatMessages.$inferSelect;
export type NewChatMessage = typeof chatMessages.$inferInsert;
