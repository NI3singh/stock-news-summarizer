import { create } from "zustand";

type NotificationType = "info" | "success" | "error" | "warning";

interface Notification {
  id: string;
  message: string;
  type: NotificationType;
}

interface DashboardStore {
  // Selected ticker state
  selectedTicker: string | null;
  setSelectedTicker: (ticker: string | null) => void;

  // Processing state (which tickers are currently being refreshed)
  processingTickers: Set<string>;
  addProcessingTicker: (ticker: string) => void;
  removeProcessingTicker: (ticker: string) => void;

  // Sidebar collapse state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Notification queue
  notifications: Notification[];
  addNotification: (message: string, type: NotificationType) => void;
  removeNotification: (id: string) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  selectedTicker: null,
  setSelectedTicker: (ticker) => set({ selectedTicker: ticker }),

  processingTickers: new Set(),
  addProcessingTicker: (ticker) =>
    set((s) => ({ processingTickers: new Set([...s.processingTickers, ticker]) })),
  removeProcessingTicker: (ticker) =>
    set((s) => {
      const n = new Set(s.processingTickers);
      n.delete(ticker);
      return { processingTickers: n };
    }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  notifications: [],
  addNotification: (message, type) =>
    set((s) => ({
      notifications: [...s.notifications, { id: crypto.randomUUID(), message, type }],
    })),
  removeNotification: (id) =>
    set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) })),
}));
