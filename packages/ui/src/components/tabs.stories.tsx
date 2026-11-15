import type { Meta, StoryObj } from "@storybook/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";

const meta: Meta<typeof Tabs> = { component: Tabs };
export default meta;

export const SessionTabs: StoryObj<typeof Tabs> = {
  render: () => (
    <Tabs defaultValue="race">
      <TabsList>
        <TabsTrigger value="qualifying">Qualifying</TabsTrigger>
        <TabsTrigger value="sprint">Sprint</TabsTrigger>
        <TabsTrigger value="race">Race</TabsTrigger>
      </TabsList>
      <TabsContent value="qualifying" className="p-4">Pole: NOR 1:22.207</TabsContent>
      <TabsContent value="sprint" className="p-4">Sprint winner: PIA</TabsContent>
      <TabsContent value="race" className="p-4">Race winner: VER</TabsContent>
    </Tabs>
  ),
};
