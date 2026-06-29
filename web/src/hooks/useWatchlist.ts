"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { watchlistApi, type WatchlistItemApi } from "@/lib/api";

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
 * Watchlist hook with dual-mode persistence:
 * - Authenticated: synced with server (primary source of truth)
 * - Anonymous: persisted to localStorage (fallback)
 *
 * On login, local items are merged into the server watchlist.
 */
export function useWatchlist() {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const hasSynced = useRef(false);

  // ── Load: from server if authed, else from localStorage ──────────────────
  useEffect(() => {
    if (isAuthenticated) {
      // Fetch from server
      watchlistApi
        .list()
        .then((serverItems) => {
          const mapped: WatchlistItem[] = serverItems.map((item: WatchlistItemApi) => ({
            ticker: item.ticker,
            name_en: item.name_en || "",
            name_ar: item.name_ar || "",
            sector_en: item.sector_en || "",
            sector_ar: item.sector_ar || "",
            verdict: item.verdict || "",
            addedAt: item.added_at ? new Date(item.added_at).getTime() : Date.now(),
          }));
          setItems(mapped);

          // Merge any local items into server
          try {
            const localRaw = localStorage.getItem(STORAGE_KEY);
            if (localRaw && !hasSynced.current) {
              const localItems: WatchlistItem[] = JSON.parse(localRaw);
              if (localItems.length > 0) {
                // Push local items that aren't on server yet
                const serverTickers = new Set(mapped.map((i) => i.ticker));
                localItems
                  .filter((li) => !serverTickers.has(li.ticker))
                  .forEach((li) => {
                    watchlistApi.add({
                      ticker: li.ticker,
                      name_en: li.name_en,
                      name_ar: li.name_ar,
                      sector_en: li.sector_en,
                      sector_ar: li.sector_ar,
                      verdict: li.verdict,
                    });
                  });
                // Clear local after merge
                localStorage.removeItem(STORAGE_KEY);
              }
              hasSynced.current = true;
            }
          } catch {
            // ignore
          }
        })
        .catch(() => {})
        .finally(() => setLoaded(true));
    } else {
      // Anonymous mode — load from localStorage
      hasSynced.current = false;
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) setItems(JSON.parse(raw));
        else setItems([]);
      } catch {
        setItems([]);
      }
      setLoaded(true);
    }
  }, [isAuthenticated]);

  // ── Persist (anonymous mode only) ────────────────────────────────────────
  useEffect(() => {
    if (!loaded || isAuthenticated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // ignore quota errors
    }
  }, [items, loaded, isAuthenticated]);

  const isInWatchlist = useCallback(
    (ticker: string) => items.some((i) => i.ticker === ticker),
    [items]
  );

  const toggle = useCallback(
    (stock: Omit<WatchlistItem, "addedAt">) => {
      const exists = items.some((i) => i.ticker === stock.ticker);

      if (isAuthenticated) {
        if (exists) {
          watchlistApi.remove(stock.ticker).catch(() => {});
          setItems((prev) => prev.filter((i) => i.ticker !== stock.ticker));
        } else {
          watchlistApi
            .add({
              ticker: stock.ticker,
              name_en: stock.name_en,
              name_ar: stock.name_ar,
              sector_en: stock.sector_en,
              sector_ar: stock.sector_ar,
              verdict: stock.verdict,
            })
            .catch(() => {});
          setItems((prev) => [...prev, { ...stock, addedAt: Date.now() }]);
        }
      } else {
        // Anonymous mode
        if (exists) {
          setItems((prev) => prev.filter((i) => i.ticker !== stock.ticker));
        } else {
          setItems((prev) => [...prev, { ...stock, addedAt: Date.now() }]);
        }
      }
    },
    [items, isAuthenticated]
  );

  const add = useCallback(
    (stock: Omit<WatchlistItem, "addedAt">) => {
      if (isAuthenticated) {
        watchlistApi
          .add({
            ticker: stock.ticker,
            name_en: stock.name_en,
            name_ar: stock.name_ar,
            sector_en: stock.sector_en,
            sector_ar: stock.sector_ar,
            verdict: stock.verdict,
          })
          .catch(() => {});
      }
      setItems((prev) => {
        if (prev.some((i) => i.ticker === stock.ticker)) return prev;
        return [...prev, { ...stock, addedAt: Date.now() }];
      });
    },
    [isAuthenticated]
  );

  const remove = useCallback(
    (ticker: string) => {
      if (isAuthenticated) {
        watchlistApi.remove(ticker).catch(() => {});
      }
      setItems((prev) => prev.filter((i) => i.ticker !== ticker));
    },
    [isAuthenticated]
  );

  const clear = useCallback(() => {
    if (isAuthenticated) {
      items.forEach((i) => watchlistApi.remove(i.ticker).catch(() => {}));
    }
    setItems([]);
  }, [isAuthenticated, items]);

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
