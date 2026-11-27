import type { Preview } from "@storybook/react";
import "../src/styles/tokens.css";

const preview: Preview = {
  parameters: { backgrounds: { default: "carbon", values: [{ name: "carbon", value: "#0b0b0d" }] } },
};
export default preview;
