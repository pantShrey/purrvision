import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
// FIX: Add 'type' before Store so the bundler knows it's not a value
import { api, type Store, type AuditLog} from '../lib/api';

export const useStores = () => {
  return useQuery({
    queryKey: ['stores'],
    queryFn: async () => {
      const { data } = await api.get<Store[]>('/stores');
      return data;
    },
    refetchInterval: 2000,
  });
};

export const useCreateStore = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newStore: { name: string; engine: string }) => {
      const { data } = await api.post('/stores', newStore);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stores'] });
    },
  });
};

export const useDeleteStore = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (storeId: string) => {
      await api.delete(`/stores/${storeId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stores'] });
    },
  });
};
export const useStore = (storeId: string) => {
  return useQuery({
    queryKey: ['store', storeId],
    queryFn: async () => {
      const { data } = await api.get<Store>(`/stores/${storeId}`);
      return data;
    },
    refetchInterval: 2000, // Poll this too so we see status changes live on the details page
  });
};

export const useStoreLogs = (storeId: string) => {
  return useQuery({
    queryKey: ['store', storeId, 'logs'],
    queryFn: async () => {
      const { data } = await api.get<AuditLog[]>(`/stores/${storeId}/audit`);
      return data;
    },
    refetchInterval: 2000, // Live logs!
  });
};