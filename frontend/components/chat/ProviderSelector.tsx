"use client";

import { Check, ChevronDown, Sparkles } from "lucide-react";
import { useAIProvider } from "@/lib/hooks/useAIProvider";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const costLabels: Record<string, string> = {
  free: "Free",
  paid: "Paid",
};

const costColors: Record<string, string> = {
  free: "text-jade-500 bg-jade-500/10",
  paid: "text-saffron-500 bg-saffron-500/10",
};

export function ProviderSelector() {
  const { currentProvider, providers, setProvider } = useAIProvider();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 text-xs text-slate-400">
          <Sparkles className="w-3 h-3 text-saffron-500" />
          {currentProvider.name}
          <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full font-medium", costColors[currentProvider.cost])}>
            {costLabels[currentProvider.cost]}
          </span>
          <ChevronDown className="w-3 h-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {providers.map((p) => (
          <DropdownMenuItem
            key={p.id}
            onClick={() => setProvider(p.id)}
            className="flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <div className="flex flex-col">
                <span className="text-sm font-medium">{p.name}</span>
                <span className="text-[10px] text-muted-foreground">{p.label}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className={cn(
                      "w-1 h-3 rounded-full",
                      i < p.quality ? "bg-saffron-500" : "bg-secondary"
                    )}
                  />
                ))}
              </div>
              {currentProvider.id === p.id && <Check className="w-3 h-3 text-saffron-500" />}
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
