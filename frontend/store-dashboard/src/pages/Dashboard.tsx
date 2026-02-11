import { useState } from 'react';
import { useStores } from '../hooks/useStores';
import { StoreCard } from '../components/features/StoreCard';
import { CreateStoreModal } from '../components/features/CreateStoreModal';
import { Button, Input } from '../components/ui/primitives';
import { Plus, Search, LayoutGrid } from 'lucide-react';

export const Dashboard = () => {
  const { data: stores, isLoading } = useStores();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');

  const filteredStores = stores?.filter(s => 
    s.name.includes(search.toLowerCase()) || s.id.includes(search)
  ) || [];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LayoutGrid className="h-6 w-6 text-slate-700" />
            <h1 className="text-xl font-bold text-slate-900">Urumi Control Plane</h1>
          </div>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Store
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Filter Bar */}
        <div className="mb-6 max-w-sm relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input 
            placeholder="Search stores by name or ID..." 
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-20 text-slate-400">
            Loading your infrastructure...
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredStores.length === 0 && (
          <div className="text-center py-20 border-2 border-dashed border-slate-200 rounded-lg">
            <h3 className="text-lg font-medium text-slate-900">No stores found</h3>
            <p className="text-slate-500 mb-4">Get started by provisioning your first environment.</p>
            <Button variant="outline" onClick={() => setIsModalOpen(true)}>Create Store</Button>
          </div>
        )}

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStores.map(store => (
            <StoreCard key={store.id} store={store} />
          ))}
        </div>
      </main>

      {isModalOpen && <CreateStoreModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
};
