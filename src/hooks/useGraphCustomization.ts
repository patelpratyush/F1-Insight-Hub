import { useState, useEffect, useCallback } from 'react';
import { GraphCustomization } from '@/components/GraphCustomizationPanel';

const defaultCustomization: GraphCustomization = {
  chartType: 'line',
  lineThickness: 2,
  opacity: 80,
  gridLines: true,
  legend: true,
  animations: true,
  colorScheme: 'racing',
  customColors: {
    speed: '#FF0000',
    throttle: '#00FF00',
    brake: '#FF4500',
    gear: '#FFD700',
    rpm: '#9932CC',
    drs: '#FF1493'
  },
  axisSettings: {
    xAxisLabel: 'Distance (m)',
    yAxisLabel: 'Value',
    autoScale: true
  },
  displaySettings: {
    showDataPoints: false,
    smoothLines: true,
    fillArea: false,
    gradient: false
  }
};

const STORAGE_KEY = 'f1-graph-customization';
const PRESETS_KEY = 'f1-graph-presets';

export const useGraphCustomization = () => {
  const [customization, setCustomization] = useState<GraphCustomization>(defaultCustomization);
  const [presets, setPresets] = useState<Record<string, GraphCustomization>>({});

  // Load customization from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setCustomization({ ...defaultCustomization, ...parsed });
      }

      const savedPresets = localStorage.getItem(PRESETS_KEY);
      if (savedPresets) {
        setPresets(JSON.parse(savedPresets));
      }
    } catch (error) {
      console.warn('Failed to load graph customization from localStorage:', error);
    }
  }, []);

  // Save customization to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(customization));
    } catch (error) {
      console.warn('Failed to save graph customization to localStorage:', error);
    }
  }, [customization]);

  // Save presets to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(PRESETS_KEY, JSON.stringify(presets));
    } catch (error) {
      console.warn('Failed to save graph presets to localStorage:', error);
    }
  }, [presets]);

  const updateCustomization = useCallback((updates: Partial<GraphCustomization>) => {
    setCustomization(prev => ({ ...prev, ...updates }));
  }, []);

  const savePreset = useCallback((name: string) => {
    setPresets(prev => ({
      ...prev,
      [name]: customization
    }));
  }, [customization]);

  const loadPreset = useCallback((preset: GraphCustomization) => {
    setCustomization(preset);
  }, []);

  const deletePreset = useCallback((name: string) => {
    setPresets(prev => {
      const newPresets = { ...prev };
      delete newPresets[name];
      return newPresets;
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    setCustomization(defaultCustomization);
  }, []);

  const getChartStyle = useCallback(() => {
    return {
      strokeWidth: customization.lineThickness,
      opacity: customization.opacity / 100,
      strokeDasharray: customization.displaySettings.smoothLines ? 'none' : undefined,
      fill: customization.displaySettings.fillArea ? 'url(#colorGradient)' : 'none',
      fillOpacity: customization.displaySettings.fillArea ? 0.3 : 0,
    };
  }, [customization]);

  const getAxisDomain = useCallback((axis: 'x' | 'y') => {
    if (customization.axisSettings.autoScale) {
      return ['dataMin', 'dataMax'];
    }
    
    if (axis === 'x') {
      const min = customization.axisSettings.xAxisMin;
      const max = customization.axisSettings.xAxisMax;
      return [min ?? 'dataMin', max ?? 'dataMax'];
    } else {
      const min = customization.axisSettings.yAxisMin;
      const max = customization.axisSettings.yAxisMax;
      return [min ?? 'dataMin', max ?? 'dataMax'];
    }
  }, [customization.axisSettings]);

  const getVariableColor = useCallback((variable: keyof GraphCustomization['customColors']) => {
    return customization.customColors[variable];
  }, [customization.customColors]);

  const exportSettings = useCallback(() => {
    const exportData = {
      customization,
      presets,
      exportedAt: new Date().toISOString(),
      version: '1.0'
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `f1-graph-settings-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [customization, presets]);

  const importSettings = useCallback((file: File) => {
    return new Promise<void>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target?.result as string);
          if (data.customization) {
            setCustomization({ ...defaultCustomization, ...data.customization });
          }
          if (data.presets) {
            setPresets(prev => ({ ...prev, ...data.presets }));
          }
          resolve();
        } catch (error) {
          reject(new Error('Invalid settings file format'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }, []);

  return {
    customization,
    updateCustomization,
    presets,
    presetNames: Object.keys(presets),
    savePreset,
    loadPreset,
    deletePreset,
    resetToDefaults,
    getChartStyle,
    getAxisDomain,
    getVariableColor,
    exportSettings,
    importSettings
  };
};

export default useGraphCustomization;