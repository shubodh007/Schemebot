"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/store/auth-store";
import { useUIStore } from "@/lib/store/ui-store";
import { authApi } from "@/lib/api/auth";
import { User, Globe, Palette, Shield, Save } from "lucide-react";

const languages = [
  { value: "en", label: "English", flag: "🇬🇧" },
  { value: "hi", label: "हिन्दी", flag: "🇮🇳" },
  { value: "te", label: "తెలుగు", flag: "🇮🇳" },
];

export default function SettingsPage() {
  const { profile, updateProfile } = useAuthStore();
  const { language, setLanguage, theme, setTheme } = useUIStore();
  const [saving, setSaving] = useState(false);

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const form = e.target as HTMLFormElement;
    const data = Object.fromEntries(new FormData(form));
    try {
      const res = await authApi.updateProfile(data as Record<string, string>);
      updateProfile(res.profile);
    } catch {
      // handle error
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-heading font-bold">Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your profile and preferences
        </p>
      </div>

      {/* Profile */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-border bg-card p-6"
      >
        <div className="flex items-center gap-2 mb-4">
          <User className="w-5 h-5 text-saffron-500" />
          <h2 className="font-heading font-semibold">Profile Information</h2>
        </div>
        <form onSubmit={saveProfile} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm">Full Name</label>
              <Input name="full_name" defaultValue={profile?.full_name || ""} />
            </div>
            <div className="space-y-2">
              <label className="text-sm">Phone</label>
              <Input name="phone" defaultValue={profile?.phone || ""} placeholder="+91" />
            </div>
            <div className="space-y-2">
              <label className="text-sm">Annual Income (₹)</label>
              <Input name="annual_income" type="number" defaultValue={profile?.annual_income || ""} placeholder="Annual income" />
            </div>
            <div className="space-y-2">
              <label className="text-sm">State</label>
              <Input name="state_code" defaultValue={profile?.state_code || ""} placeholder="AP, TS, MH..." maxLength={2} />
            </div>
          </div>
          <Button type="submit" variant="saffron" className="gap-2" disabled={saving}>
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : "Save Profile"}
          </Button>
        </form>
      </motion.div>

      {/* Language */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="rounded-xl border border-border bg-card p-6"
      >
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-saffron-500" />
          <h2 className="font-heading font-semibold">Language</h2>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {languages.map((lang) => (
            <button
              key={lang.value}
              onClick={() => setLanguage(lang.value as "en" | "hi" | "te")}
              className={`p-3 rounded-xl border text-center transition-all ${
                language === lang.value
                  ? "border-saffron-500/50 bg-saffron-500/10"
                  : "border-border hover:border-saffron-500/20"
              }`}
            >
              <span className="text-lg">{lang.flag}</span>
              <p className="text-sm font-medium mt-1">{lang.label}</p>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Theme */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-xl border border-border bg-card p-6"
      >
        <div className="flex items-center gap-2 mb-4">
          <Palette className="w-5 h-5 text-saffron-500" />
          <h2 className="font-heading font-semibold">Appearance</h2>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {["dark", "light", "system"].map((t) => (
            <button
              key={t}
              onClick={() => setTheme(t as "dark" | "light" | "system")}
              className={`p-3 rounded-xl border text-center transition-all capitalize ${
                theme === t
                  ? "border-saffron-500/50 bg-saffron-500/10"
                  : "border-border hover:border-saffron-500/20"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
