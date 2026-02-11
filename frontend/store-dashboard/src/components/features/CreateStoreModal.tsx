import { useState } from 'react';
import { useCreateStore } from '../../hooks/useStores';
import { Button, Input, Card } from '../ui/primitives';
import { X, Copy, CheckCircle, AlertTriangle } from 'lucide-react';
import { copyToClipboard } from '../../lib/utils';

export const CreateStoreModal = ({ onClose }: { onClose: () => void }) => {
  const [name, setName] = useState('');
  const createStore = useCreateStore();
  
  // State to hold the "One Time" credentials
  const [credentials, setCredentials] = useState<{username: string, password: string} | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createStore.mutate({ name, engine: 'woocommerce' }, {
      onSuccess: (data) => {
        // Capture credentials immediately
        setCredentials(data.initial_credentials);
      },
      onError: (err: any) => {
        alert("Error: " + (err.response?.data?.detail || "Failed to create"));
      }
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
      <Card className="w-full max-w-md p-6 bg-white shadow-xl relative">
        {/* If we have credentials, show the Nuclear Code view */}
        {credentials ? (
          <div className="space-y-4 animate-in fade-in zoom-in duration-300">
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-6 w-6" />
              <h2 className="text-xl font-bold">Provisioning Started</h2>
            </div>
            
            <div className="bg-amber-50 border-l-4 border-amber-500 p-4">
              <div className="flex gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <p className="font-bold text-amber-800 text-sm">Save these credentials now.</p>
              </div>
              <p className="text-xs text-amber-700 mt-1">For security, they will not be shown again.</p>
            </div>

            <div className="bg-slate-900 text-slate-50 p-4 rounded-md font-mono text-sm space-y-2 relative group">
              <div className="flex justify-between">
                <span className="text-slate-400">User:</span>
                <span>{credentials.username}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Pass:</span>
                <span className="text-green-400">{credentials.password}</span>
              </div>
              <Button 
                variant="outline" 
                className="absolute top-2 right-2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-700 border-slate-600 hover:bg-slate-600"
                onClick={() => copyToClipboard(`User: ${credentials.username}\nPass: ${credentials.password}`)}
              >
                <Copy className="h-3 w-3 text-white" />
              </Button>
            </div>

            <Button className="w-full" onClick={onClose}>
              I have saved them safely
            </Button>
          </div>
        ) : (
          /* Normal Form View */
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-bold">New Store</h2>
              <button type="button" onClick={onClose}><X className="h-5 w-5 text-slate-400" /></button>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Store Name (Subdomain)</label>
              <Input 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                placeholder="e.g. demo-store-1" 
                pattern="[a-z0-9-]+"
                title="Lowercase letters, numbers, and hyphens only"
                required
              />
              <p className="text-xs text-slate-500">
                Will be available at {name}.127.0.0.1.nip.io
              </p>
            </div>

            <div className="pt-2">
              <Button type="submit" className="w-full" disabled={createStore.isPending}>
                {createStore.isPending ? " provisioning..." : "Launch Store"}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
};
