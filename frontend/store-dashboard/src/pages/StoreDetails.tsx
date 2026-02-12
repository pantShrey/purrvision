import { useParams, Link } from 'react-router-dom';
import { useStore, useStoreLogs } from '../hooks/useStores';
import { Card, Badge, Button } from '../components/ui/primitives';
import { ArrowLeft, Terminal, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export const StoreDetails = () => {
  const { id } = useParams<{ id: string }>();
  // We force 'id!' because we know the route has it, but safe coding practice would check
  const { data: store, isLoading: isStoreLoading } = useStore(id!);
  const { data: logs, isLoading: isLogsLoading } = useStoreLogs(id!);

  if (isStoreLoading) return <div className="p-8 text-center text-slate-400">Loading store context...</div>;
  if (!store) return <div className="p-8 text-center">Store not found</div>;

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-8 py-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" className="px-2"><ArrowLeft className="h-5 w-5" /></Button>
            </Link>
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2">
                {store.name}
                <Badge variant={store.status === 'READY' ? 'success' : store.status === 'FAILED' ? 'destructive' : 'default'}>
                  {store.status}
                </Badge>
              </h1>
              <p className="text-xs text-slate-400 font-mono mt-1">{store.id}</p>
            </div>
          </div>
          
          {store.url && (
             <a href={store.url} target="_blank" className="text-sm font-medium text-blue-600 hover:underline">
               Open Storefront ↗
             </a>
          )}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-8 py-8 space-y-6">
        
        {/* Connection Info Card */}
        <Card className="p-6">
          <h3 className="font-bold text-lg mb-4">Connection Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
               <span className="text-slate-500 block">Engine</span>
               <span className="font-mono">{store.engine}</span>
            </div>
            <div>
               <span className="text-slate-500 block">Admin URL</span>
               {store.store_admin_url ? (
                 <a href={store.store_admin_url} target="_blank" className="text-blue-600 hover:underline break-all">
                   {store.store_admin_url}
                 </a>
               ) : <span className="text-slate-300 italic">Not ready</span>}
            </div>
          </div>
        </Card>

        {/* The Timeline (The "Stand Out" Feature) */}
        <div>
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <Terminal className="h-5 w-5 text-slate-500" />
            Provisioning Logs
          </h3>
          
          <div className="relative border-l-2 border-slate-200 ml-3 space-y-8 pb-8">
            {isLogsLoading && <div className="pl-6 text-slate-400">Loading logs...</div>}
            
            {logs?.map((log, idx) => {
              // Parse details if it's JSON
              let parsedDetails = null;
              try { parsedDetails = log.details ? JSON.parse(log.details) : null; } catch(e) {}

              return (
                <div key={idx} className="relative pl-6">
                  {/* Timeline Dot */}
                  <div className={`absolute -left-[9px] top-0 h-4 w-4 rounded-full border-2 border-white ${
                    log.event.includes('Failed') ? 'bg-red-500' : 'bg-slate-400'
                  }`} />
                  
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900">{log.event}</span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    {/* If we have details (like Helm output), show them in a code block */}
                    {parsedDetails && (
                      <div className="mt-2 bg-slate-900 rounded p-3 overflow-x-auto">
                        <pre className="text-xs font-mono text-green-400">
                          {typeof parsedDetails === 'object' 
                            ? JSON.stringify(parsedDetails, null, 2) 
                            : parsedDetails}
                        </pre>
                      </div>
                    )}
                    
                    {/* Fallback for plain string details */}
                    {!parsedDetails && log.details && (
                       <p className="text-sm text-slate-600 mt-1">{log.details}</p>
                    )}
                  </div>
                </div>
              );
            })}
            
            {logs?.length === 0 && (
              <div className="pl-6 text-slate-400 italic">No logs generated yet...</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};