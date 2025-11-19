import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
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

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] text-foreground overflow-x-hidden pb-32">
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
        {/* Hero Section */}
        <section className="pt-20 md:pt-32 pb-12 md:pb-20 px-4">
          <div className="max-w-6xl mx-auto text-center">
            <motion.h1 
              className="text-7xl sm:text-8xl md:text-9xl lg:text-[10rem] font-bold tracking-tight mb-6 bg-gradient-to-br from-white via-white to-white/60 bg-clip-text text-transparent"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              data-testid="text-hero-headline"
            >
              JAI
            </motion.h1>
            
            <motion.p 
              className="text-xl md:text-2xl lg:text-3xl text-foreground/80 font-light max-w-3xl mx-auto leading-relaxed"
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
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <GrokButton
                icon={<MessageSquare className="w-5 h-5" />}
                text="Ask JAI anything"
                primary
                testId="button-ask-jai"
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
                text="Image Generation"
                testId="button-image"
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
              className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8"
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
              className="flex flex-col sm:flex-row items-center justify-center gap-8 md:gap-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <div className="relative group" data-testid="mockup-iphone">
                <div className="absolute inset-0 bg-cyan-500/20 blur-3xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                <img 
                  src={iphoneMockup} 
                  alt="JAI app on iPhone" 
                  className="relative w-64 md:w-80 h-auto drop-shadow-2xl"
                />
              </div>
              <div className="relative group" data-testid="mockup-android">
                <div className="absolute inset-0 bg-purple-500/20 blur-3xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                <img 
                  src={androidMockup} 
                  alt="JAI app on Android" 
                  className="relative w-64 md:w-80 h-auto drop-shadow-2xl"
                />
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
    </div>
  );
}

interface GrokButtonProps {
  icon: React.ReactNode;
  text: string;
  primary?: boolean;
  testId?: string;
}

function GrokButton({ icon, text, primary = false, testId }: GrokButtonProps) {
  return (
    <Button
      variant="outline"
      size="lg"
      className={`
        relative group rounded-full border-2 
        ${primary 
          ? 'border-primary/60 bg-primary/10 text-primary-foreground' 
          : 'border-border/40 bg-card/30'
        }
        backdrop-blur-sm transition-all duration-300
        overflow-visible hover-elevate active-elevate-2
      `}
      data-testid={testId}
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
      className="group p-8 bg-card/40 hover:bg-card/50 backdrop-blur-sm border-border/40 hover:border-border/60 transition-all duration-300"
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
