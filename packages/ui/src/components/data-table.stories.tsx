import type { Meta, StoryObj } from "@storybook/react";
import { DataTable } from "./data-table";

const meta: Meta<typeof DataTable> = { component: DataTable };
export default meta;

export const ConstructorStandings: StoryObj<typeof DataTable> = {
  render: () => (
    <DataTable>
      <thead>
        <tr><th>Pos</th><th>Team</th><th className="text-right">Points</th></tr>
      </thead>
      <tbody>
        <tr><td>1</td><td>McLaren</td><td className="tabular text-right">833</td></tr>
        <tr><td>2</td><td>Mercedes</td><td className="tabular text-right">469</td></tr>
        <tr><td>3</td><td>Red Bull</td><td className="tabular text-right">451</td></tr>
      </tbody>
    </DataTable>
  ),
};
