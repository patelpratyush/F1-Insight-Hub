import type { Meta, StoryObj } from "@storybook/react";
import { CommandPalette } from "./command-palette";

const meta: Meta<typeof CommandPalette> = { component: CommandPalette };
export default meta;

export const DriversAndRaces: StoryObj<typeof CommandPalette> = {
  args: {
    items: [
      { id: "nor", label: "Lando Norris", hint: "Driver" },
      { id: "ver", label: "Max Verstappen", hint: "Driver" },
      { id: "abu-2025", label: "Abu Dhabi Grand Prix 2025", hint: "Race" },
    ],
    onSelect: () => {},
  },
  render: (args) => (
    <div>
      <p className="text-sm text-carbon-200">Press Cmd+K (or Ctrl+K) to open.</p>
      <CommandPalette {...args} />
    </div>
  ),
};
