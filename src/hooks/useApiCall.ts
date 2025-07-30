import { useState, useCallback, useRef } from 'react';

interface ApiCallState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

interface UseApiCallOptions {
  maxRetries?: number;
  retryDelay?: number;
  timeout?: number;
}

interface UseApiCallReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  execute: () => Promise<void>;
  retry: () => Promise<void>;
  reset: () => void;
  isRetrying: boolean;
}

const useApiCall = <T = any>(
  apiFunction: () => Promise<T>,
  options: UseApiCallOptions = {}
): UseApiCallReturn<T> => {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    timeout = 30000
  } = options;

  const [state, setState] = useState<ApiCallState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null
  });

  const [isRetrying, setIsRetrying] = useState(false);
  const retryCountRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const getErrorMessage = (error: any): string => {
    if (error.name === 'AbortError') {
      return 'Request was cancelled';
    }
    
    if (error.message?.includes('fetch')) {
      return 'Network error. Please check your internet connection.';
    }
    
    if (error.message?.includes('timeout')) {
      return 'Request timed out. Please try again.';
    }
    
    if (error.status) {
      switch (error.status) {
        case 400:
          return 'Invalid request. Please check your input.';
        case 401:
          return 'Authentication required.';
        case 403:
          return 'Access denied.';
        case 404:
          return 'Data not found.';
        case 429:
          return 'Too many requests. Please wait and try again.';
        case 500:
          return 'Server error. Please try again later.';
        case 503:
          return 'Service temporarily unavailable.';
        default:
          return `Server error (${error.status}). Please try again.`;
      }
    }
    
    return error.message || 'An unexpected error occurred. Please try again.';
  };

  const executeWithTimeout = useCallback(async (): Promise<T> => {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error('Request timeout'));
      }, timeout);

      apiFunction()
        .then(resolve)
        .catch(reject)
        .finally(() => clearTimeout(timeoutId));
    });
  }, [apiFunction, timeout]);

  const execute = useCallback(async (): Promise<void> => {
    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    retryCountRef.current = 0;

    setState(prev => ({
      ...prev,
      loading: true,
      error: null
    }));

    try {
      const result = await executeWithTimeout();
      
      setState({
        data: result,
        loading: false,
        error: null,
        lastUpdated: new Date()
      });
    } catch (error: any) {
      const errorMessage = getErrorMessage(error);
      
      setState({
        data: null,
        loading: false,
        error: errorMessage,
        lastUpdated: null
      });
    }
  }, [executeWithTimeout]);

  const retry = useCallback(async (): Promise<void> => {
    if (retryCountRef.current >= maxRetries) {
      setState(prev => ({
        ...prev,
        error: `Maximum retry attempts (${maxRetries}) exceeded. Please try again later.`
      }));
      return;
    }

    setIsRetrying(true);
    retryCountRef.current += 1;

    // Wait before retrying
    await new Promise(resolve => setTimeout(resolve, retryDelay * retryCountRef.current));

    try {
      const result = await executeWithTimeout();
      
      setState({
        data: result,
        loading: false,
        error: null,
        lastUpdated: new Date()
      });
      
      setIsRetrying(false);
      retryCountRef.current = 0;
    } catch (error: any) {
      const errorMessage = getErrorMessage(error);
      
      if (retryCountRef.current < maxRetries) {
        // Will retry again
        setTimeout(() => retry(), retryDelay * retryCountRef.current);
      } else {
        // Max retries reached
        setState({
          data: null,
          loading: false,
          error: `${errorMessage} (After ${maxRetries} attempts)`,
          lastUpdated: null
        });
        setIsRetrying(false);
      }
    }
  }, [executeWithTimeout, maxRetries, retryDelay]);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    setState({
      data: null,
      loading: false,
      error: null,
      lastUpdated: null
    });
    
    setIsRetrying(false);
    retryCountRef.current = 0;
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    lastUpdated: state.lastUpdated,
    execute,
    retry,
    reset,
    isRetrying
  };
};

export default useApiCall;