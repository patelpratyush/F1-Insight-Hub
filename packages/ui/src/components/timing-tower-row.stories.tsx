import type { Meta, StoryObj } from "@storybook/react";
import { TimingTowerRow } from "./timing-tower-row";

const meta: Meta<typeof TimingTowerRow> = { component: TimingTowerRow };
export default meta;

export const Leader: StoryObj<typeof TimingTowerRow> = {
  args: { position: 1, code: "NOR", name: "Lando Norris", value: "423.5", teamColor: "#FF8000", sector: "purple" },
};
export const Chaser: StoryObj<typeof TimingTowerRow> = {
  args: { position: 2, code: "VER", name: "Max Verstappen", value: "421", delta: "-2.5", teamColor: "#3671C6", sector: "green" },
};
