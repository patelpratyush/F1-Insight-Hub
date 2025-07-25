import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Settings, Palette, BarChart3, Save, RotateCcw, Download } from 'lucide-react';

export interface GraphCustomization {
  chartType: 'line' | 'area' | 'scatter';
  lineThickness: number;
  opacity: number;
  gridLines: boolean;
  legend: boolean;
  animations: boolean;
  colorScheme: 'default' | 'racing' | 'classic' | 'neon' | 'custom';
  customColors: {
    speed: string;
    throttle: string;
    brake: string;
    gear: string;
    rpm: string;
    drs: string;
  };
  axisSettings: {
    xAxisLabel: string;
    yAxisLabel: string;
    xAxisMin?: number;
    xAxisMax?: number;
    yAxisMin?: number;
    yAxisMax?: number;
    autoScale: boolean;
  };
  displaySettings: {
    showDataPoints: boolean;
    smoothLines: boolean;
    fillArea: boolean;
    gradient: boolean;
  };
}

interface GraphCustomizationPanelProps {
  customization: GraphCustomization;
  onCustomizationChange: (customization: GraphCustomization) => void;
  onSavePreset: (name: string) => void;
  onLoadPreset: (preset: GraphCustomization) => void;
  presetNames: string[];
}

const defaultCustomization: GraphCustomization = {
  chartType: 'line',
  lineThickness: 2,
  opacity: 80,
  gridLines: true,
  legend: true,
  animations: true,
  colorScheme: 'racing',
  customColors: {
    speed: '#3B82F6',
    throttle: '#10B981',
    brake: '#EF4444',
    gear: '#F59E0B',
    rpm: '#8B5CF6',
    drs: '#EC4899'
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

const colorSchemes = {
  default: {
    speed: '#3B82F6',
    throttle: '#10B981',
    brake: '#EF4444',
    gear: '#F59E0B',
    rpm: '#8B5CF6',
    drs: '#EC4899'
  },
  racing: {
    speed: '#FF0000',
    throttle: '#00FF00',
    brake: '#FF4500',
    gear: '#FFD700',
    rpm: '#9932CC',
    drs: '#FF1493'
  },
  classic: {
    speed: '#000080',
    throttle: '#008000',
    brake: '#800000',
    gear: '#808000',
    rpm: '#800080',
    drs: '#008080'
  },
  neon: {
    speed: '#00FFFF',
    throttle: '#39FF14',
    brake: '#FF073A',
    gear: '#FFFF00',
    rpm: '#BF00FF',
    drs: '#FF69B4'
  }
};

export const GraphCustomizationPanel: React.FC<GraphCustomizationPanelProps> = ({
  customization,
  onCustomizationChange,
  onSavePreset,
  onLoadPreset,
  presetNames
}) => {
  const [presetName, setPresetName] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const updateCustomization = (updates: Partial<GraphCustomization>) => {
    onCustomizationChange({ ...customization, ...updates });
  };

  const updateAxisSettings = (updates: Partial<GraphCustomization['axisSettings']>) => {
    onCustomizationChange({
      ...customization,
      axisSettings: { ...customization.axisSettings, ...updates }
    });
  };

  const updateDisplaySettings = (updates: Partial<GraphCustomization['displaySettings']>) => {
    onCustomizationChange({
      ...customization,
      displaySettings: { ...customization.displaySettings, ...updates }
    });
  };

  const updateCustomColors = (updates: Partial<GraphCustomization['customColors']>) => {
    onCustomizationChange({
      ...customization,
      customColors: { ...customization.customColors, ...updates }
    });
  };

  const handleColorSchemeChange = (scheme: string) => {
    if (scheme !== 'custom' && colorSchemes[scheme as keyof typeof colorSchemes]) {
      onCustomizationChange({
        ...customization,
        colorScheme: scheme as GraphCustomization['colorScheme'],
        customColors: colorSchemes[scheme as keyof typeof colorSchemes]
      });
    } else {
      updateCustomization({ colorScheme: scheme as GraphCustomization['colorScheme'] });
    }
  };

  const resetToDefaults = () => {
    onCustomizationChange(defaultCustomization);
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      onSavePreset(presetName.trim());
      setPresetName('');
    }
  };

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-blue-500" />
            <span>Graph Customization</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsOpen(!isOpen)}
            className="text-gray-300 border-gray-600"
          >
            {isOpen ? 'Hide' : 'Show'} Controls
          </Button>
        </CardTitle>
      </CardHeader>
      
      {isOpen && (
        <CardContent className="space-y-6">
          <Tabs defaultValue="chart" className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-gray-700">
              <TabsTrigger value="chart" className="text-white data-[state=active]:bg-blue-600">
                Chart Type
              </TabsTrigger>
              <TabsTrigger value="colors" className="text-white data-[state=active]:bg-green-600">
                Colors
              </TabsTrigger>
              <TabsTrigger value="axes" className="text-white data-[state=active]:bg-purple-600">
                Axes
              </TabsTrigger>
              <TabsTrigger value="presets" className="text-white data-[state=active]:bg-orange-600">
                Presets
              </TabsTrigger>
            </TabsList>

            {/* Chart Type & Style Tab */}
            <TabsContent value="chart" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Chart Type</Label>
                  <Select value={customization.chartType} onValueChange={(value) => 
                    updateCustomization({ chartType: value as GraphCustomization['chartType'] })
                  }>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      <SelectItem value="line" className="text-white hover:bg-gray-600">
                        📈 Line Chart
                      </SelectItem>
                      <SelectItem value="area" className="text-white hover:bg-gray-600">
                        📊 Area Chart
                      </SelectItem>
                      <SelectItem value="scatter" className="text-white hover:bg-gray-600">
                        ⚬ Scatter Plot
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-gray-300">Line Thickness</Label>
                  <div className="flex items-center space-x-2">
                    <Slider
                      value={[customization.lineThickness]}
                      onValueChange={([value]) => updateCustomization({ lineThickness: value })}
                      max={8}
                      min={1}
                      step={0.5}
                      className="flex-1"
                    />
                    <span className="text-gray-300 w-8 text-sm">{customization.lineThickness}px</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">Opacity</Label>
                  <div className="flex items-center space-x-2">
                    <Slider
                      value={[customization.opacity]}
                      onValueChange={([value]) => updateCustomization({ opacity: value })}
                      max={100}
                      min={10}
                      step={5}
                      className="flex-1"
                    />
                    <span className="text-gray-300 w-12 text-sm">{customization.opacity}%</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-gray-300">Show Data Points</Label>
                  <Switch
                    checked={customization.displaySettings.showDataPoints}
                    onCheckedChange={(checked) => updateDisplaySettings({ showDataPoints: checked })}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <Label className="text-gray-300">Smooth Lines</Label>
                  <Switch
                    checked={customization.displaySettings.smoothLines}
                    onCheckedChange={(checked) => updateDisplaySettings({ smoothLines: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label className="text-gray-300">Fill Area</Label>
                  <Switch
                    checked={customization.displaySettings.fillArea}
                    onCheckedChange={(checked) => updateDisplaySettings({ fillArea: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label className="text-gray-300">Grid Lines</Label>
                  <Switch
                    checked={customization.gridLines}
                    onCheckedChange={(checked) => updateCustomization({ gridLines: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label className="text-gray-300">Show Legend</Label>
                  <Switch
                    checked={customization.legend}
                    onCheckedChange={(checked) => updateCustomization({ legend: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label className="text-gray-300">Animations</Label>
                  <Switch
                    checked={customization.animations}
                    onCheckedChange={(checked) => updateCustomization({ animations: checked })}
                  />
                </div>
              </div>
            </TabsContent>

            {/* Colors Tab */}
            <TabsContent value="colors" className="space-y-4">
              <div>
                <Label className="text-gray-300">Color Scheme</Label>
                <Select value={customization.colorScheme} onValueChange={handleColorSchemeChange}>
                  <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-700 border-gray-600">
                    <SelectItem value="default" className="text-white hover:bg-gray-600">
                      🎨 Default
                    </SelectItem>
                    <SelectItem value="racing" className="text-white hover:bg-gray-600">
                      🏎️ Racing
                    </SelectItem>
                    <SelectItem value="classic" className="text-white hover:bg-gray-600">
                      📊 Classic
                    </SelectItem>
                    <SelectItem value="neon" className="text-white hover:bg-gray-600">
                      💫 Neon
                    </SelectItem>
                    <SelectItem value="custom" className="text-white hover:bg-gray-600">
                      ✨ Custom
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {customization.colorScheme === 'custom' && (
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(customization.customColors).map(([key, color]) => (
                    <div key={key} className="flex items-center space-x-2">
                      <Label className="text-gray-300 capitalize w-16">{key}:</Label>
                      <Input
                        type="color"
                        value={color}
                        onChange={(e) => updateCustomColors({ [key]: e.target.value } as any)}
                        className="w-12 h-8 bg-gray-700 border-gray-600"
                      />
                      <span className="text-xs text-gray-400">{color}</span>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Axes Tab */}
            <TabsContent value="axes" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-300">X-Axis Label</Label>
                  <Input
                    value={customization.axisSettings.xAxisLabel}
                    onChange={(e) => updateAxisSettings({ xAxisLabel: e.target.value })}
                    className="bg-gray-700 border-gray-600 text-white"
                  />
                </div>
                <div>
                  <Label className="text-gray-300">Y-Axis Label</Label>
                  <Input
                    value={customization.axisSettings.yAxisLabel}
                    onChange={(e) => updateAxisSettings({ yAxisLabel: e.target.value })}
                    className="bg-gray-700 border-gray-600 text-white"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Label className="text-gray-300">Auto Scale Axes</Label>
                <Switch
                  checked={customization.axisSettings.autoScale}
                  onCheckedChange={(checked) => updateAxisSettings({ autoScale: checked })}
                />
              </div>

              {!customization.axisSettings.autoScale && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">X-Axis Range</Label>
                    <div className="flex space-x-2">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={customization.axisSettings.xAxisMin || ''}
                        onChange={(e) => updateAxisSettings({ 
                          xAxisMin: e.target.value ? Number(e.target.value) : undefined 
                        })}
                        className="bg-gray-700 border-gray-600 text-white"
                      />
                      <Input
                        type="number"
                        placeholder="Max"
                        value={customization.axisSettings.xAxisMax || ''}
                        onChange={(e) => updateAxisSettings({ 
                          xAxisMax: e.target.value ? Number(e.target.value) : undefined 
                        })}
                        className="bg-gray-700 border-gray-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-gray-300">Y-Axis Range</Label>
                    <div className="flex space-x-2">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={customization.axisSettings.yAxisMin || ''}
                        onChange={(e) => updateAxisSettings({ 
                          yAxisMin: e.target.value ? Number(e.target.value) : undefined 
                        })}
                        className="bg-gray-700 border-gray-600 text-white"
                      />
                      <Input
                        type="number"
                        placeholder="Max"
                        value={customization.axisSettings.yAxisMax || ''}
                        onChange={(e) => updateAxisSettings({ 
                          yAxisMax: e.target.value ? Number(e.target.value) : undefined 
                        })}
                        className="bg-gray-700 border-gray-600 text-white"
                      />
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Presets Tab */}
            <TabsContent value="presets" className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Preset name"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  className="bg-gray-700 border-gray-600 text-white"
                />
                <Button onClick={handleSavePreset} className="bg-green-600 hover:bg-green-700">
                  <Save className="h-4 w-4 mr-1" />
                  Save
                </Button>
              </div>

              {presetNames.length > 0 && (
                <div>
                  <Label className="text-gray-300">Load Preset</Label>
                  <Select onValueChange={(presetName) => {
                    // In a real implementation, you'd load the preset data
                    // onLoadPreset(savedPresets[presetName]);
                  }}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Choose preset" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {presetNames.map((name) => (
                        <SelectItem key={name} value={name} className="text-white hover:bg-gray-600">
                          {name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <Separator className="bg-gray-600" />

              <div className="flex space-x-2">
                <Button onClick={resetToDefaults} variant="outline" className="text-gray-300 border-gray-600">
                  <RotateCcw className="h-4 w-4 mr-1" />
                  Reset to Defaults
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  );
};

export default GraphCustomizationPanel;