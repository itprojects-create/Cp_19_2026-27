"use client";

import React, { useState } from "react";
import Input from "../ui/Input";
import Button from "../ui/Button";

type Item = { name: string; address: string; rating: number; reviews: number };

export default function MapsSearch({ onSelect, onSkip }: { onSelect: (v: Item) => void; onSkip: () => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Item[]>([]);

  async function search(v: string) {
    setQuery(v);
    if (v.trim().length < 2) {
      setResults([]);
      return;
    }
    setResults([
      { name: `${v} Traders`, address: "Sadashiv Peth, Pune", rating: 4.2, reviews: 47 },
      { name: `${v} Store`, address: "Narayan Peth, Pune", rating: 4.0, reviews: 21 },
    ]);
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <Input label="Search your shop name..." value={query} onChange={(e) => search(e.target.value)} />
      {results.map((r) => (
        <button key={r.name} onClick={() => onSelect(r)} style={{ textAlign: "left", border: "1.5px solid var(--color-border)", borderRadius: 12, padding: 16, background: "white" }}>
          <div style={{ fontWeight: 600 }}>{r.name}</div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{r.address}</div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{`${r.reviews} reviews · ${r.rating} ⭐`}</div>
        </button>
      ))}
      <Button variant="ghost" onClick={onSkip}>
        My shop isn't on Google Maps
      </Button>
    </div>
  );
}

