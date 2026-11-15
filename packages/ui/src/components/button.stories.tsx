import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";

const meta: Meta<typeof Button> = { component: Button, args: { children: "Button" } };
export default meta;
export const Primary: StoryObj<typeof Button> = {};
export const Secondary: StoryObj<typeof Button> = { args: { variant: "secondary" } };
export const Ghost: StoryObj<typeof Button> = { args: { variant: "ghost" } };
