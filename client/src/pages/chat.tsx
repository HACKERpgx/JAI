import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [helpOpen, setHelpOpen] = useState(false);

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
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <Sparkles className="w-12 h-12 mx-auto mb-4 text-primary" />
                <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
                <p className="text-muted-foreground">Ask me anything, I'm here to assist.</p>
              </motion.div>
            </div>
          </div>

          <div className="p-4 border-t border-border/50">
            <div className="max-w-3xl mx-auto flex gap-2">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && message.trim()) {
                    setMessage("");
                  }
                }}
              />
              <Button disabled={!message.trim()}>
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
