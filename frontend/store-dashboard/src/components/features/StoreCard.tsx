import { Link } from 'react-router-dom';
import type { Store } from '../../lib/api';
import { useDeleteStore } from '../../hooks/useStores';
import { Card, Badge, Button } from '../ui/primitives';
// FIX: Added 'Copy' to the imports
import { ExternalLink, Trash2, Shield, RefreshCw, List, Copy } from 'lucide-react';
import { copyToClipboard } from '../../lib/utils';

const statusConfig = {
  QUEUED: { color: 'default', label: 'Queued' },
  PROVISIONING: { color: 'warning', label: 'Provisioning...' },
  READY: { color: 'success', label: 'Online' },
  FAILED: { color: 'destructive', label: 'Provisioning Failed' },
  DELETING: { color: 'outline', label: 'Deleting...' },
  DELETED: { color: 'outline', label: 'Deleted' },
} as const; // 'as const' helps typescript narrow the types

export const StoreCard = ({ store }: { store: Store }) => {
  const deleteStore = useDeleteStore();
  // @ts-ignore - Safe fallback
  const config = statusConfig[store.status] || statusConfig.QUEUED;
  const isWorking = store.status === 'PROVISIONING' || store.status === 'DELETING';
   
  return (
    <Card className="p-5 hover:shadow-md transition-shadow flex flex-col justify-between h-full">
      <div>
        <div className="flex justify-between items-start mb-2">
          <Badge variant={config.color} className={isWorking ? "animate-pulse" : ""}>
            {isWorking && <RefreshCw className="h-3 w-3 mr-1 animate-spin" />}
            {config.label}
          </Badge>
          <div className="text-xs font-mono text-slate-400">
            {store.engine}
          </div>
        </div>
        
        {/* ID & Copy Section */}
        <div className="group flex items-center gap-2 mb-4">
            <h3 className="font-bold text-lg tracking-tight mr-2">{store.name}</h3>
            <code className="text-[10px] text-slate-400 font-mono bg-slate-100 px-1 py-0.5 rounded">
              {store.id.slice(0, 8)}...
            </code>
            <button 
              onClick={() => copyToClipboard(store.id)}
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              title="Copy ID"
            >
              <Copy className="h-3 w-3 text-slate-400 hover:text-blue-500" />
            </button>
        </div>

        {store.status === 'READY' && (
          <div className="space-y-2 mb-4">
             {/* Note: The ! asserts url is not null */}
             <a href={store.url!} target="_blank" rel="noopener noreferrer" className="flex items-center text-sm text-blue-600 hover:underline">
               <ExternalLink className="h-4 w-4 mr-2" />
               Visit Storefront
             </a>
             {store.store_admin_url && (
               <a href={store.store_admin_url} target="_blank" rel="noopener noreferrer" className="flex items-center text-sm text-slate-600 hover:text-slate-900">
                 <Shield className="h-4 w-4 mr-2" />
                 Admin Panel
               </a>
             )}
          </div>
        )}

        {store.status === 'FAILED' && (
          <div className="text-xs text-red-600 bg-red-50 p-2 rounded mb-4">
            Provisioning failed. Check logs for details.
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-slate-100 flex justify-end gap-2">
        {/* Logs Button */}
        <Link to={`/stores/${store.id}`}>
            <Button variant="outline" className="h-8 text-xs">
                <List className="h-3 w-3 mr-1" />
                Logs & Details
            </Button>
        </Link>

        {/* Delete Button */}
        <Button 
          variant="ghost" 
          className="text-red-500 hover:text-red-600 hover:bg-red-50 h-8 text-xs"
          onClick={() => {
            if(confirm(`Are you sure you want to delete ${store.name}?`)) {
              deleteStore.mutate(store.id);
            }
          }}
          disabled={deleteStore.isPending || store.status === 'DELETING'}
        >
          <Trash2 className="h-3 w-3 mr-1" />
          {store.status === 'FAILED' ? 'Cleanup' : 'Delete'}
        </Button>
      </div>
    </Card>
  );
};