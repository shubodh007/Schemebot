"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SchemeCard } from "@/components/schemes/SchemeCard";
import { SchemeCardSkeleton } from "@/components/common/SkeletonLoader";
import { schemesApi, type SchemeCard as SchemeCardType, type Category } from "@/lib/api/schemes";
import { Search, Filter, LayoutList, SlidersHorizontal } from "lucide-react";

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<SchemeCardType[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    schemesApi.categories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    schemesApi.list({
      query: search || undefined,
      category_id: selectedCategory || undefined,
      page,
      limit: 12,
    }).then((res) => {
      setSchemes(page === 1 ? res.schemes : [...schemes, ...res.schemes]);
      setHasMore(res.has_more);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [search, selectedCategory, page]);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold">Government Schemes</h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse central and state welfare schemes
          </p>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search schemes..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-9 w-full sm:w-64"
            />
          </div>
          <Button variant="outline" size="icon">
            <SlidersHorizontal className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-6 scrollbar-none">
        <button
          onClick={() => { setSelectedCategory(null); setPage(1); }}
          className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
            selectedCategory === null
              ? "bg-saffron-500 text-white"
              : "bg-secondary/50 text-slate-400 hover:text-foreground"
          }`}
        >
          <LayoutList className="w-3 h-3 inline mr-1" />
          All
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => { setSelectedCategory(cat.id); setPage(1); }}
            className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors whitespace-nowrap ${
              selectedCategory === cat.id
                ? "bg-saffron-500 text-white"
                : "bg-secondary/50 text-slate-400 hover:text-foreground"
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Results */}
      {loading && page === 1 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <SchemeCardSkeleton key={i} />
          ))}
        </div>
      ) : schemes.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {schemes.map((scheme, i) => (
              <SchemeCard key={scheme.id} scheme={scheme} index={i} />
            ))}
          </div>
          {hasMore && (
            <div className="text-center mt-8">
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={loading}
              >
                {loading ? "Loading..." : "Load More"}
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-20">
          <div className="w-12 h-12 rounded-xl bg-secondary/50 flex items-center justify-center mx-auto mb-3">
            <Search className="w-6 h-6 text-slate-400" />
          </div>
          <p className="text-slate-400">No schemes found</p>
          <p className="text-sm text-slate-600 mt-1">Try a different search term</p>
        </div>
      )}
    </div>
  );
}
