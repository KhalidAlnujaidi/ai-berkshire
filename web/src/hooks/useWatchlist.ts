"use client";

import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "mizan:watchlist";

export interface WatchlistItem {
  ticker: string;
  name_en: string;
  name_ar: string;
  sector_en: string;
  sector_ar: string;
  verdict: string;
  addedAt: number;
}

/**
 * Client-side watchlist with localStorage persistence.
 * Lets users star/bookmark stocks and view them on a dedicated page.
 */
export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        setItems(JSON.parse(raw));
      }
    } catch {
      // ignore parse errors
    }
    setLoaded(true);
  }, []);

  // Persist on change
  useEffect(() => {
    if (!loaded) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // ignore quota errors
    }
  }, [items, loaded]);

  const isInWatchlist = useCallback(
    (ticker: string) => items.some((i) => i.ticker === ticker),
    [items]
  );

  const toggle = useCallback((stock: Omit<WatchlistItem, "addedAt">) => {
    setItems((prev) => {
      const exists = prev.some((i) => i.ticker === stock.ticker);
      if (exists) {
        return prev.filter((i) => i.ticker !== stock.ticker);
      }
      return [...prev, { ...stock, addedAt: Date.now() }];
    });
  }, []);

  const add = useCallback((stock: Omit<WatchlistItem, "addedAt">) => {
    setItems((prev) => {
      if (prev.some((i) => i.ticker === stock.ticker)) return prev;
      return [...prev, { ...stock, addedAt: Date.now() }];
    });
  }, []);

  const remove = useCallback((ticker: string) => {
    setItems((prev) => prev.filter((i) => i.ticker !== ticker));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return {
    items,
    count: items.length,
    loaded,
    isInWatchlist,
    toggle,
    add,
    remove,
    clear,
  };
}
