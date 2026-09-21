"use client";

import { useState } from "react";
import HomeView from "@/components/HomeView";
import BanksView from "@/components/BanksView";

type Tab = "biens" | "prets";

export default function Home() {
  const [tab, setTab] = useState<Tab>("biens");

  const tabClass = (t: Tab) =>
    `px-3 py-1 rounded-md transition-colors ${
      tab === t ? "bg-white text-slate-900 font-semibold" : "text-slate-300 hover:text-white"
    }`;

  return (
    <div>
      <nav className="bg-slate-900 text-xs px-4 py-1.5 flex items-center gap-2">
        <button onClick={() => setTab("biens")} className={tabClass("biens")}>
          Analyse de biens
        </button>
        <button onClick={() => setTab("prets")} className={tabClass("prets")}>
          Comparateur de prêts
        </button>
      </nav>
      {/* Both views stay mounted so switching tabs never resets their state. */}
      <div className={tab === "biens" ? "" : "hidden"}>
        <HomeView />
      </div>
      <div className={tab === "prets" ? "" : "hidden"}>
        <BanksView />
      </div>
    </div>
  );
}
