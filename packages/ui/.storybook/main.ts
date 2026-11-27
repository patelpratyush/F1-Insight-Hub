import type { StorybookConfig } from "@storybook/react-vite";
import tailwindcss from "@tailwindcss/vite";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y"],
  framework: "@storybook/react-vite",
  viteFinal: async (cfg) => ({ ...cfg, plugins: [...(cfg.plugins ?? []), tailwindcss()] }),
};
export default config;
