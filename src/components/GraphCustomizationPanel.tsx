import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    BarChart3,
    Download,
    Palette,
    RotateCcw,
    Save,
    Settings,
} from "lucide-react";
import React, { useEffect, useState } from "react";

export interface GraphCustomization {
  chartType: "line" | "area" | "scatter";
  lineThickness: number;
  opacity: number;
  gridLines: boolean;
  legend: boolean;
  animations: boolean;
  colorScheme: "default" | "racing" | "classic" | "neon" | "custom";
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
  chartType: "line",
  lineThickness: 2,
  opacity: 80,
  gridLines: true,
  legend: true,
  animations: true,
  colorScheme: "racing",
  customColors: {
    speed: "#3B82F6",
    throttle: "#10B981",
    brake: "#EF4444",
    gear: "#F59E0B",
    rpm: "#8B5CF6",
    drs: "#EC4899",
  },
  axisSettings: {
    xAxisLabel: "Distance (m)",
    yAxisLabel: "Value",
    autoScale: true,
  },
  displaySettings: {
    showDataPoints: false,
    smoothLines: true,
    fillArea: false,
    gradient: false,
  },
};

const colorSchemes = {
  default: {
    speed: "#3B82F6",
    throttle: "#10B981",
    brake: "#EF4444",
    gear: "#F59E0B",
    rpm: "#8B5CF6",
    drs: "#EC4899",
  },
  racing: {
    speed: "#FF0000",
    throttle: "#00FF00",
    brake: "#FF4500",
    gear: "#FFD700",
    rpm: "#9932CC",
    drs: "#FF1493",
  },
  classic: {
    speed: "#000080",
    throttle: "#008000",
    brake: "#800000",
    gear: "#808000",
    rpm: "#800080",
    drs: "#008080",
  },
  neon: {
    speed: "#00FFFF",
    throttle: "#39FF14",
    brake: "#FF073A",
    gear: "#FFFF00",
    rpm: "#BF00FF",
    drs: "#FF69B4",
  },
};

export const GraphCustomizationPanel: React.FC<
  GraphCustomizationPanelProps
> = ({
  customization,
  onCustomizationChange,
  onSavePreset,
  onLoadPreset,
  presetNames,
}) => {
  const [presetName, setPresetName] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const updateCustomization = (updates: Partial<GraphCustomization>) => {
    onCustomizationChange({ ...customization, ...updates });
  };

  const updateAxisSettings = (
    updates: Partial<GraphCustomization["axisSettings"]>,
  ) => {
    onCustomizationChange({
      ...customization,
      axisSettings: { ...customization.axisSettings, ...updates },
    });
  };

  const updateDisplaySettings = (
    updates: Partial<GraphCustomization["displaySettings"]>,
  ) => {
    onCustomizationChange({
      ...customization,
      displaySettings: { ...customization.displaySettings, ...updates },
    });
  };

  const updateCustomColors = (
    updates: Partial<GraphCustomization["customColors"]>,
  ) => {
    onCustomizationChange({
      ...customization,
      customColors: { ...customization.customColors, ...updates },
    });
  };

  const handleColorSchemeChange = (scheme: string) => {
    if (
      scheme !== "custom" &&
      colorSchemes[scheme as keyof typeof colorSchemes]
    ) {
      onCustomizationChange({
        ...customization,
        colorScheme: scheme as GraphCustomization["colorScheme"],
        customColors: colorSchemes[scheme as keyof typeof colorSchemes],
      });
    } else {
      updateCustomization({
        colorScheme: scheme as GraphCustomization["colorScheme"],
      });
    }
  };

  const resetToDefaults = () => {
    onCustomizationChange(defaultCustomization);
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      onSavePreset(presetName.trim());
      setPresetName("");
    }
  };

  return (
    <Card className="bg-transparent bg-gradient-to-br from-white/[0.02] to-transparent shadow-none border border-white/5 rounded-[32px] overflow-hidden">
      <CardHeader>
        <CardTitle className="text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-blue-500" />
            <span>Graph Customization</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(!isOpen)}
            className="text-white hover:bg-white/10 rounded-full border border-white/5 bg-white/5 p-4 py-2 hover:border-white/10"
          >
            {isOpen ? "Hide" : "Show"} Controls
          </Button>
        </CardTitle>
      </CardHeader>

      {isOpen && (
        <CardContent className="space-y-6">
          <Tabs defaultValue="chart" className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-white/5 rounded-full p-1 h-auto mb-6">
              <TabsTrigger
                value="chart"
                className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-2"
              >
                Chart Type
              </TabsTrigger>
              <TabsTrigger
                value="colors"
                className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-2"
              >
                Colors
              </TabsTrigger>
              <TabsTrigger
                value="axes"
                className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-2"
              >
                Axes
              </TabsTrigger>
              <TabsTrigger
                value="presets"
                className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-2"
              >
                Presets
              </TabsTrigger>
            </TabsList>

            {/* Chart Type & Style Tab */}
            <TabsContent value="chart" className="space-y-6">
              {/* Chart Type Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-400" />
                  Chart Configuration
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300 text-sm font-medium">
                      Chart Type
                    </Label>
                    <Select
                      value={customization.chartType}
                      onValueChange={(value) =>
                        updateCustomization({
                          chartType: value as GraphCustomization["chartType"],
                        })
                      }
                    >
                      <SelectTrigger className="bg-[#111111] border-white/10 rounded-full h-12 text-white mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#111111] border-white/10 rounded-2xl">
                        <SelectItem
                          value="line"
                          className="text-white hover:bg-gray-600"
                        >
                          📈 Line Chart
                        </SelectItem>
                        <SelectItem
                          value="area"
                          className="text-white hover:bg-gray-600"
                        >
                          📊 Area Chart
                        </SelectItem>
                        <SelectItem
                          value="scatter"
                          className="text-white hover:bg-gray-600"
                        >
                          ⚬ Scatter Plot
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-gray-300 text-sm font-medium">
                      Line Thickness
                    </Label>
                    <div className="flex items-center space-x-3 mt-2">
                      <Slider
                        value={[customization.lineThickness]}
                        onValueChange={([value]) =>
                          updateCustomization({ lineThickness: value })
                        }
                        max={8}
                        min={1}
                        step={0.5}
                        className="flex-1"
                      />
                      <div className="bg-blue-600/20 border border-blue-600/40 rounded px-2 py-1 min-w-[50px] text-center">
                        <span className="text-blue-400 font-medium text-sm">
                          {customization.lineThickness}px
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <Label className="text-gray-300 text-sm font-medium">
                    Opacity
                  </Label>
                  <div className="flex items-center space-x-3 mt-2">
                    <Slider
                      value={[customization.opacity]}
                      onValueChange={([value]) =>
                        updateCustomization({ opacity: value })
                      }
                      max={100}
                      min={10}
                      step={5}
                      className="flex-1"
                    />
                    <div className="bg-purple-600/20 border border-purple-600/40 rounded px-2 py-1 min-w-[50px] text-center">
                      <span className="text-purple-400 font-medium text-sm">
                        {customization.opacity}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Display Options Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Settings className="h-4 w-4 text-green-400" />
                  Display Options
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5">
                      <Label className="text-gray-300 text-sm font-medium">
                        Show Data Points
                      </Label>
                      <Switch
                        checked={customization.displaySettings.showDataPoints}
                        onCheckedChange={(checked) =>
                          updateDisplaySettings({ showDataPoints: checked })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5">
                      <Label className="text-gray-300 text-sm font-medium">
                        Smooth Lines
                      </Label>
                      <Switch
                        checked={customization.displaySettings.smoothLines}
                        onCheckedChange={(checked) =>
                          updateDisplaySettings({ smoothLines: checked })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5">
                      <Label className="text-gray-300 text-sm font-medium">
                        Fill Area
                      </Label>
                      <Switch
                        checked={customization.displaySettings.fillArea}
                        onCheckedChange={(checked) =>
                          updateDisplaySettings({ fillArea: checked })
                        }
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5">
                      <Label className="text-gray-300 text-sm font-medium">
                        Grid Lines
                      </Label>
                      <Switch
                        checked={customization.gridLines}
                        onCheckedChange={(checked) =>
                          updateCustomization({ gridLines: checked })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5">
                      <Label className="text-gray-300 text-sm font-medium">
                        Show Legend
                      </Label>
                      <Switch
                        checked={customization.legend}
                        onCheckedChange={(checked) =>
                          updateCustomization({ legend: checked })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between bg-white/5 p-4 rounded-2xl border border-white/5">
                      <Label className="text-gray-300 text-sm font-medium">
                        Animations
                      </Label>
                      <Switch
                        checked={customization.animations}
                        onCheckedChange={(checked) =>
                          updateCustomization({ animations: checked })
                        }
                      />
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Colors Tab */}
            <TabsContent value="colors" className="space-y-6">
              {/* Color Scheme Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Palette className="h-4 w-4 text-pink-400" />
                  Color Scheme
                </h4>
                <div>
                  <Label className="text-gray-300 text-sm font-medium">
                    Select Theme
                  </Label>
                  <Select
                    value={customization.colorScheme}
                    onValueChange={handleColorSchemeChange}
                  >
                    <SelectTrigger className="bg-gray-800/50 border-gray-600 text-white mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      <SelectItem
                        value="default"
                        className="text-white hover:bg-gray-600"
                      >
                        🎨 Default
                      </SelectItem>
                      <SelectItem
                        value="racing"
                        className="text-white hover:bg-gray-600"
                      >
                        🏎️ Racing
                      </SelectItem>
                      <SelectItem
                        value="classic"
                        className="text-white hover:bg-gray-600"
                      >
                        📊 Classic
                      </SelectItem>
                      <SelectItem
                        value="neon"
                        className="text-white hover:bg-gray-600"
                      >
                        💫 Neon
                      </SelectItem>
                      <SelectItem
                        value="custom"
                        className="text-white hover:bg-gray-600"
                      >
                        ✨ Custom
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Color Preview Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3">
                  Color Preview
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(customization.customColors).map(
                    ([key, color]) => (
                      <div
                        key={key}
                        className="text-center p-3 bg-gray-800/50 rounded border border-gray-600/30"
                      >
                        <div
                          className="w-8 h-8 rounded-full mx-auto mb-2 border-2 border-gray-600"
                          style={{ backgroundColor: color }}
                        />
                        <div className="text-xs font-medium text-white capitalize">
                          {key}
                        </div>
                        <div className="text-xs text-gray-400">{color}</div>
                      </div>
                    ),
                  )}
                </div>
              </div>

              {/* Custom Colors Section */}
              {customization.colorScheme === "custom" && (
                <div className="bg-white/5 rounded-[24px] p-6">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Settings className="h-4 w-4 text-purple-400" />
                    Custom Colors
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(customization.customColors).map(
                      ([key, color]) => (
                        <div
                          key={key}
                          className="bg-gray-800/50 p-3 rounded border border-gray-600/30"
                        >
                          <div className="flex items-center justify-between">
                            <Label className="text-gray-300 capitalize text-sm font-medium">
                              {key}
                            </Label>
                            <div className="flex items-center space-x-2">
                              <Input
                                type="color"
                                value={color}
                                onChange={(e) =>
                                  updateCustomColors({
                                    [key]: e.target.value,
                                  } as any)
                                }
                                className="w-10 h-8 bg-transparent border-white/20 rounded cursor-pointer"
                              />
                              <span className="text-xs text-gray-400 font-mono min-w-[60px]">
                                {color}
                              </span>
                            </div>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Axes Tab */}
            <TabsContent value="axes" className="space-y-6">
              {/* Axis Labels Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-orange-400" />
                  Axis Labels
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300 text-sm font-medium">
                      X-Axis Label
                    </Label>
                    <Input
                      value={customization.axisSettings.xAxisLabel}
                      onChange={(e) =>
                        updateAxisSettings({ xAxisLabel: e.target.value })
                      }
                      className="bg-gray-800/50 border-gray-600 text-white mt-2"
                      placeholder="e.g., Distance (m)"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300 text-sm font-medium">
                      Y-Axis Label
                    </Label>
                    <Input
                      value={customization.axisSettings.yAxisLabel}
                      onChange={(e) =>
                        updateAxisSettings({ yAxisLabel: e.target.value })
                      }
                      className="bg-gray-800/50 border-gray-600 text-white mt-2"
                      placeholder="e.g., Speed (km/h)"
                    />
                  </div>
                </div>
              </div>

              {/* Scaling Options Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Settings className="h-4 w-4 text-blue-400" />
                  Scaling Options
                </h4>
                <div className="flex items-center justify-between bg-gray-800/50 p-3 rounded border border-gray-600/30">
                  <div>
                    <Label className="text-gray-300 text-sm font-medium">
                      Auto Scale Axes
                    </Label>
                    <div className="text-xs text-gray-400 mt-1">
                      Automatically adjust axis ranges based on data
                    </div>
                  </div>
                  <Switch
                    checked={customization.axisSettings.autoScale}
                    onCheckedChange={(checked) =>
                      updateAxisSettings({ autoScale: checked })
                    }
                  />
                </div>
              </div>

              {/* Manual Range Section */}
              {!customization.axisSettings.autoScale && (
                <div className="bg-white/5 rounded-[24px] p-6">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Settings className="h-4 w-4 text-purple-400" />
                    Manual Axis Ranges
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-800/50 p-3 rounded border border-gray-600/30">
                      <Label className="text-gray-300 text-sm font-medium">
                        X-Axis Range
                      </Label>
                      <div className="flex space-x-2 mt-2">
                        <Input
                          type="number"
                          placeholder="Min"
                          value={customization.axisSettings.xAxisMin || ""}
                          onChange={(e) =>
                            updateAxisSettings({
                              xAxisMin: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                          className="bg-gray-700 border-gray-600 text-white text-sm"
                        />
                        <Input
                          type="number"
                          placeholder="Max"
                          value={customization.axisSettings.xAxisMax || ""}
                          onChange={(e) =>
                            updateAxisSettings({
                              xAxisMax: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                          className="bg-gray-700 border-gray-600 text-white text-sm"
                        />
                      </div>
                    </div>
                    <div className="bg-gray-800/50 p-3 rounded border border-gray-600/30">
                      <Label className="text-gray-300 text-sm font-medium">
                        Y-Axis Range
                      </Label>
                      <div className="flex space-x-2 mt-2">
                        <Input
                          type="number"
                          placeholder="Min"
                          value={customization.axisSettings.yAxisMin || ""}
                          onChange={(e) =>
                            updateAxisSettings({
                              yAxisMin: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                          className="bg-gray-700 border-gray-600 text-white text-sm"
                        />
                        <Input
                          type="number"
                          placeholder="Max"
                          value={customization.axisSettings.yAxisMax || ""}
                          onChange={(e) =>
                            updateAxisSettings({
                              yAxisMax: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                          className="bg-gray-700 border-gray-600 text-white text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Presets Tab */}
            <TabsContent value="presets" className="space-y-6">
              {/* Save Preset Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Save className="h-4 w-4 text-green-400" />
                  Save Current Settings
                </h4>
                <div className="flex space-x-2">
                  <Input
                    placeholder="Enter preset name..."
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    className="bg-gray-800/50 border-gray-600 text-white"
                  />
                  <Button
                    onClick={handleSavePreset}
                    className="bg-green-600 hover:bg-green-700 text-white px-4"
                    disabled={!presetName.trim()}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                </div>
              </div>

              {/* Load Preset Section */}
              {presetNames.length > 0 && (
                <div className="bg-white/5 rounded-[24px] p-6">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Download className="h-4 w-4 text-blue-400" />
                    Load Saved Preset
                  </h4>
                  <div>
                    <Label className="text-gray-300 text-sm font-medium">
                      Choose preset to load
                    </Label>
                    <Select
                      onValueChange={(presetName) => {
                        // In a real implementation, you'd load the preset data
                        // onLoadPreset(savedPresets[presetName]);
                      }}
                    >
                      <SelectTrigger className="bg-gray-800/50 border-gray-600 text-white mt-2">
                        <SelectValue placeholder="Select a preset..." />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-700 border-gray-600">
                        {presetNames.map((name) => (
                          <SelectItem
                            key={name}
                            value={name}
                            className="text-white hover:bg-gray-600"
                          >
                            📋 {name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {/* Reset Section */}
              <div className="bg-white/5 rounded-[24px] p-6">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <RotateCcw className="h-4 w-4 text-orange-400" />
                  Reset Options
                </h4>
                <div className="bg-white/10 border border-white/10 p-3 rounded-2xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-gray-300 text-sm font-medium">
                        Reset to Default Settings
                      </Label>
                      <div className="text-xs text-gray-400 mt-1">
                        Restore all customizations to original values
                      </div>
                    </div>
                    <Button
                      onClick={resetToDefaults}
                      variant="outline"
                      className="text-orange-400 border-orange-600/40 hover:bg-orange-600/10"
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Reset
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  );
};

export default GraphCustomizationPanel;
