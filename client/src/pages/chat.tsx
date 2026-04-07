import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  MessageSquare,
  Mic,
  ChevronDown,
  HelpCircle,
  FileText,
  LifeBuoy,
  ExternalLink,
  Send,
  Sparkles,
  Globe,
  Loader2,
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface Message {
  id: string;
  text: string;
  sender: "user" | "assistant";
  timestamp: Date;
  isLive?: boolean;
  source?: string;
  sourceUrl?: string;
}

export default function Chat() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [helpOpen, setHelpOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const helpItems = [
    { label: "FAQ", icon: HelpCircle, href: "#faq" },
    { label: "Support", icon: LifeBuoy, href: "#support" },
    { label: "Documentation", icon: FileText, href: "#documentation" },
    { label: "About JAI", icon: ExternalLink, href: "https://github.com/HACKERpgx/JAI", external: true },
  ];

  const handleHelpItemClick = (item: typeof helpItems[0]) => {
    if (item.external) {
      window.open(item.href, "_blank", "noopener noreferrer");
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setIsLoading(true);

    try {
      // First, try web scraping for real-time data
      const scrapingResponse = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message }),
      });

      const scrapingData = await scrapingResponse.json();

      if (scrapingData.needsScraping && scrapingData.success) {
        // Use scraped data
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: scrapingData.response,
          sender: "assistant",
          timestamp: new Date(),
          isLive: true,
          source: scrapingData.source,
          sourceUrl: scrapingData.url,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // Fallback to regular AI response
        const aiResponse = await fetch("/api/jai/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: message }),
        });

        const aiData = await aiResponse.json();

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: aiData.response || "I'm here to help! What would you like to know?",
          sender: "assistant",
          timestamp: new Date(),
          isLive: false,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I couldn't fetch data right now. Please try again.",
        sender: "assistant",
        timestamp: new Date(),
        isLive: false,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  return (
    <SidebarProvider>
      <Sidebar className="bg-[#0f0f0f] border-r border-border/50">
        <SidebarHeader className="p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary" />
            <span className="text-xl font-bold">JAI</span>
          </div>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Main</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton isActive>
                    <MessageSquare className="w-4 h-4" />
                    <span>Chat</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton>
                    <Mic className="w-4 h-4" />
                    <span>Voice Mode</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter className="p-2">
          <SidebarMenu>
            <Collapsible open={helpOpen} onOpenChange={setHelpOpen}>
              <CollapsibleTrigger asChild>
                <SidebarMenuItem>
                  <SidebarMenuButton className="w-full">
                    <HelpCircle className="w-4 h-4" />
                    <span>Help</span>
                    <ChevronDown className={`ml-auto w-4 h-4 transition-transform ${helpOpen ? "rotate-180" : ""}`} />
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarMenuSub>
                  {helpItems.map((item) => (
                    <SidebarMenuSubItem key={item.label}>
                      <SidebarMenuSubButton
                        asChild
                        onClick={() => handleHelpItemClick(item)}
                      >
                        <a
                          href={item.external ? undefined : item.href}
                          target={item.external ? "_blank" : undefined}
                          rel={item.external ? "noopener noreferrer" : undefined}
                          className="flex items-center gap-2 cursor-pointer"
                        >
                          <item.icon className="w-4 h-4" />
                          <span>{item.label}</span>
                        </a>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
              </CollapsibleContent>
            </Collapsible>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset>
        <div className="flex flex-col h-screen bg-[#0f0f0f]">
          <header className="flex items-center justify-between px-4 py-3 border-b border-border/50">
            <SidebarTrigger />
            <h1 className="text-lg font-semibold">JAI Chat</h1>
            <div className="w-8" />
          </header>

          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.length === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center py-12"
                >
                  <Sparkles className="w-12 h-12 mx-auto mb-4 text-primary" />
                  <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
                  <p className="text-muted-foreground">Ask me anything, I'm here to assist.</p>
                  <p className="text-muted-foreground text-sm mt-4">
                    Try: "What's the Bitcoin price?" or "Latest cricket scores"
                  </p>
                </motion.div>
              )}

              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  <Card className={`max-w-[80%] p-4 ${msg.sender === "user" ? "bg-primary/20" : "bg-card/50"}`}>
                    {msg.isLive && (
                      <div className="flex items-center gap-2 mb-2 text-xs text-green-500">
                        <Globe className="w-3 h-3 animate-pulse" />
                        <span className="font-medium">LIVE</span>
                        {msg.source && (
                          <span className="text-muted-foreground">• {msg.source}</span>
                        )}
                      </div>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                    {msg.sourceUrl && (
                      <a
                        href={msg.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline mt-2 block"
                      >
                        Source: {msg.sourceUrl}
                      </a>
                    )}
                  </Card>
                </motion.div>
              ))}

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <Card className="bg-card/50 p-4">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Fetching live data...</span>
                    </div>
                  </Card>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="p-4 border-t border-border/50">
            <div className="max-w-3xl mx-auto flex gap-2">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message... (Try: 'Bitcoin price' or 'Live cricket scores')"
                className="flex-1"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && message.trim() && !isLoading) {
                    handleSendMessage();
                  }
                }}
                disabled={isLoading}
              />
              <Button onClick={handleSendMessage} disabled={!message.trim() || isLoading}>
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
