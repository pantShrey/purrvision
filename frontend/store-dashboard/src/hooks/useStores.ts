import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
// FIX: Add 'type' before Store so the bundler knows it's not a value
import { api, type Store } from '../lib/api';

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
