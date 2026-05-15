"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/lib/store/auth-store";
import {
  Sparkles,
  MessageSquare,
  CheckCircle2,
  Shield,
  ArrowRight,
  FileText,
  Scale,
  Globe,
  Zap,
  Users,
  ChevronDown,
} from "lucide-react";

const fadeUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
};

const stagger = {
  animate: {
    transition: { staggerChildren: 0.1 },
  },
};

const features = [
  {
    icon: MessageSquare,
    title: "AI Chat Assistant",
    desc: "Ask in English, Hindi, or Telugu. Get instant answers about schemes you qualify for.",
  },
  {
    icon: CheckCircle2,
    title: "Eligibility Engine",
    desc: "Complete your profile once. Our AI finds every central and state scheme you're eligible for.",
  },
  {
    icon: FileText,
    title: "Document Analysis",
    desc: "Upload Aadhaar, PAN, or certificates. AI extracts and maps data to scheme requirements.",
  },
  {
    icon: Scale,
    title: "Legal Guidance",
    desc: "Know your rights. Get RTI guidance, grievance procedures, and legal information in simple language.",
  },
  {
    icon: Globe,
    title: "Multi-Language",
    desc: "Full support for English, Hindi, and Telugu. More Indian languages coming soon.",
  },
  {
    icon: Zap,
    title: "Multiple AI Models",
    desc: "Choose between Claude, GPT-4o, Gemini, and Groq. Switch providers per conversation.",
  },
];

const stats = [
  { value: "3,000+", label: "Schemes Indexed", icon: Users },
  { value: "15+", label: "Categories", icon: CheckCircle2 },
  { value: "3", label: "Languages", icon: Globe },
];

export default function LandingPage() {
  const { isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.15], [1, 0.95]);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-background">
      {/* ─── NAV ─── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-saffron-500 to-saffron-400 flex items-center justify-center shadow-lg shadow-saffron-500/20">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-heading font-bold text-base tracking-tight">
              Gov<span className="text-saffron-500">Scheme</span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link href="/dashboard">
                <Button variant="default" size="sm">
                  Dashboard <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/register">
                  <Button variant="saffron" size="sm">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ─── HERO ─── */}
      <motion.section
        style={{ opacity: heroOpacity, scale: heroScale }}
        className="relative min-h-[90vh] flex items-center justify-center pt-14 overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-saffron-500/5 via-transparent to-background pointer-events-none" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-saffron-500/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-jade-500/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6"
          >
            <Badge variant="saffron" className="text-xs px-3 py-1">
              <Sparkles className="w-3 h-3 mr-1" />
              Powered by Multi-Model AI
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-7xl font-heading font-bold leading-[1.1] tracking-tight mb-6"
          >
            Know Every Scheme
            <br />
            <span className="text-gradient">You Qualify For</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            An AI-powered platform that helps Indian citizens discover, understand,
            and apply for government welfare schemes — in your language.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            {isAuthenticated ? (
              <Link href="/chat">
                <Button variant="saffron" size="xl" className="text-base gap-2">
                  Start Chatting <MessageSquare className="w-5 h-5" />
                </Button>
              </Link>
            ) : (
              <Link href="/register">
                <Button variant="saffron" size="xl" className="text-base gap-2">
                  Get Started Free <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
            )}
            <Link href="/schemes">
              <Button variant="outline" size="xl" className="text-base">
                Browse Schemes
              </Button>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="mt-16"
          >
            <ChevronDown className="w-6 h-6 text-slate-600 animate-bounce mx-auto" />
          </motion.div>
        </div>
      </motion.section>

      {/* ─── STATS ─── */}
      <section className="py-16 border-y border-border/50">
        <div className="max-w-5xl mx-auto px-4">
          <div className="grid grid-cols-3 gap-8">
            {stats.map((stat) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <stat.icon className="w-6 h-6 text-saffron-500 mx-auto mb-2" />
                <div className="text-2xl sm:text-3xl font-heading font-bold text-foreground">
                  {stat.value}
                </div>
                <div className="text-sm text-slate-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── */}
      <section className="py-24">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <Badge variant="saffron" className="mb-4">Features</Badge>
            <h2 className="text-3xl sm:text-4xl font-heading font-bold mb-4">
              Everything you need to navigate
              <br />
              <span className="text-gradient">government schemes</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              From AI-powered chat to document analysis — one platform for all your scheme discovery needs.
            </p>
          </motion.div>

          <motion.div
 variants={stagger}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {features.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                className="group p-6 rounded-xl border border-border bg-card hover:border-saffron-500/20 transition-all duration-300"
              >
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-5 h-5 text-saffron-500" />
                </div>
                <h3 className="font-heading font-semibold text-base mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-saffron-500/5 via-transparent to-jade-500/5 pointer-events-none" />
        <div className="max-w-3xl mx-auto px-4 text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <Badge variant="jade" className="mb-4">
              <Users className="w-3 h-3 mr-1" />
              For Every Citizen
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-heading font-bold mb-4">
              Start discovering schemes
              <br />
              <span className="text-gradient">you never knew existed</span>
            </h2>
            <p className="text-slate-400 mb-8 max-w-xl mx-auto">
              Millions in benefits go unclaimed every year. Don&apos;t leave money on the table.
            </p>
            {isAuthenticated ? (
              <Link href="/eligibility">
                <Button variant="saffron" size="xl" className="gap-2">
                  Check Eligibility <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
            ) : (
              <Link href="/register">
                <Button variant="saffron" size="xl" className="gap-2">
                  Create Free Account <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
            )}
          </motion.div>
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-border py-8">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Sparkles className="w-4 h-4 text-saffron-500" />
            GovScheme AI — Know your schemes
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-600">
            <span>AI-powered civic technology</span>
            <span>·</span>
            <span>OpenRouter · Google · Groq</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
