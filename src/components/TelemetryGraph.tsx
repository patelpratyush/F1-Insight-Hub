import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TelemetryData {
  lap: number;
  throttle: number;
  brake: number;
  speed: number;
  gear: number;
  drs: boolean;
}

interface TelemetryGraphProps {
  data: TelemetryData[];
  driver1: string;
  driver2?: string;
  data2?: TelemetryData[];
  title?: string;
}

export const TelemetryGraph = ({ 
  data, 
  driver1, 
  driver2, 
  data2, 
  title = "Telemetry Analysis" 
}: TelemetryGraphProps) => {
  // Combine data for comparison if second driver data is provided
  const chartData = data.map((item, index) => ({
    lap: item.lap,
    [`${driver1}_throttle`]: item.throttle,
    [`${driver1}_brake`]: item.brake,
    [`${driver1}_speed`]: item.speed,
    [`${driver1}_gear`]: item.gear,
    ...(data2 && data2[index] && {
      [`${driver2}_throttle`]: data2[index].throttle,
      [`${driver2}_brake`]: data2[index].brake,
      [`${driver2}_speed`]: data2[index].speed,
      [`${driver2}_gear`]: data2[index].gear,
    })
  }));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Speed Chart */}
            <div className="h-64">
              <h4 className="text-sm font-medium mb-2">Speed (km/h)</h4>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="lap" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey={`${driver1}_speed`} 
                    stroke="hsl(var(--primary))" 
                    name={`${driver1} Speed`}
                    strokeWidth={2}
                  />
                  {driver2 && (
                    <Line 
                      type="monotone" 
                      dataKey={`${driver2}_speed`} 
                      stroke="hsl(var(--destructive))" 
                      name={`${driver2} Speed`}
                      strokeWidth={2}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Throttle Chart */}
            <div className="h-64">
              <h4 className="text-sm font-medium mb-2">Throttle (%)</h4>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="lap" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey={`${driver1}_throttle`} 
                    stroke="hsl(var(--chart-1))" 
                    name={`${driver1} Throttle`}
                    strokeWidth={2}
                  />
                  {driver2 && (
                    <Line 
                      type="monotone" 
                      dataKey={`${driver2}_throttle`} 
                      stroke="hsl(var(--chart-2))" 
                      name={`${driver2} Throttle`}
                      strokeWidth={2}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Brake Chart */}
            <div className="h-64">
              <h4 className="text-sm font-medium mb-2">Brake Pressure (%)</h4>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="lap" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey={`${driver1}_brake`} 
                    stroke="hsl(var(--chart-3))" 
                    name={`${driver1} Brake`}
                    strokeWidth={2}
                  />
                  {driver2 && (
                    <Line 
                      type="monotone" 
                      dataKey={`${driver2}_brake`} 
                      stroke="hsl(var(--chart-4))" 
                      name={`${driver2} Brake`}
                      strokeWidth={2}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Gear Chart */}
            <div className="h-64">
              <h4 className="text-sm font-medium mb-2">Gear</h4>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="lap" />
                  <YAxis domain={[1, 8]} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="stepAfter" 
                    dataKey={`${driver1}_gear`} 
                    stroke="hsl(var(--chart-5))" 
                    name={`${driver1} Gear`}
                    strokeWidth={2}
                  />
                  {driver2 && (
                    <Line 
                      type="stepAfter" 
                      dataKey={`${driver2}_gear`} 
                      stroke="hsl(var(--secondary))" 
                      name={`${driver2} Gear`}
                      strokeWidth={2}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export type { TelemetryData };