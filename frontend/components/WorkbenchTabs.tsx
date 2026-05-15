export type WorkbenchTab = "analyze" | "library" | "ingest" | "retrieval" | "status";

const TABS: { id: WorkbenchTab; label: string }[] = [
  { id: "analyze", label: "Analyze Contract" },
  { id: "library", label: "RAG Library" },
  { id: "ingest", label: "RAG Ingest" },
  { id: "retrieval", label: "RAG Retrieval Test" },
  { id: "status", label: "System Status" },
];

interface WorkbenchTabsProps {
  activeTab: WorkbenchTab;
  onChange: (tab: WorkbenchTab) => void;
}

export default function WorkbenchTabs({ activeTab, onChange }: WorkbenchTabsProps) {
  return (
    <nav className="workbench-tabs" aria-label="Workbench sections">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={activeTab === tab.id ? "tab-button active" : "tab-button"}
          onClick={() => onChange(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
