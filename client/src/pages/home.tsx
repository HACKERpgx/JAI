import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Menubar,
  MenubarMenu,
  MenubarTrigger,
  MenubarContent,
  MenubarItem,
} from "@/components/ui/menubar";
import {
  MessageSquare, 
  Apple, 
  Smartphone, 
  Crown, 
  Code, 
  Mic, 
  Image as ImageIcon, 
  Sparkles,
  Brain,
  Globe,
  Shield,
  Github
} from "lucide-react";
import { SiX } from "react-icons/si";
import iphoneMockup from "@assets/generated_images/iPhone_mockup_with_JAI_app_a4b2e58a.png";
import androidMockup from "@assets/generated_images/Android_phone_mockup_with_JAI_app_01e4b32e.png";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import React, { useState } from "react";
import { useToast } from "@/hooks/use-toast";

export default function Home() {
  const [askOpen, setAskOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [visionOpen, setVisionOpen] = useState(false);
  const [visionPrompt, setVisionPrompt] = useState("");
  const [visionAnswer, setVisionAnswer] = useState<string | null>(null);
  const [visionImageDataUrl, setVisionImageDataUrl] = useState<string | null>(null);
  const [visionPreviewUrl, setVisionPreviewUrl] = useState<string | null>(null);
  const [visionLoading, setVisionLoading] = useState(false);
  const { toast } = useToast();

  async function submitPrompt() {
    if (!prompt.trim()) return;
    setLoading(true);
    setAnswer(null);
    try {
      const res = await fetch("/api/jai/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: prompt.trim() }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || res.statusText);
      }
      const data = (await res.json()) as { response?: string };
      setAnswer(data?.response ?? "");
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      toast({ title: "Request failed", description: message });
    } finally {
      setLoading(false);
    }
  }

  function onVisionFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast({ title: "Invalid file", description: "Please select an image file." });
      return;
    }

    const preview = URL.createObjectURL(file);
    setVisionPreviewUrl(preview);

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result === "string") {
        setVisionImageDataUrl(result);
      }
    };
    reader.readAsDataURL(file);
  }

  async function submitVision() {
    if (!visionImageDataUrl) {
      toast({ title: "Image required", description: "Please upload an image first." });
      return;
    }
    setVisionLoading(true);
    setVisionAnswer(null);
    try {
      const res = await fetch("/api/jai/vision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image: visionImageDataUrl,
          prompt: visionPrompt.trim() || undefined,
        }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || res.statusText);
      }
      const data = (await res.json()) as { response?: string };
      setVisionAnswer(data?.response ?? "");
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      toast({ title: "Vision request failed", description: message });
    } finally {
      setVisionLoading(false);
    }
  }

  function resetVisionState() {
    setVisionPrompt("");
    setVisionAnswer(null);
    setVisionImageDataUrl(null);
    if (visionPreviewUrl) {
      URL.revokeObjectURL(visionPreviewUrl);
    }
    setVisionPreviewUrl(null);
  }
  return (
    <div className="min-h-dvh bg-[#0f0f0f] text-foreground overflow-x-clip pb-24 md:pb-32">
      {/* Animated gradient background */}
      <div className="fixed inset-0 z-0 overflow-hidden">
        <div className="absolute inset-0 bg-[#0f0f0f]" />
        <div 
          className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-[120px] animate-glow"
          style={{ animationDelay: "0s" }}
        />
        <div 
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[120px] animate-glow"
          style={{ animationDelay: "1s" }}
        />
        <div 
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 rounded-full blur-[100px] animate-gradient"
        />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header with Help Menu */}
        <header className="flex items-center justify-between px-4 py-4 md:px-6">
          <div className="text-xl font-bold tracking-tight">JAI</div>
          <Menubar className="border-none bg-transparent">
            <MenubarMenu>
              <MenubarTrigger className="cursor-pointer">Help</MenubarTrigger>
              <MenubarContent>
                <MenubarItem asChild>
                  <a
                    href="https://github.com/HACKERpgx/JAI"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="cursor-pointer"
                  >
                    About JAI
                  </a>
                </MenubarItem>
              </MenubarContent>
            </MenubarMenu>
          </Menubar>
        </header>

        {/* Hero Section */}
        <section className="px-4 pt-16 pb-12 md:pt-28 md:pb-20">
          <div className="max-w-6xl mx-auto text-center">
            <motion.h1 
              className="mb-6 text-[clamp(4.5rem,18vw,10rem)] font-bold tracking-[-0.04em] bg-gradient-to-br from-white via-white to-white/60 bg-clip-text text-transparent"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              data-testid="text-hero-headline"
            >
              JAI
            </motion.h1>
            
            <motion.p 
              className="mx-auto max-w-3xl text-balance text-lg leading-relaxed text-foreground/80 sm:text-xl md:text-2xl lg:text-3xl font-light"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              data-testid="text-hero-tagline"
            >
              The world's most powerful and honest AI assistant
            </motion.p>
          </div>
        </section>

        {/* Interactive Button Grid */}
        <section className="pb-16 md:pb-24 px-4">
          <div className="max-w-7xl mx-auto">
            <motion.div 
              className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:gap-4 lg:grid-cols-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <GrokButton
                icon={<MessageSquare className="w-5 h-5" />}
                text="Ask JAI anything"
                primary
                testId="button-ask-jai"
                onClick={() => setAskOpen(true)}
              />
              <GrokButton
                icon={<Apple className="w-5 h-5" />}
                text="Try JAI on iOS"
                testId="button-ios"
              />
              <GrokButton
                icon={<Smartphone className="w-5 h-5" />}
                text="Try JAI on Android"
                testId="button-android"
              />
              <GrokButton
                icon={<Crown className="w-5 h-5" />}
                text="JAI Pro"
                testId="button-pro"
              />
              <GrokButton
                icon={<Code className="w-5 h-5" />}
                text="API Access"
                testId="button-api"
              />
              <GrokButton
                icon={<Mic className="w-5 h-5" />}
                text="Voice Mode"
                testId="button-voice"
              />
              <GrokButton
                icon={<ImageIcon className="w-5 h-5" />}
                text="Image Understanding"
                testId="button-image"
                onClick={() => {
                  resetVisionState();
                  setVisionOpen(true);
                }}
              />
              <GrokButton
                icon={<Sparkles className="w-5 h-5" />}
                text="Fun Mode"
                testId="button-fun"
              />
            </motion.div>
          </div>
        </section>

        {/* Feature Cards */}
        <section className="pb-16 md:pb-24 px-4">
          <div className="max-w-6xl mx-auto">
            <motion.div 
              className="grid grid-cols-1 gap-6 md:grid-cols-3 md:gap-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <FeatureCard
                icon={<Brain className="w-8 h-8" />}
                title="Reasoning"
                description="Advanced multi-step reasoning capabilities that understand context and nuance to deliver thoughtful, accurate responses."
                testId="card-reasoning"
              />
              <FeatureCard
                icon={<Globe className="w-8 h-8" />}
                title="Real-time Knowledge"
                description="Access to up-to-the-minute information from across the web, ensuring you always get the most current insights."
                testId="card-knowledge"
              />
              <FeatureCard
                icon={<Shield className="w-8 h-8" />}
                title="No Filter Honesty"
                description="Unfiltered, direct responses without corporate sanitization. Get the truth, even when it's uncomfortable."
                testId="card-honesty"
              />
            </motion.div>
          </div>
        </section>

        {/* Mobile Mockup Section */}
        <section className="pb-16 md:pb-24 px-4">
          <div className="max-w-6xl mx-auto">
            <motion.div 
              className="grid grid-cols-1 place-items-center gap-8 sm:grid-cols-2 md:gap-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <div className="relative group w-full max-w-[16rem] sm:max-w-[18rem] md:max-w-[20rem]" data-testid="mockup-iphone">
                <div className="absolute inset-0 bg-cyan-500/20 blur-3xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative aspect-[7/10]">
                  <img 
                    src={iphoneMockup} 
                    alt="JAI app on iPhone" 
                    className="h-full w-full object-contain drop-shadow-2xl"
                  />
                </div>
              </div>
              <div className="relative group w-full max-w-[16rem] sm:max-w-[18rem] md:max-w-[20rem]" data-testid="mockup-android">
                <div className="absolute inset-0 bg-purple-500/20 blur-3xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative aspect-[7/10]">
                  <img 
                    src={androidMockup} 
                    alt="JAI app on Android" 
                    className="h-full w-full object-contain drop-shadow-2xl"
                  />
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-border/50 py-12 px-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex flex-wrap items-center justify-center gap-6 md:gap-8 text-sm text-muted-foreground">
                <a 
                  href="#about" 
                  className="hover:text-foreground transition-colors"
                  data-testid="link-about"
                >
                  About
                </a>
                <a 
                  href="#careers" 
                  className="hover:text-foreground transition-colors"
                  data-testid="link-careers"
                >
                  Careers
                </a>
                <a 
                  href="#privacy" 
                  className="hover:text-foreground transition-colors"
                  data-testid="link-privacy"
                >
                  Privacy
                </a>
                <a 
                  href="#terms" 
                  className="hover:text-foreground transition-colors"
                  data-testid="link-terms"
                >
                  Terms
                </a>
              </div>
              
              <div className="flex items-center gap-4">
                <a 
                  href="https://x.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  data-testid="link-twitter"
                  aria-label="Twitter/X"
                >
                  <SiX className="w-5 h-5" />
                </a>
                <a 
                  href="https://github.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  data-testid="link-github"
                  aria-label="GitHub"
                >
                  <Github className="w-5 h-5" />
                </a>
              </div>
            </div>
            
            <div className="mt-8 text-center text-sm text-muted-foreground">
              <p>© 2025 JAI. Just Artificial Intelligence.</p>
            </div>
          </div>
        </footer>
      </div>

      {/* Ask JAI Dialog */}
      <Dialog open={askOpen} onOpenChange={setAskOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ask JAI</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Type your question or command..."
              rows={4}
            />
            <div className="flex items-center gap-3">
              <Button onClick={submitPrompt} disabled={loading || !prompt.trim()}>
                {loading ? "Thinking…" : "Send"}
              </Button>
              <Button variant="secondary" onClick={() => { setPrompt(""); setAnswer(null); }}>
                Clear
              </Button>
            </div>
            {answer !== null && (
              <Card className="p-4 whitespace-pre-wrap text-sm">
                {answer || "(no response)"}
              </Card>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Vision Dialog */}
      <Dialog
        open={visionOpen}
        onOpenChange={(open) => {
          setVisionOpen(open);
          if (!open) {
            resetVisionState();
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Image Understanding</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Upload an image
              </label>
              <div className="flex flex-col gap-3">
                <input
                  type="file"
                  accept="image/*"
                  onChange={onVisionFileChange}
                  className="text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary-foreground hover:file:bg-primary/20"
                />
                {visionPreviewUrl && (
                  <div className="rounded-lg border border-border/60 overflow-hidden max-h-64">
                    <img
                      src={visionPreviewUrl}
                      alt="Selected for analysis"
                      className="w-full h-full object-contain bg-background"
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Optional instruction
              </label>
              <Textarea
                value={visionPrompt}
                onChange={(e) => setVisionPrompt(e.target.value)}
                placeholder="Describe what you want JAI to focus on (e.g. “summarize this document”, “read the handwritten text”, “explain this chart”)…"
                rows={3}
              />
            </div>

            <div className="flex items-center gap-3">
              <Button
                onClick={submitVision}
                disabled={visionLoading || !visionImageDataUrl}
              >
                {visionLoading ? "Analyzing…" : "Analyze image"}
              </Button>
              <Button
                variant="secondary"
                onClick={resetVisionState}
                disabled={visionLoading}
              >
                Clear
              </Button>
            </div>

            {visionAnswer !== null && (
              <Card className="p-4 whitespace-pre-wrap text-sm max-h-72 overflow-auto">
                {visionAnswer || "(no response)"}
              </Card>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface GrokButtonProps {
  icon: React.ReactNode;
  text: string;
  primary?: boolean;
  testId?: string;
  onClick?: () => void;
}

function GrokButton({ icon, text, primary = false, testId, onClick }: GrokButtonProps) {
  return (
    <Button
      variant="outline"
      size="lg"
      className={`
        relative group min-h-14 w-full justify-start rounded-full border-2 px-5 text-left
        ${primary 
          ? 'border-primary/60 bg-primary/10 text-primary-foreground' 
          : 'border-border/40 bg-card/30'
        }
        backdrop-blur-sm transition-all duration-300
        overflow-visible hover-elevate active-elevate-2
      `}
      data-testid={testId}
      onClick={onClick}
    >
      {primary && (
        <div className="absolute inset-0 rounded-full bg-cyan-500/20 blur-xl group-hover:bg-cyan-500/30 transition-all duration-300" />
      )}
      <div className="relative flex items-center gap-3">
        <div className={`${primary ? 'text-primary-foreground' : 'text-foreground/70'}`}>
          {icon}
        </div>
        <span className="font-medium">{text}</span>
      </div>
    </Button>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  testId?: string;
}

function FeatureCard({ icon, title, description, testId }: FeatureCardProps) {
  return (
    <Card 
      className="group h-full p-6 md:p-8 bg-card/40 hover:bg-card/50 backdrop-blur-sm border-border/40 hover:border-border/60 transition-all duration-300"
      data-testid={testId}
    >
      <div className="mb-4 text-primary inline-block">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-3 text-foreground">
        {title}
      </h3>
      <p className="text-muted-foreground leading-relaxed">
        {description}
      </p>
    </Card>
  );
}
