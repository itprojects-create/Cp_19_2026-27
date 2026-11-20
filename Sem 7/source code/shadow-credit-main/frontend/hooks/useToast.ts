import { create } from 'zustand';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error';
}

interface ToastStore {
  toasts: Toast[];
  addToast: (message: string, type: 'success' | 'error') => void;
  removeToast: (id: string) => void;
  dismissAll: () => void;
}

const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (message, type) => {
    const id = Math.random().toString(36).substring(7);
    set((state) => {
      const newToasts = [...state.toasts, { id, message, type }];
      if (newToasts.length > 3) newToasts.shift();
      return { toasts: newToasts };
    });

    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 3000);
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
  dismissAll: () => set({ toasts: [] }),
}));

export const useToast = () => {
  const { addToast, dismissAll } = useToastStore();
  return {
    toast: (message: string, type: 'success' | 'error' = 'success') => addToast(message, type),
    dismissAll,
  };
};

export { useToastStore };
