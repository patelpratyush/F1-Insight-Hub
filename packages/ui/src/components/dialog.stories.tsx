import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "./dialog";

const meta: Meta<typeof Dialog> = { component: Dialog };
export default meta;

export const DriverDetails: StoryObj<typeof Dialog> = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Lando Norris</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle className="font-[var(--font-display)] text-2xl font-bold">Lando Norris</DialogTitle>
        <DialogDescription className="text-carbon-200">McLaren · #4 · 423.5 points · 7 wins</DialogDescription>
      </DialogContent>
    </Dialog>
  ),
};
