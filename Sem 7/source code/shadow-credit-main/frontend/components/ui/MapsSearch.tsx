import React, { useState, useEffect, useCallback } from 'react';
import { Check, Search, MapPin, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/cn';
import { Spinner } from './Spinner';
import { Button } from './Button';
import { api, MapsResult } from '../../lib/api';

// Simple debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

interface MapsSearchProps {
  sessionId?: string;
  onSelect: (result: MapsResult) => void;
  className?: string;
}

export const MapsSearch: React.FC<MapsSearchProps> = ({ sessionId, onSelect, className }) => {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);
  
  const [results, setResults] = useState<MapsResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.length < 3) {
      setResults([]);
      return;
    }

    const fetchMaps = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api.searchMaps(debouncedQuery, sessionId);
        setResults(data);
      } catch (err) {
        setError('Failed to search maps');
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMaps();
  }, [debouncedQuery, sessionId]);

  const handleSelect = (result: MapsResult) => {
    setSelectedId(result.placeId);
    onSelect(result);
  };

  const clearSelection = () => {
    setSelectedId(null);
    setQuery('');
    setResults([]);
  };

  return (
    <div className={cn("w-full space-y-3", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for shop name..."
          className="h-10 w-full rounded-md border border-border-default bg-bg-input pl-9 pr-9 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Spinner size={14} className="text-text-tertiary" />
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-[12px] text-status-error">
          <AlertCircle className="h-3 w-3" />
          <span>{error}</span>
        </div>
      )}

      {results.length > 0 && !selectedId && (
        <div className="max-h-[240px] overflow-y-auto rounded-md border border-border-subtle bg-bg-elevated">
          {results.map((result) => (
            <button
              key={result.placeId}
              onClick={() => handleSelect(result)}
              className="flex w-full flex-col items-start gap-0.5 border-b border-border-subtle p-3 text-left last:border-0 hover:bg-bg-overlay transition-colors"
            >
              <span className="text-[14px] font-medium text-text-primary">{result.name}</span>
              <span className="text-[12px] text-text-secondary line-clamp-1">{result.address}</span>
              <div className="mt-1 flex items-center gap-2 text-[11px] text-text-tertiary">
                {result.rating && (
                  <span className="flex items-center gap-1">
                    <span className="text-status-warning">★</span> {result.rating}
                  </span>
                )}
                {result.user_ratings_total && <span>({result.user_ratings_total})</span>}
              </div>
            </button>
          ))}
        </div>
      )}

      {results.length === 0 && debouncedQuery.length >= 3 && !loading && !error && (
        <div className="rounded-md border border-border-subtle bg-bg-elevated p-4 text-center">
          <MapPin className="mx-auto mb-2 h-6 w-6 text-text-tertiary opacity-50" />
          <h4 className="text-[13px] font-medium text-text-primary">Your shop isn't on Google Maps?</h4>
          <p className="mt-1 text-[12px] text-text-secondary">
            No problem. Shadow Credit can triangulate location using bills and delivery data.
          </p>
        </div>
      )}

      {selectedId && (
        <div className="animate-in fade-in zoom-in-95 duration-200">
           {/* Selected Card View can be rendered here if needed, or parent handles UI based on selection */}
           <div className="flex items-center justify-between rounded-md border-l-[3px] border-l-status-success border-y border-r border-border-subtle bg-bg-elevated p-3">
             <div>
               <div className="text-[13px] font-bold text-text-primary">
                 {results.find(r => r.placeId === selectedId)?.name}
               </div>
               <div className="text-[11px] text-text-secondary">Selected Location</div>
             </div>
             <div className="flex items-center gap-2">
               <span className="flex h-5 w-5 items-center justify-center rounded-full bg-status-success text-white">
                 <Check className="h-3 w-3" />
               </span>
             </div>
           </div>
           <Button variant="ghost" size="sm" onClick={clearSelection} className="mt-2 w-full text-[12px] text-text-tertiary h-8">
             Not my shop? Search again
           </Button>
        </div>
      )}
    </div>
  );
};
