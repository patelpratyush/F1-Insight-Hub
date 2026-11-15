import type { Meta, StoryObj } from "@storybook/react";
import { Card } from "./card";

const meta: Meta<typeof Card> = { component: Card };
export default meta;

export const RaceSummary: StoryObj<typeof Card> = {
  render: () => (
    <Card>
      <h3 className="font-[var(--font-display)] text-2xl font-bold">Abu Dhabi Grand Prix</h3>
      <p className="text-sm text-carbon-200">Round 24 · Yas Marina Circuit · 58 laps</p>
    </Card>
  ),
};
